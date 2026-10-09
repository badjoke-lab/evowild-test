import fs from "node:fs";
import path from "node:path";

const [beforeDir = "artifacts/gamestudio-2p5d/before", afterDir = "artifacts/gamestudio-2p5d/after", outputDir = "artifacts/gamestudio-2p5d/summary"] = process.argv.slice(2);
fs.mkdirSync(outputDir, { recursive: true });
const read = file => JSON.parse(fs.readFileSync(file, "utf8"));

function outcomes(dir) {
  const report = read(path.join(dir, "tests.json"));
  const tests = [];
  const visit = suite => {
    for (const spec of suite.specs || []) {
      for (const test of spec.tests) {
        const result = test.results.at(-1);
        tests.push({ title: spec.title, project: test.projectName, status: result.status, duration: result.duration, errors: result.errors?.map(error => error.message) || [] });
      }
    }
    for (const child of suite.suites || []) visit(child);
  };
  for (const suite of report.suites) visit(suite);
  return { stats: report.stats, tests };
}

const result = { before: outcomes(beforeDir), after: outcomes(afterDir), projects: {}, limitations: [
  "Android evidence is Chromium device emulation, not a physical Android device.",
  "Controlled 4600ms browser-clock advancement can differ by one fixed simulation step during initial RAF scheduling; use captured telemetry, not pixel equality, to compare scenes.",
  "Unique frames and preserved source hashes do not establish smooth gait or canonical art approval. No new creature asset is promoted."
] };
for (const project of ["android-chromium", "desktop-chromium"]) {
  const before = read(path.join(beforeDir, project, "sprite-audit.json"));
  const after = read(path.join(afterDir, project, "sprite-audit.json"));
  const changedSources = Object.keys(before.sourceHashes).filter(file => before.sourceHashes[file] !== after.sourceHashes[file]);
  if (changedSources.length) throw new Error(`Protected art changed: ${changedSources.join(", ")}`);
  const beforeUI = read(path.join(beforeDir, project, "ui-audit.json"));
  const afterUI = read(path.join(afterDir, project, "ui-audit.json"));
  result.projects[project] = {
    viewport: afterUI.viewport,
    protectedSourcesUnchanged: true,
    sourceHashes: after.sourceHashes,
    controlSizes: afterUI.controls.map(control => ({ id: control.id, before: beforeUI.controls.find(item => item.id === control.id), after: control })),
    scenes: Object.fromEntries(["race-4600ms", "dense-pack-4600ms"].map(name => [name, {
      before: read(path.join(beforeDir, project, `${name}.json`)).state,
      after: read(path.join(afterDir, project, `${name}.json`)).state
    }]))
  };
}
fs.writeFileSync(path.join(outputDir, "summary.json"), JSON.stringify(result, null, 2));
console.log(JSON.stringify({ before: result.before.stats, after: result.after.stats, protectedSourcesUnchanged: true }, null, 2));
