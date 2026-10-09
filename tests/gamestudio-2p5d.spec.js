import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const root = path.resolve(process.env.GAMESTUDIO_EVIDENCE_DIR || "artifacts/gamestudio-2p5d/latest");
const phases = ["CONTACT", "PUSH", "LIFT", "FLIGHT", "REACH", "LAND"];
const morphs = ["S", "P", "E", "A"];
const fixedTime = new Date("2026-10-10T00:00:00Z");

function evidence(testInfo, name) {
  const dir = path.join(root, testInfo.project.name);
  fs.mkdirSync(dir, { recursive: true });
  return path.join(dir, name);
}

async function frozenScene(page, query = "") {
  // Advance every animation frame, rather than jumping the capped fixed-step loop.
  await page.clock.install({ time: fixedTime });
  await page.clock.pauseAt(fixedTime);
  await page.goto(`/evowild-test/race-quality.html${query}`, { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-run-sheets", "ready");
  await page.clock.runFor(4600);
}

async function snapshot(page) {
  return page.locator("#stage").evaluate(node => ({
    state: { ...node.dataset },
    viewport: { width: innerWidth, height: innerHeight, dpr: devicePixelRatio },
    controls: [...document.querySelectorAll("button, select")].map(el => {
      const r = el.getBoundingClientRect();
      return { id: el.id || el.dataset.agentCommand, text: el.textContent.trim(), x: r.x, y: r.y, width: r.width, height: r.height };
    })
  }));
}

test("Game Studio controlled-clock 18-runner and dense-pack evidence", async ({ page }, testInfo) => {
  test.setTimeout(60000);
  await frozenScene(page);
  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-field-size", "18");
  await expect(stage).toHaveAttribute("data-morph-set", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-race-state", "running");
  await expect(page.locator("#agentTargetSelect option")).toHaveCount(18);
  await expect(page.locator("#ranking span")).toHaveCount(18);
  await page.screenshot({ path: evidence(testInfo, "race-4600ms.png") });
  fs.writeFileSync(evidence(testInfo, "race-4600ms.json"), JSON.stringify(await snapshot(page), null, 2));

  await page.goto("/evowild-test/race-quality.html?battleReview=1", { waitUntil: "networkidle" });
  await expect(stage).toHaveAttribute("data-run-sheets", "ready");
  await page.clock.runFor(4600);
  await expect(stage).toHaveAttribute("data-label-overlap-count", "0");
  await expect(stage).toHaveAttribute("data-battle-visible", "1");
  await page.screenshot({ path: evidence(testInfo, "dense-pack-4600ms.png") });
  fs.writeFileSync(evidence(testInfo, "dense-pack-4600ms.json"), JSON.stringify(await snapshot(page), null, 2));
});

test("Game Studio shipped sprite sheets retain transparency and all six distinct slots", async ({ page }, testInfo) => {
  test.setTimeout(60000);
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-run-sheets", "ready");
  const audit = await page.evaluate(async ({ morphs, phases }) => {
    const result = [];
    for (const morph of morphs) {
      const image = new Image();
      image.src = `/evowild-test/concept/${morph.toLowerCase()}-run-sheet.webp`;
      await image.decode();
      const cols = morph === "A" ? 2 : 3;
      const rows = morph === "A" ? 3 : 2;
      const width = Math.floor(image.naturalWidth / cols);
      const height = Math.floor(image.naturalHeight / rows);
      const frame = document.createElement("canvas");
      frame.width = width; frame.height = height;
      const ctx = frame.getContext("2d", { willReadFrequently: true });
      const frames = [];
      const preview = document.createElement("canvas");
      preview.width = 6 * 240; preview.height = 250;
      const pc = preview.getContext("2d");
      pc.fillStyle = "#071018"; pc.fillRect(0, 0, preview.width, preview.height);
      // One scale and bottom-center slot anchor for the complete shipped strip.
      const scale = Math.min(220 / width, 195 / height);
      for (let index = 0; index < 6; index++) {
        ctx.clearRect(0, 0, width, height);
        ctx.drawImage(image, index % cols * width, Math.floor(index / cols) * height, width, height, 0, 0, width, height);
        const data = ctx.getImageData(0, 0, width, height).data;
        let opaque = 0, transparent = 0;
        let left = width, right = -1, top = height, bottom = -1;
        for (let pixel = 0; pixel < width * height; pixel++) {
          if (data[pixel * 4 + 3] === 0) transparent++;
          if (data[pixel * 4 + 3] > 12) {
            opaque++;
            const x = pixel % width, y = Math.floor(pixel / width);
            left = Math.min(left, x); right = Math.max(right, x);
            top = Math.min(top, y); bottom = Math.max(bottom, y);
          }
        }
        const hash = [...new Uint8Array(await crypto.subtle.digest("SHA-256", data))].map(x => x.toString(16).padStart(2, "0")).join("");
        frames.push({ phase: phases[index], opaque, transparent, bbox: { left, right, top, bottom }, hash });
        pc.drawImage(frame, index * 240 + (240 - width * scale) / 2, 215 - height * scale, width * scale, height * scale);
        pc.strokeStyle = "#b9f1ff"; pc.beginPath(); pc.moveTo(index * 240 + 10, 215); pc.lineTo(index * 240 + 230, 215); pc.stroke();
        pc.fillStyle = "#eff9ff"; pc.font = "14px monospace";
        pc.fillText(`${morph} ${index + 1} ${phases[index]}`, index * 240 + 10, 240);
      }
      result.push({ morph, source: image.src, width: image.naturalWidth, height: image.naturalHeight, layout: `${cols}x${rows}`, slot: { width, height }, frames, preview: preview.toDataURL("image/png") });
    }
    return result;
  }, { morphs, phases });
  for (const item of audit) {
    expect(new Set(item.frames.map(frame => frame.hash)).size).toBe(6);
    for (const frame of item.frames) {
      expect(frame.opaque).toBeGreaterThan(100);
      expect(frame.transparent).toBeGreaterThan(100);
    }
    fs.writeFileSync(evidence(testInfo, `sheet-${item.morph}.png`), Buffer.from(item.preview.split(",")[1], "base64"));
    delete item.preview;
  }
  const files = ["docs/references/evowild-creature-reference-sheet-20260921.jpg", "docs/creature-reference-index-v0.1.md", "docs/2p5d-creature-reference-lock.md", ...morphs.flatMap(morph => [`public/concept/${morph}.webp`, `public/concept/${morph.toLowerCase()}-run-sheet.webp`])];
  const hashes = Object.fromEntries(files.map(file => [file, crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex")]));
  fs.writeFileSync(evidence(testInfo, "sprite-audit.json"), JSON.stringify({ sheets: audit, sourceHashes: hashes, note: "Raw shipped slots, one common scale; no art or runtime anchor changes. Bounding boxes include source artifacts. Identity and gait require visual review." }, null, 2));
});

test("Game Studio all four morphs show all six live phases and pinned runtime frames", async ({ page }, testInfo) => {
  test.setTimeout(120000);
  for (const [index, morph] of morphs.entries()) {
    await page.goto(`/evowild-test/race-quality.html?motionReview=1&selected=${index + 1}`, { waitUntil: "networkidle" });
    const stage = page.locator("#stage");
    await expect(stage).toHaveAttribute("data-run-sheets", "ready");
    await expect(stage).toHaveAttribute("data-race-state", "running");
    const observed = new Set();
    for (let sample = 0; sample < 90 && observed.size < 6; sample++) {
      observed.add(await stage.getAttribute("data-selected-run-phase"));
      await page.waitForTimeout(25);
    }
    expect([...observed].sort()).toEqual([...phases].sort());
    const metrics = [];
    for (let frame = 0; frame < 6; frame++) {
      await page.goto(`/evowild-test/race-quality.html?motionReview=1&selected=${index + 1}&motionFrame=${frame}`, { waitUntil: "networkidle" });
      await expect(stage).toHaveAttribute("data-run-sheets", "ready");
      await expect(stage).toHaveAttribute("data-selected-run-frame", String(frame));
      await expect(stage).toHaveAttribute("data-selected-morph", morph);
      await expect(stage).toHaveAttribute("data-selected-run-phase", phases[frame]);
      await expect(stage).toHaveAttribute("data-camera-subject", "motion-review-isolated");
      await page.screenshot({ path: evidence(testInfo, `motion-${morph}-${frame}-${phases[frame]}.png`) });
      metrics.push(await snapshot(page));
    }
    fs.writeFileSync(evidence(testInfo, `motion-${morph}.json`), JSON.stringify({ observed: [...observed], frames: metrics }, null, 2));
  }
});

test("Game Studio controls remain reachable and preserve race through pause, target command and reset", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-race-state", "running");
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  const clock = await page.locator("#clock").textContent();
  await page.waitForTimeout(300);
  await expect(page.locator("#clock")).toHaveText(clock);
  await page.screenshot({ path: evidence(testInfo, "paused.png") });
  await page.getByRole("button", { name: "Resume", exact: true }).click();
  await expect(page.locator("#clock")).not.toHaveText(clock);
  await page.locator("#agentTargetSelect").selectOption("1");
  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await expect(stage).toHaveAttribute("data-agent-target-morph", "P");
  await expect(stage).toHaveAttribute("data-agent-focus-command", "PUSH");
  await expect(stage).toHaveAttribute("data-selected-morph", "S");
  await expect(page.locator("#agentFeedback")).toBeVisible();
  await page.screenshot({ path: evidence(testInfo, "agent-P-push.png") });
  await page.getByRole("button", { name: "CLEAR", exact: true }).click();
  await expect(stage).toHaveAttribute("data-agent-focus-command", "NEUTRAL");
  await page.getByRole("button", { name: "Reset", exact: true }).click();
  await expect(stage).toHaveAttribute("data-race-state", "countdown");
  await expect(stage).toHaveAttribute("data-agent-target-runner", "1");
  await expect(page.locator("#ranking span")).toHaveCount(18);
  await page.screenshot({ path: evidence(testInfo, "reset-countdown.png") });
});

test("Game Studio touch targets and keyboard focus are clear", async ({ page }, testInfo) => {
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state", "running");
  const data = await snapshot(page);
  fs.writeFileSync(evidence(testInfo, "ui-audit.json"), JSON.stringify(data, null, 2));
  for (const control of data.controls) {
    expect(control.width, control.id).toBeGreaterThanOrEqual(44);
    expect(control.height, control.id).toBeGreaterThanOrEqual(44);
    expect(control.x, control.id).toBeGreaterThanOrEqual(0);
    expect(control.y + control.height, control.id).toBeLessThanOrEqual(data.viewport.height);
  }
  await page.keyboard.press("Tab");
  await expect(page.locator("#agentTargetSelect")).toBeFocused();
  await page.screenshot({ path: evidence(testInfo, "keyboard-focus.png") });
  const focus = await page.locator("#agentTargetSelect").evaluate(el => ({ style: getComputedStyle(el).outlineStyle, width: parseFloat(getComputedStyle(el).outlineWidth) }));
  expect(focus.style).toBe("solid");
  expect(focus.width).toBeGreaterThanOrEqual(2);
  await expect(page.locator("#agentTargetSelect option:checked")).toContainText("S01");
  await expect(page.locator("#agentTargetSelect option:checked")).toContainText("YOU");
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await expect(page.locator("#pause")).toHaveAttribute("aria-pressed", "true");
});

test("Game Studio reduced motion removes only nonessential feedback animation", async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-race-state", "running");
  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await expect(page.locator("#agentFeedback")).toBeVisible();
  await page.screenshot({ path: evidence(testInfo, "reduced-motion-feedback.png") });
  expect(await page.locator(".agent-feedback-orb").evaluate(el => getComputedStyle(el).animationName)).toBe("none");
  const distance = await stage.getAttribute("data-selected-distance");
  await expect(stage).not.toHaveAttribute("data-selected-distance", distance);
});
