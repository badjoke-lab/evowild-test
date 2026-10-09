import path from "node:path";
import { defineConfig } from "@playwright/test";
import base from "./playwright.config.js";

const evidenceDir = path.resolve(process.env.GAMESTUDIO_EVIDENCE_DIR || "artifacts/gamestudio-2p5d/latest");
const executablePath = process.env.GAMESTUDIO_CHROMIUM_PATH;

// Keep the existing Android/desktop projects and server; change only evidence output.
export default defineConfig({
  ...base,
  workers: 2,
  outputDir: path.join(evidenceDir, "test-results"),
  reporter: [["list"], ["json", { outputFile: path.join(evidenceDir, "tests.json") }]],
  use: {
    ...base.use,
    screenshot: "only-on-failure",
    video: "on",
    ...(executablePath ? {
      launchOptions: { executablePath, args: ["--enable-unsafe-swiftshader"] }
    } : {})
  }
});
