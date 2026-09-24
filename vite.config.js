import { defineConfig } from "vite";

export default defineConfig({
  base: process.env.EVOWILD_BASE || "/evowild-test/"
});
