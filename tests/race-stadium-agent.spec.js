import { test, expect } from "@playwright/test";
import fs from "node:fs";
import {
  AGENT_FIELDS, AGENT_PRESETS, makeAgentFile, validateAgentFile,
  normalizedAgentFile, decideAgentAction
} from "../src/race_agent_v1.js";

test("common Agent File validates all seven fields without external-AI privileges", ()=>{
  expect(AGENT_FIELDS).toHaveLength(7);
  for(const preset of Object.keys(AGENT_PRESETS)){
    const file=makeAgentFile(preset);
    expect(validateAgentFile(file)).toEqual({valid:true,errors:[]});
    expect(normalizedAgentFile(file).file).toEqual(file);
  }
  expect(validateAgentFile({...makeAgentFile(), privilegedLiveAI:true}).valid).toBe(false);
  expect(validateAgentFile({...makeAgentFile(), positioning:"TELEPORT"}).valid).toBe(false);
});

test("Agent decisions respond to pressure and fatigue, never guarantee movement", ()=>{
  const file=makeAgentFile();
  expect(decideAgentAction(file,{progress:.22,pressure:.7,stamina:90,fatigue:.05,blocked:true}).command).toBe("SHIFT_LINE");
  expect(decideAgentAction(file,{progress:.30,pressure:0,stamina:15,fatigue:.8,blocked:false}).command).toBe("HOLD");
  expect(decideAgentAction(file,{progress:.91,pressure:0,stamina:75,fatigue:.1,blocked:false}).command).toBe("PUSH");
  const wait=makeAgentFile();
  wait.traffic="WAIT";
  expect(decideAgentAction(wait,{progress:.22,pressure:.9,stamina:88,fatigue:.1,blocked:true}).command).toBe("HOLD");
});

test("stadium Agent setup is pre-race only; race runs unattended with visible orbs",async ({page},testInfo)=>{
  await page.goto("/evowild-test/race-stadium.html",{waitUntil:"networkidle"});
  const stage=page.locator("#stage");
  await expect(stage).toHaveAttribute("data-race-state","setup");
  await expect(stage).toHaveAttribute("data-manual-controls","0");
  await expect(page.locator("button[data-agent-command]")).toHaveCount(0);
  await expect(page.locator("[data-agent-field]")).toHaveCount(7);
  await page.locator("#presetSelect").selectOption("CLOSER");
  await expect(page.locator('[name="basePace"]')).toHaveValue("CONSERVE");
  await page.locator("#startAutonomous").click();
  await expect(stage).toHaveAttribute("data-agent-file-valid","1");
  await expect(stage).toHaveAttribute("data-agent-auto-all","18");
  await expect(page.locator("#preRacePanel")).toBeHidden();
  await expect(stage).toHaveAttribute("data-race-state","running",{timeout:9000});
  await expect(stage).toHaveAttribute("data-agent-decision-count",/[1-9]\d*/,{timeout:9000});
  await expect(stage).toHaveAttribute("data-selected-orb-mode",/(HOLD|PUSH|CONSERVE|SHIFT_LINE)/);
  await expect(stage).toHaveAttribute("data-selected-orb-x",/-?\d+\.\d+/);
  await expect(stage).toHaveAttribute("data-selected-orb-y",/-?\d+\.\d+/);
  const orbCount=Number(await stage.getAttribute("data-orb-count"));
  expect(orbCount).toBeGreaterThan(0);
  await expect(page.locator("#autoTimeline li").first()).toBeVisible();
  await expect(page.locator("#autoAgentPanel")).toBeVisible();
  // Keep evidence in Actions artifacts; no claim that a build gate proves art quality.
  fs.mkdirSync("test-results/visuals",{recursive:true});
  await page.screenshot({path:"test-results/visuals/stadium-agent-"+testInfo.project.name+".png",fullPage:true});
});

test("original race-quality manual review controls remain isolated",async ({page})=>{
  await page.goto("/evowild-test/race-quality.html",{waitUntil:"networkidle"});
  await expect(page.getByRole("button",{name:"PUSH",exact:true})).toBeVisible();
  await expect(page.locator("#stage")).toHaveAttribute("data-engine-lineage","lane5-fixed-step-plus-four-morph-run-sheets");
});
