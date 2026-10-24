import { test, expect } from "@playwright/test";

test("Course Workshop can build, validate and race locally saved segments",async({page})=>{
  await page.goto("/evowild-test/course-builder.html",{waitUntil:"networkidle"});
  await expect(page.locator("#validation")).toHaveAttribute("data-valid","1");
  await expect(page.locator("#distance")).toHaveText("1,600");
  await page.locator("#courseName").fill("Marsh Test");
  await page.locator("#weather").selectOption("rain");
  await page.locator('#addSegment [name="length"]').selectOption("200");
  await page.locator('#addSegment [name="surface"]').selectOption("mud");
  await page.locator('#addSegment [name="width"]').selectOption("2");
  await page.locator('#addSegment [name="curve"]').selectOption("-1");
  await page.locator('#addSegment [name="grade"]').selectOption("0.08");
  await page.getByRole("button",{name:"+ ADD SEGMENT"}).click();
  await expect(page.locator("#distance")).toHaveText("1,800");
  await expect(page.locator(".segment")).toHaveCount(5);
  await expect(page.locator("#validation")).toHaveAttribute("data-valid","1");
  await page.getByRole("button",{name:"TEST IN REAL RACE"}).click();
  await expect(page).toHaveURL(/race-quality\.html\?course=custom/);
  const stage=page.locator("#stage");
  await expect(stage).toHaveAttribute("data-course-id","custom");
  await expect(stage).toHaveAttribute("data-course-distance","1800");
  await expect(stage).toHaveAttribute("data-course-weather","rain");
  await expect(stage).toHaveAttribute("data-field-size","18");
  await expect(page.locator("#courseSelect")).toHaveValue("custom");
  await expect(page.locator("#courseStatus")).toContainText("Marsh Test");
  await expect(stage).toHaveAttribute("data-run-sheets","ready",{timeout:15000});
});

test("Course Workshop rejects too-short courses and saves no invalid profile",async({page})=>{
  await page.goto("/evowild-test/course-builder.html",{waitUntil:"networkidle"});
  await page.locator(".segment-buttons button").nth(2).click();
  await page.locator(".segment-buttons button").nth(2).click();
  await page.locator(".segment-buttons button").nth(2).click();
  await expect(page.locator("#distance")).toHaveText("400");
  await expect(page.locator("#validation")).toHaveAttribute("data-valid","0");
  await expect(page.locator("#testCourse")).toBeDisabled();
  await expect(page.locator("#saveCourse")).toBeDisabled();
});
