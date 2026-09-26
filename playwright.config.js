import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testIgnore: ["**/lane4-v4.spec.js", "**/lane4-s.spec.js"],
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "retain-on-failure"
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 4173",
    port: 4173,
    reuseExistingServer: false
  },
  projects: [
    {
      name: "android-chromium",
      use: {
        ...devices["Pixel 7"]
      }
    },
    {
      name: "desktop-chromium",
      use: {
        ...devices["Desktop Chrome"]
      }
    }
  ]
});
