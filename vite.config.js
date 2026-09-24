import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  base: "/evowild-test/",
  build: {
    rollupOptions: {
      input: {
        main: resolve(process.cwd(), "index.html"),
        mode7: resolve(process.cwd(), "mode7.html")
      }
    }
  }
});
