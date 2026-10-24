import {test,expect} from "@playwright/test";
import fs from "node:fs";
import {loadAgentProfile,saveAgentProfile,matchedAgentPreset} from "../src/race_agent_profile_store.js";
import {makeAgentFile} from "../src/race_agent_v1.js";
import {
  ENTRANTS,GAME_STORAGE_KEY,RACE_COURSE_ID,defaultGameState,
  validateGameState,makeRaceRecord,validateRaceRecord,loadGameState,
  storeGameState,appendRaceResult,selectPlayerRunner,formatRaceTime
} from "../src/game_progress_2p5d.js";
function fakeStorage(initial={}){
  const m=new Map(Object.entries(initial));
  return {getItem:key=>m.get(key)||null,setItem:(key,value)=>m.set(key,value)};
}
function testRecord(id="test-only-00000001",playerRunnerId=4){
  const results=ENTRANTS.map((r,i)=>({
    ...r,finishPlace:i+1,finishTime:43500+i*700
  }));
  return makeRaceRecord({id,selectedRunnerId:playerRunnerId,finishedAt:1761300000000,results});
}
test("race archive accepts only complete 18-entrant classifications with unique ranks",()=>{
  expect(ENTRANTS).toHaveLength(18);
  const record=testRecord();
  expect(validateRaceRecord(record)).toBe(true);
  expect(record.playerPlace).toBe(4);
  expect(makeRaceRecord({...record,results:record.results.slice(0,17)})).toBeNull();
  const cheated={...record,results:record.results.map(x=>({...x}))};
  cheated.results[1].place=1;
  expect(validateRaceRecord(cheated)).toBe(false);
  expect(formatRaceTime(63530)).toBe("01:03.53");
});
test("history persists only valid records, dedupes and does not create sample wins",()=>{
  const storage=fakeStorage();
  expect(loadGameState(storage)).toEqual(defaultGameState());
  expect(selectPlayerRunner(storage,4)).toBe(true);
  expect(loadGameState(storage).selectedRunnerId).toBe(4);
  const record=testRecord();
  expect(appendRaceResult(storage,record)).toBe(true);
  expect(appendRaceResult(storage,record)).toBe(true);
  const state=loadGameState(storage);
  expect(state.history).toHaveLength(1);
  expect(state.history[0].playerPlace).toBe(4);
  storage.setItem(GAME_STORAGE_KEY,"invalid");
  expect(loadGameState(storage).history).toHaveLength(0);
  expect(storeGameState(storage,{schemaVersion:1,selectedRunnerId:99,history:[]})).toBe(false);
});
test("game menus select only the implemented oval and navigate to the real race",async ({page})=>{
  await page.goto("/evowild-test/game-2p5d.html",{waitUntil:"networkidle"});
  await expect(page.getByRole("heading",{name:"一匹から、種を作れ。"})).toBeVisible();
  await expect(page.locator("#homeHistoryCount")).toHaveText("記録 0 レース");
  await page.locator('[data-nav="course"]').click();
  await expect(page.getByRole("heading",{name:"オーバル 1600"})).toBeVisible();
  await expect(page.locator(".course-card")).toHaveCount(1);
  await page.locator('[data-nav="creatures"]').click();
  await expect(page.locator(".creature-card")).toHaveCount(18);
  await page.locator('[data-runner-id="4"]').click();
  await page.locator("#saveCreature").click();
  await expect(page.locator("#saveNotice")).toContainText("保存しました");
  const href=await page.locator("#playFromCreatures").getAttribute("href");
  expect(href).toContain("selected=4");
  await page.locator("#playFromCreatures").click();
  await expect(page.locator("#entryRunnerSelect")).toHaveValue("4");
  await expect(page.locator("[data-agent-field]")).toHaveCount(7);
  await expect(page.locator("#preRacePanel")).toBeVisible();
  await page.getByRole("link",{name:"ホームへ"}).click();
  await expect(page.getByRole("heading",{name:"一匹から、種を作れ。"})).toBeVisible();
  await expect(page.locator("#heroCreatureName")).toContainText("Serein");
});
test("review-only finish never pollutes the local real race history",async ({page})=>{
  await page.goto("/evowild-test/race-stadium.html?finishReview=1&selected=4",{waitUntil:"networkidle"});
  await page.locator("#startAutonomous").click();
  await expect(page.locator("#stage")).toHaveAttribute("data-race-state","finished",{timeout:14000});
  await expect(page.locator("#stage")).toHaveAttribute("data-record-saved","review-excluded");
  await expect(page.locator("#resultList li")).toHaveCount(18);
  await expect(page.locator("#resultList li").first()).toHaveAttribute("data-runner-id",/\d+/);
  await page.locator("#goToHistory").click();
  await expect(page.locator("#historyEmpty")).toBeVisible();
});

test("capture genuine home, course and selected Creature UI on desktop and Android",async ({page},testInfo)=>{
  await page.goto("/evowild-test/game-2p5d.html",{waitUntil:"networkidle"});
  fs.mkdirSync("test-results/visuals",{recursive:true});
  const capture=async name=>page.screenshot({
    path:"test-results/visuals/game-"+name+"-"+testInfo.project.name+".png",
    fullPage:true
  });
  await expect(page.locator("#heroCreatureArt")).toHaveJSProperty("complete",true);
  await capture("home");
  await page.locator('[data-nav="course"]').click();
  await capture("course");
  await page.locator('[data-nav="creatures"]').click();
  await page.locator('[data-runner-id="4"]').click();
  await capture("creatures");
  await page.locator('[data-nav="history"]').click();
  await capture("empty-history");
});

test("selected entrant keeps a validated Agent profile rather than losing it after race",async ({page})=>{
  await page.goto("/evowild-test/race-stadium.html?selected=4",{waitUntil:"networkidle"});
  const file=makeAgentFile("CLOSER");
  await page.locator("#importAgent").setInputFiles({
    name:"agent-file.json",mimeType:"application/json",
    buffer:Buffer.from(JSON.stringify(file))
  });
  await expect(page.locator("#setupValidation")).toContainText("読み込みました");
  await expect(page.locator('[name="basePace"]')).toHaveValue("CONSERVE");
  await page.locator("#startAutonomous").click();
  await expect(page.locator("#stage")).toHaveAttribute("data-agent-profile-saved","1");
  await page.goto("/evowild-test/race-stadium.html?selected=4",{waitUntil:"networkidle"});
  await expect(page.locator('[name="basePace"]')).toHaveValue("CONSERVE");
  await expect(page.locator("#presetSelect")).toHaveValue("CLOSER");
  await expect(page.locator("#entryRunnerSelect")).toHaveValue("4");
});
test("Agent per entrant profile storage validates JSON and does not spill between entrants",()=>{
  const storage=fakeStorage();
  const closer=makeAgentFile("CLOSER");
  expect(saveAgentProfile(storage,4,closer)).toBe(true);
  expect(loadAgentProfile(storage,4)).toEqual(closer);
  expect(loadAgentProfile(storage,5)).toEqual(makeAgentFile());
  expect(matchedAgentPreset(closer)).toBe("CLOSER");
  expect(saveAgentProfile(storage,4,{...closer,unsafeScript:"alert(1)"})).toBe(false);
});
