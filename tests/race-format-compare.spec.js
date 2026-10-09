import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

// Optional evidence run; excluded from routine tests and deploys.
// RACE_FORMAT_COMPARE=1 npx playwright test tests/race-format-compare.spec.js --workers=1
const candidates = [
  {
    id: "2p5d",
    url: "/evowild-test/race-quality.html?selected=1",
    canvas: "#raceCanvas",
    async ready(page) {
      const stage = page.locator("#stage");
      await expect(stage).toHaveAttribute("data-field-size", "18", {timeout:15000});
      await expect(stage).toHaveAttribute("data-morph-set", "S,P,E,A", {timeout:15000});
      await expect(stage).toHaveAttribute("data-run-sheets", "ready", {timeout:30000});
      await expect(stage).toHaveAttribute("data-race-state", "running", {timeout:15000});
    },
    async state(page) {
      return page.locator("#stage").evaluate(el => ({
        fieldSize:el.dataset.fieldSize, morphSet:el.dataset.morphSet,
        raceState:el.dataset.raceState, runSheetsReady:el.dataset.runSheetsReady,
        visibleRacers:el.dataset.visibleRacers, selectedPhase:el.dataset.selectedRunPhase,
        selectedFrame:el.dataset.selectedRunFrame
      }));
    }
  },
  {
    id: "3d",
    url: "/evowild-test/preview-motion-first-race/",
    canvas: "#scene",
    async ready(page) {
      const scene = page.locator("#scene");
      await expect(scene).toBeVisible({timeout:20000});
      await expect(scene).toHaveAttribute("data-runner-count", "18", {timeout:45000});
      await expect(scene).toHaveAttribute("data-morph-set", /S.*P.*E.*A/, {timeout:15000});
      await expect(page.locator("#fpsReadout")).toContainText("FPS", {timeout:15000});
    },
    async state(page) {
      return page.locator("#scene").evaluate(el => ({
        runnerCount:el.dataset.runnerCount, morphSet:el.dataset.morphSet,
        raceTime:el.dataset.raceTime, simulationHz:el.dataset.simulationHz,
        renderCalls:el.dataset.renderCalls, renderTriangles:el.dataset.renderTriangles,
        renderPixelRatio:el.dataset.renderPixelRatio,
        raceProxyInstanceCount:el.dataset.raceProxyInstanceCount,
        fpsReadout:document.querySelector("#fpsReadout")?.textContent ?? null
      }));
    }
  }
];

async function observeRaf(page) {
  // Browser RAF scheduling is not a GPU profiler or gameplay/simulation FPS.
  return page.evaluate(() => new Promise(resolve => {
    const intervals=[]; let previous=null; let done=false;
    function finish() {
      if(done) return;
      done=true;
      const sorted=intervals.filter(n=>Number.isFinite(n) && n>0).sort((a,b)=>a-b);
      const pct=p=>sorted.length ? sorted[Math.floor((sorted.length-1)*p)] : null;
      const mean=sorted.length ? sorted.reduce((a,b)=>a+b,0)/sorted.length : null;
      resolve({samples:sorted.length, meanMs:mean, medianMs:pct(0.5),
        p95Ms:pct(0.95), observedHz:mean ? 1000/mean : null});
    }
    function tick(t) {
      if(done) return;
      if(previous !== null) intervals.push(t-previous);
      previous=t;
      if(intervals.length >= 120) finish();
      else requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick); setTimeout(finish,12000);
  }));
}

test("2.5D versus 3D evidence without an assumed winner", async ({page}, testInfo) => {
  test.skip(process.env.RACE_FORMAT_COMPARE !== "1", "Opt-in to avoid routine CI costs");
  test.setTimeout(180000);
  const dir=path.join("test-results","format-comparison",testInfo.project.name);
  fs.mkdirSync(dir,{recursive:true});
  const data={
    protocol:"format-comparison-v1", platform:testInfo.project.name,
    generatedUtc:new Date().toISOString(),
    limitation:"Different simulation and cameras; no claim of identical physics or fair game-balance comparison.",
    timingCaveat:"RAF scheduling is not GPU time; CI/headless WebGL is not real mobile GPU performance.",
    pluginCaveat:"Game Studio was not installed or used; this compares existing implementations.",
    runs:[]
  };
  for(const candidate of candidates) {
    const errors=[];
    const handler=e=>errors.push(e.message || String(e));
    page.on("pageerror",handler);
    const run={format:candidate.id,url:candidate.url,ready:false,pageErrors:errors};
    try {
      await page.goto(candidate.url,{waitUntil:"domcontentloaded",timeout:30000});
      await candidate.ready(page);
      run.ready=true;
      await page.waitForTimeout(2500);
      run.rafTiming=await observeRaf(page);
      run.state=await candidate.state(page);
      run.viewport=await page.evaluate(()=>({
        width:innerWidth,height:innerHeight,devicePixelRatio:devicePixelRatio
      }));
      const full=path.join(dir,candidate.id+"-full.png");
      await page.screenshot({path:full,fullPage:true,animations:"disabled"});
      run.fullScreenshot=full;
      await testInfo.attach(candidate.id+"-screen",{path:full,contentType:"image/png"});
      const stage=path.join(dir,candidate.id+"-stage.png");
      await page.locator(candidate.canvas).screenshot({path:stage,animations:"disabled"});
      run.stageScreenshot=stage;
      await testInfo.attach(candidate.id+"-stage",{path:stage,contentType:"image/png"});
    } catch(e) {
      run.error=String(e?.message ?? e).slice(0,1500);
      // Continue to the other format, preserving evidence of both outcomes.
    } finally {
      page.off("pageerror",handler);
      data.runs.push(run);
    }
  }
  const report=path.join(dir,"results.json");
  fs.writeFileSync(report,JSON.stringify(data,null,2)+"\n");
  await testInfo.attach("format-comparison-json",{path:report,contentType:"application/json"});
  expect(data.runs.every(r=>r.ready && !r.error && !r.pageErrors.length),
    JSON.stringify(data.runs,null,2)).toBe(true);
});
