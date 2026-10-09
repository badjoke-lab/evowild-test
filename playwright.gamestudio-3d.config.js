import {defineConfig, devices} from '@playwright/test';
export default defineConfig({
  testDir:'./tests',
  testMatch:['gamestudio-3d.spec.js','motion-first.spec.js'],
  workers:1,
  timeout:45000,
  outputDir:'test-results/gamestudio-3d',
  reporter:[['list'],['json',{outputFile:'test-results/gamestudio-3d-results.json'}]],
  use:{baseURL:process.env.BASE_URL || 'http://127.0.0.1:4173', trace:'retain-on-failure',
    launchOptions:{executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',args:['--no-sandbox','--enable-unsafe-swiftshader']}},
  webServer: process.env.BASE_URL ? undefined : {command:'npm run dev -- --host 127.0.0.1 --port 4173 --strictPort',port:4173,reuseExistingServer:true},
  projects:[
    {name:'desktop-chromium',use:{...devices['Desktop Chrome'],viewport:{width:1280,height:720}}},
    {name:'android-chromium',use:{...devices['Pixel 7']}}
  ]
});
