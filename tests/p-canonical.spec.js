import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const root = process.env.P_CANONICAL_EVIDENCE_DIR || "work/p-canonical/runtime";
const phases = ["CONTACT", "CONTACT_TO_PUSH", "PUSH", "PUSH_TO_LIFT", "LIFT", "LIFT_TO_FLIGHT", "FLIGHT", "FLIGHT_TO_REACH", "REACH", "REACH_TO_LAND", "LAND", "LAND_TO_CONTACT"];
const fixedTime = new Date("2026-10-11T00:00:00Z");
const evidence = (info, name) => {
  const dir = path.join(root, info.project.name); fs.mkdirSync(dir, { recursive: true }); return path.join(dir, name);
};

test("canonical P decodes twelve complete transparent poses with authored flight clearance", async ({ page }, info) => {
  await page.goto("/evowild-test/race-quality.html?selected=2");
  await expect(page.locator("#stage")).toHaveAttribute("data-run-sheets", "ready");
  const frames = await page.evaluate(async () => {
    const image = new Image(); image.src = "/evowild-test/concept/p-run-sheet.webp"; await image.decode();
    if (image.naturalWidth !== 1664 || image.naturalHeight !== 960) throw new Error("Unexpected P atlas size");
    const canvas = document.createElement("canvas"); canvas.width = 416; canvas.height = 320;
    const ctx = canvas.getContext("2d", { willReadFrequently:true }), result = [];
    for (let i = 0; i < 12; i++) {
      ctx.clearRect(0,0,416,320); ctx.drawImage(image, i%4*416, Math.floor(i/4)*320,416,320,0,0,416,320);
      const data = ctx.getImageData(0,0,416,320).data;
      let left=416, right=-1, top=320, bottom=-1, clear=0, opaque=0;
      for (let p=0;p<416*320;p++) {
        if (data[p*4+3]===0) clear++;
        if (data[p*4+3]<=12) continue;
        opaque++; const x=p%416,y=Math.floor(p/416);
        left=Math.min(left,x);right=Math.max(right,x);top=Math.min(top,y);bottom=Math.max(bottom,y);
      }
      const hash=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",data)),n=>n.toString(16).padStart(2,"0")).join("");
      result.push({i,left,right,top,bottom,clear,opaque,hash});
    }
    return result;
  });
  expect(new Set(frames.map(f=>f.hash)).size).toBe(12);
  for (const f of frames) {
    expect(f.clear).toBeGreaterThan(50000); expect(f.opaque).toBeGreaterThan(30000);
    expect(f.left).toBeGreaterThan(12); expect(f.right).toBeLessThan(404);
    expect(f.top).toBeGreaterThan(12); expect(f.bottom).toBeLessThan(308);
  }
  expect(frames[0].bottom).toBe(295); expect(frames[10].bottom).toBe(295);
  expect(frames[6].bottom).toBe(271); // 24px airborne; never auto-ground this pose.
  fs.writeFileSync(evidence(info,"atlas-audit.json"),JSON.stringify({frames, sha256:crypto.createHash("sha256").update(fs.readFileSync("public/concept/p-run-sheet.webp")).digest("hex")},null,2));
});

test("canonical P twelve runtime poses, cycle wrap and normal race visual evidence", async ({ page }, info) => {
  test.setTimeout(120000);
  const errors=[]; page.on("pageerror",e=>errors.push(e.message));
  await page.clock.install({time:fixedTime}); await page.clock.pauseAt(fixedTime);
  const stage=page.locator("#stage"), crops=[], audit=[];
  for (let i=0;i<12;i++) {
    await page.goto(`/evowild-test/race-quality.html?motionReview=1&selected=2&motionFrame=${i}`, {waitUntil:"networkidle"});
    await expect(stage).toHaveAttribute("data-run-sheets","ready"); await page.clock.runFor(4600);
    await expect(stage).toHaveAttribute("data-selected-run-frame",String(i));
    await expect(stage).toHaveAttribute("data-selected-run-phase",phases[i]);
    await expect(stage).toHaveAttribute("data-p-ground-anchor","authored-baseline-296-of-320");
    await expect(stage).toHaveAttribute("data-p-horizontal-adjust","0.00");
    audit.push(await stage.evaluate(el=>({...el.dataset})));
    crops.push(await page.evaluate(()=>{
      const stage=document.querySelector("#stage"), canvas=document.querySelector("#raceCanvas");
      const dpr=canvas.width/canvas.getBoundingClientRect().width;
      const x=Number(stage.dataset.selectedX),y=Number(stage.dataset.selectedY);
      const c=document.createElement("canvas");c.width=420;c.height=340;
      c.getContext("2d").drawImage(canvas,(x-210)*dpr,(y-280)*dpr,420*dpr,340*dpr,0,0,420,340);
      return c.toDataURL();
    }));
    if(i===6) await page.screenshot({path:evidence(info,"isolated-flight.png")});
  }
  // Assert the real live sampler reaches late frames and wraps, not only pinned URLs.
  await page.goto("/evowild-test/race-quality.html?motionReview=1&selected=2",{waitUntil:"networkidle"});
  await expect(stage).toHaveAttribute("data-run-sheets","ready"); await page.clock.runFor(4600);
  const live=[];
  for(let i=0;i<90;i++){ await page.clock.runFor(17);live.push(Number(await stage.getAttribute("data-selected-run-frame"))); }
  expect([...new Set(live)].sort((a,b)=>a-b)).toEqual(Array.from({length:12},(_,i)=>i));
  expect(live.some((value,i)=>i>0&&live[i-1]===11&&value===0)).toBe(true);
  // Flight and contact use exactly the same canvas baseline correction.
  expect(new Set(audit.map(a=>a.pFootAdjust)).size).toBe(1);
  const contact=await page.evaluate(async ({crops,phases})=>{
    const c=document.createElement("canvas");c.width=1680;c.height=1110;const ctx=c.getContext("2d");
    ctx.fillStyle="#10212b";ctx.fillRect(0,0,c.width,c.height);
    for(let i=0;i<crops.length;i++){const im=new Image();im.src=crops[i];await im.decode();const x=i%4*420,y=Math.floor(i/4)*370;ctx.drawImage(im,x,y);ctx.fillStyle="#ffffff";ctx.font="16px monospace";ctx.fillText(`${i+1} ${phases[i]}`,x+10,y+360);}
    return c.toDataURL();
  },{crops,phases});
  fs.writeFileSync(evidence(info,"runtime-contact-sheet.png"),Buffer.from(contact.split(",")[1],"base64"));
  await page.goto("/evowild-test/race-quality.html?selected=2",{waitUntil:"networkidle"});
  await expect(stage).toHaveAttribute("data-run-sheets","ready"); await page.clock.runFor(4600);
  await expect(stage).toHaveAttribute("data-field-size","18"); await expect(stage).toHaveAttribute("data-selected-morph","P");
  await expect(stage).toHaveAttribute("data-s-frame-count","6");await expect(stage).toHaveAttribute("data-e-frame-count","6");await expect(stage).toHaveAttribute("data-a-frame-count","6");
  await page.screenshot({path:evidence(info,"race-size-18-runners.png")});
  expect(errors).toEqual([]);
  fs.writeFileSync(evidence(info,"runtime-audit.json"),JSON.stringify({viewport:info.project.use,observed:[...new Set(live)].sort((a,b)=>a-b),wrap11to0:true,errors,frames:audit},null,2));
});
