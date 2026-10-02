import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("2.5D selection capture - Four Morph Quality", async ({ page }, testInfo) => {
  const errors = [];
  page.on("pageerror", e => errors.push(e.stack || String(e)));
  page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });

  await page.goto("/evowild-test/race-quality.html", { waitUntil: "networkidle" });
  const stage = page.locator("#stage");
  await expect(stage).toHaveAttribute("data-morph-set", "S,P,E,A");
  await expect(stage).toHaveAttribute("data-run-sheets", "ready", { timeout: 15000 });
  await expect(stage).toHaveAttribute("data-race-state", "running", { timeout: 8000 });

  fs.mkdirSync("artifacts/2p5d-survivor", { recursive: true });
  await page.waitForTimeout(1800);
  await stage.screenshot({ path: `artifacts/2p5d-survivor/2p5d-survivor-18-${testInfo.project.name}-early.png` });
  await page.waitForTimeout(5000);
  await stage.screenshot({ path: `artifacts/2p5d-survivor/2p5d-survivor-18-${testInfo.project.name}-mid.png` });

  await page.locator("#agentTargetSelect").selectOption("0");
  await page.getByRole("button", { name: "PUSH", exact: true }).click();
  await page.waitForTimeout(450);
  await expect(stage).toHaveAttribute("data-agent-focus-command", "PUSH");
  expect(Number(await stage.getAttribute("data-agent-focus-response"))).toBeGreaterThan(0.6);
  await stage.screenshot({ path: `artifacts/2p5d-survivor/2p5d-survivor-18-${testInfo.project.name}-agent-push.png` });
  await page.getByRole("button", { name: "CLEAR", exact: true }).click();
  await expect(stage).toHaveAttribute("data-agent-focus-command", "NEUTRAL");

  expect(Number(await stage.getAttribute("data-visible-racers"))).toBeGreaterThanOrEqual(3);
  expect(Number(await stage.getAttribute("data-camera-relevant-count"))).toBeLessThanOrEqual(6);
  expect(Number(await stage.getAttribute("data-visible-labels"))).toBeLessThanOrEqual(4);
  expect(Number(await stage.getAttribute("data-selected-speed"))).toBeGreaterThan(14);

  if (testInfo.project.name === "android-chromium") {
    const agentBox = await page.locator("#agentControl").boundingBox();
    expect(agentBox?.height ?? Infinity).toBeLessThan(140);
  }

  expect(errors, errors.join("\n")).toEqual([]);
});