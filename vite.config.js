import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  base: "/evowild-test/",
  build: {
    rollupOptions: {
      input: {
        main: resolve(process.cwd(), "index.html"),
        race2_5d: resolve(process.cwd(), "race-2_5d.html"),
        raceSSideview: resolve(process.cwd(), "race-s-sideview.html"),
        raceSOnlyV3: resolve(process.cwd(), "race-s-only-v3.html"),
        raceSHybrid: resolve(process.cwd(), "race-s-hybrid.html")
      }
    }
  }
});