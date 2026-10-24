import { test, expect } from "@playwright/test";
import {
  COURSE_PRESETS, getCourse, DEFAULT_COURSE_ID, courseSectionAt,
  courseEffects, validateCourse
} from "../src/course_profiles_2p5d.js";

test("2.5D courses have validated modules and original defaults remain neutral", async () => {
  expect(COURSE_PRESETS).toHaveLength(5);
  for (const course of COURSE_PRESETS) {
    const result=validateCourse(course);
    expect(result.errors).toEqual([]);
    expect(result.distance).toBe(course.distance);
    expect(courseSectionAt(course, course.distance).part).toBe(course.segments.at(-1));
  }
  const original=getCourse(DEFAULT_COURSE_ID);
  expect(original.distance).toBe(1600);
  for (const morph of ["S","P","E","A"]) {
    expect(courseEffects(original,240,morph,0).pace).toBe(1);
    expect(courseEffects(original,240,morph,0).stamina).toBe(1);
  }
  expect(getCourse("unknown").id).toBe(DEFAULT_COURSE_ID);
});

test("course effects change by morph and segment, not a predetermined winner", async () => {
  const mud=getCourse("heavy-1200");
  const bend=getCourse("switchback-1200");
  const sprint=getCourse("sprint-800");
  expect(courseEffects(mud,30,"P").pace).toBeGreaterThan(courseEffects(mud,30,"S").pace);
  expect(courseEffects(mud,30,"P").stamina).toBeLessThan(courseEffects(mud,30,"S").stamina);
  expect(courseEffects(bend,30,"A").pace).toBeGreaterThan(courseEffects(bend,30,"P").pace);
  expect(courseEffects(sprint,30,"S").pace).toBeGreaterThan(courseEffects(sprint,30,"E").pace);
  expect(courseEffects(bend,450,"A",1).pace).toBeLessThan(courseEffects(bend,450,"A",0).pace);
  const invalid={segments:[{length:100,surface:"lava",width:8,curve:2,grade:1}]};
  expect(validateCourse(invalid).valid).toBe(false);
});

test("race screen course picker restarts with real selected distance and surface", async ({page}) => {
  await page.goto("/evowild-test/race-quality.html?course=heavy-1200", {waitUntil:"networkidle"});
  const stage=page.locator("#stage");
  await expect(stage).toHaveAttribute("data-course-model","segmented-v1");
  await expect(stage).toHaveAttribute("data-field-size","18");
  await expect(stage).toHaveAttribute("data-course-id","heavy-1200");
  await expect(stage).toHaveAttribute("data-course-distance","1200");
  await expect(stage).toHaveAttribute("data-course-surface","mud");
  await expect(page.locator("#courseStatus")).toContainText("HEAVY 1200");
  await expect(stage).toHaveAttribute("data-course-pace-factor",/\d+\.\d+/);
  await page.locator("#courseSelect").selectOption("sprint-800");
  await expect(stage).toHaveAttribute("data-course-id","sprint-800");
  await expect(stage).toHaveAttribute("data-course-distance","800");
  await expect(stage).toHaveAttribute("data-course-surface","fast");
  await expect(page.locator("#courseStatus")).toContainText("SPRINT 800");
  await expect(stage).toHaveAttribute("data-run-sheets","ready",{timeout:15000});
  await expect(stage).toHaveAttribute("data-race-state","running",{timeout:8000});
});
