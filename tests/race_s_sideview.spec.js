import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("S visual lane uses one continuous gait runner with stable contact", async ({ page }, testInfo) => {
  test.setTimeout(60000);

  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", error => pageErrors.push(error.stack || String(error)));
  page.on("console", message => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto("/evowild-test/race-s-sideview.html", { waitUntil: "networkidle" });

  const canvas = page.locator("#scene");
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute("data-mode", "s-continuous-motion");
  await expect(canvas).toHaveAttribute("data-creature-count", "1");
  await expect(canvas).toHaveAttribute("data-agent", "off");
  await expect(canvas).toHaveAttribute("data-hud", "off");
  await expect(canvas).toHaveAttribute("data-gait-source", "motion-first-s-gait-v3");

  await expect(page.locator("#runtimeControls")).toBeHidden();
  await expect(page.locator("#runnerSelect option")).toHaveCount(1);
  await expect(page.locator("#morphReadout")).toHaveText("S");
  await expect(page.locator("#cameraReadout")).toHaveText("SIDE");

  await page.waitForTimeout(4200);

  await expect(canvas).toHaveAttribute("data-ik-clamped", "0");

  const stanceSlip = Number(await canvas.getAttribute("data-max-stance-slip"));
  expect(Number.isFinite(stanceSlip)).toBeTruthy();
  expect(stanceSlip).toBeLessThan(0.12);

  const bodyStretch = Number(await canvas.getAttribute("data-max-body-stretch"));
  expect(Number.isFinite(bodyStretch)).toBeTruthy();
  expect(bodyStretch).toBeGreaterThan(0.14);

  expect(pageErrors, pageErrors.join("\n")).toEqual([]);
  expect(consoleErrors, consoleErrors.join("\n")).toEqual([]);

  fs.mkdirSync("test-results/visuals", { recursive: true });
  await canvas.screenshot({
    path: "test-results/visuals/" + testInfo.project.name + "-s-continuous-side.png"
  });
});
