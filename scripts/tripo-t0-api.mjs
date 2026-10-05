import fs from "node:fs/promises";
import path from "node:path";

const BASE = "https://openapi.tripo3d.ai/v3";
const apiKey = process.env.TRIPO_API_KEY;
const mode = (process.env.TRIPO_T0_MODE || "check").toLowerCase();
const inputPath = process.env.TRIPO_INPUT || "public/models/evowild-s/source-lod2.glb";
const outDir = "artifacts/tripo-t0-api";
const reviewDir = "art/motion/tripo-s/review";
const riggedPath = "public/experiments/tripo-s/t0-rigged-lod2.glb";
const sessionPath = path.join(reviewDir, "t0-api-session.json");

if (!apiKey) throw new Error("TRIPO_API_KEY is required");
if (!["check", "rig"].includes(mode)) throw new Error("TRIPO_T0_MODE must be check or rig");

await fs.mkdir(outDir, { recursive: true });
await fs.mkdir(reviewDir, { recursive: true });
await fs.mkdir(path.dirname(riggedPath), { recursive: true });

const startedAt = new Date().toISOString();

async function requestJson(url, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${apiKey}`);
  const res = await fetch(url, { ...options, headers });
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Non-JSON response ${res.status}: ${text.slice(0, 500)}`);
  }
  if (!res.ok || data.code !== 0) {
    throw new Error(`Tripo API error ${res.status}: ${JSON.stringify(data)}`);
  }
  return data.data;
}

async function getBalance() {
  const data = await requestJson(`${BASE}/account/balance`);
  return data;
}

async function uploadModel(filePath) {
  const bytes = await fs.readFile(filePath);
  const form = new FormData();
  form.append("file", new Blob([bytes], { type: "model/gltf-binary" }), path.basename(filePath));
  return requestJson(`${BASE}/files`, { method: "POST", body: form });
}

async function createTask(endpoint, payload) {
  return requestJson(`${BASE}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

async function pollTask(taskId, timeoutMs = 10 * 60 * 1000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const task = await requestJson(`${BASE}/tasks/${taskId}`);
    if (task.status === "success") return task;
    if (["failed", "cancelled"].includes(task.status)) {
      throw new Error(`Task ${taskId} ended with status ${task.status}: ${JSON.stringify(task)}`);
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  throw new Error(`Task ${taskId} timed out after ${timeoutMs}ms`);
}

async function download(url, outputPath) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed ${res.status}: ${url}`);
  const bytes = new Uint8Array(await res.arrayBuffer());
  await fs.writeFile(outputPath, bytes);
  return bytes.length;
}

const session = {
  schema_version: 1,
  gate: "T0",
  path: "API_FALLBACK",
  mode,
  started_at_utc: startedAt,
  completed_at_utc: null,
  input: inputPath,
  rig_model: "v2.5-20260210",
  requested_rig_type: "quadruped",
  spec: "tripo",
  out_format: "glb",
  balance_before: null,
  balance_after: null,
  file_token_created: false,
  rig_check: null,
  rig: null,
  output_path: mode === "rig" ? riggedPath : null,
  status: "RUNNING",
  notes: [
    "This path bypasses the Tripo Studio WebGL renderer and uses the documented v3 API.",
    "No API key or credential is written to this record."
  ]
};

try {
  session.balance_before = await getBalance();

  const uploaded = await uploadModel(inputPath);
  if (!uploaded.file_token) throw new Error("Upload succeeded but file_token was missing");
  session.file_token_created = true;

  const checkCreated = await createTask("/animations/rig-check", { input: uploaded.file_token });
  const checkTask = await pollTask(checkCreated.task_id);
  session.rig_check = {
    task_id: checkCreated.task_id,
    status: checkTask.status,
    riggable: checkTask.output?.riggable ?? null,
    recommended_rig_type: checkTask.output?.rig_type ?? null,
    credits_consumed: checkTask.credits_consumed ?? null
  };

  if (checkTask.output?.riggable !== true) {
    session.status = "REJECT_RIG_CHECK";
    throw new Error("Rig check reported riggable=false");
  }

  if (mode === "check") {
    session.status = "RIG_CHECK_PASS";
  } else {
    if (checkTask.output?.rig_type !== "quadruped") {
      session.status = "STOP_RIG_TYPE_MISMATCH";
      throw new Error(`Rig check recommended ${checkTask.output?.rig_type}, expected quadruped. Rig was not submitted.`);
    }

    const rigCreated = await createTask("/animations/rig", {
      input: uploaded.file_token,
      model: "v2.5-20260210",
      rig_type: "quadruped",
      spec: "tripo",
      out_format: "glb"
    });
    const rigTask = await pollTask(rigCreated.task_id);
    const modelUrl = rigTask.output?.model_url;
    if (!modelUrl) throw new Error("Rig task succeeded but output.model_url was missing");

    const bytes = await download(modelUrl, riggedPath);
    session.rig = {
      task_id: rigCreated.task_id,
      status: rigTask.status,
      credits_consumed: rigTask.credits_consumed ?? null,
      downloaded_bytes: bytes
    };
    session.status = "RIG_EXPORT_READY";
  }

  session.balance_after = await getBalance();
  session.completed_at_utc = new Date().toISOString();
  await fs.writeFile(sessionPath, JSON.stringify(session, null, 2) + "\n");
  await fs.writeFile(path.join(outDir, "t0-api-session.json"), JSON.stringify(session, null, 2) + "\n");
  console.log(JSON.stringify(session, null, 2));
} catch (error) {
  try {
    session.balance_after = await getBalance();
  } catch {}
  session.completed_at_utc = new Date().toISOString();
  if (session.status === "RUNNING") session.status = "ERROR";
  session.error = String(error?.message || error);
  await fs.writeFile(sessionPath, JSON.stringify(session, null, 2) + "\n");
  await fs.writeFile(path.join(outDir, "t0-api-session.json"), JSON.stringify(session, null, 2) + "\n");
  console.error(JSON.stringify(session, null, 2));
  process.exitCode = 1;
}
