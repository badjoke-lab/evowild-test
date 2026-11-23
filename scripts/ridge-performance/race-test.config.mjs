// Run the repository's ordinary game regression against the packaged build.
import {fileURLToPath} from 'node:url';
import {defineConfig} from '@playwright/test';
import config from '../../playwright.config.js';
export default defineConfig({...config,
  testDir:fileURLToPath(new URL('../../tests',import.meta.url)),testMatch:'race.spec.js',webServer:undefined,
  use:{...config.use,baseURL:process.env.RIDGE_ORIGIN,launchOptions:{
    executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',
    args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']
  }}
});
