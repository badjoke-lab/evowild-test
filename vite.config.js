import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/evowild-test/",
  build: {
    rollupOptions: {
      input: {
        main: resolve(process.cwd(), "index.html"),
        race2_5d: resolve(process.cwd(), "race-2_5d.html"),
        race_lane5: resolve(process.cwd(), "race-lane5.html"),
        race_quality: resolve(process.cwd(), "race-quality.html"),
        tripo_motion_review: resolve(process.cwd(), "tripo-motion-review.html")
      }
    }
  }
});
