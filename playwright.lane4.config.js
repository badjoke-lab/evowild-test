import { defineConfig, devices } from "@playwright/test";

const launchOptions = {
  args: [
    "--no-sandbox",
    "--enable-unsafe-swiftshader",
    "--use-gl=angle",
    "--enable-webgl",
    "--ignore-gpu-blocklist"
  ]
};

export default defineConfig({
  testDir: "./tests",
  timeout: 150000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:4174",
    trace: "retain-on-failure",
    launchOptions
  },
  webServer: {
    command: "npm run preview -- --host 127.0.0.1 --port 4174",
    port: 4174,
    reuseExistingServer: false
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"], launchOptions } },
    { name: "android-chromium", use: { ...devices["Pixel 7"], launchOptions } }
  ]
});
