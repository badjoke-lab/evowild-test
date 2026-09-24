import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 120000,
  use: {
    baseURL: "http://127.0.0.1:4174",
    trace: "retain-on-failure"
  },
  webServer: {
    command: "npm run preview -- --host 127.0.0.1 --port 4174",
    port: 4174,
    reuseExistingServer: false
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "android-chromium", use: { ...devices["Pixel 7"] } }
  ]
});
