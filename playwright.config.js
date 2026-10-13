import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30000,
  // Canvas/WebGL software rendering shares the two-core CI runner. Run the
  // complete suite serially instead of competing for its render resources.
  workers: process.env.CI ? 1 : undefined,
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
