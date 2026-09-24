import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/evowild-test/",
  build: {
    rollupOptions: {
      input: {
        main: resolve(process.cwd(), "index.html"),
        race2_5d: resolve(process.cwd(), "race-2_5d.html"),\n        race2_5d_lane4: resolve(process.cwd(), "race-2_5d-lane4.html")
      }
    }
  }
});
