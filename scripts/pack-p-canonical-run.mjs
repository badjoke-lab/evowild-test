// Reproduce the 12-frame P asset from the reviewed imagegen drawing.
// Only alpha-component extraction, rigid translation and lossless packing;
// no interpolation, limb warping, per-frame scaling or painted anatomy.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { chromium } from "@playwright/test";

const evidence = "docs/evidence/p-canonical-20261011";
const output = process.argv[2] || "work/p-canonical/candidate.webp";
const dataUrl = file => `data:image/${file.endsWith("webp") ? "webp" : "png"};base64,${fs.readFileSync(file).toString("base64")}`;
const phases = ["CONTACT", "LOAD", "PUSH", "TOE-OFF", "LIFT", "GATHER", "FLIGHT", "EXTEND", "REACH", "PRE-LAND", "LAND", "SETTLE"];
const clearance = [0, 0, 0, 0, 0, 16, 24, 12, 4, 0, 0, 0];
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium", headless: true, args: ["--no-sandbox"] });
try {
  const page = await browser.newPage();
  const result = await page.evaluate(async ({ raw, canonical, old, phases, clearance }) => {
    const load = async src => { const im = new Image(); im.src = src; await im.decode(); return im; };
    const make = (w, h) => { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; };
    const source = await load(raw);
    const c = make(source.width, source.height), ctx = c.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(source, 0, 0);
    const pixels = ctx.getImageData(0, 0, c.width, c.height), a = pixels.data;
    const seen = new Uint8Array(c.width * c.height), queue = new Int32Array(seen.length), components = [];
    for (let seed = 0; seed < seen.length; seed++) {
      if (seen[seed] || a[seed * 4 + 3] <= 12) continue;
      let head = 0, tail = 1, left = c.width, right = 0, top = c.height, bottom = 0;
      queue[0] = seed; seen[seed] = 1;
      while (head < tail) {
        const p = queue[head++], x = p % c.width, y = Math.floor(p / c.width);
        left = Math.min(left, x); right = Math.max(right, x); top = Math.min(top, y); bottom = Math.max(bottom, y);
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const nx = x + dx, ny = y + dy, n = ny * c.width + nx;
          if (nx < 0 || nx >= c.width || ny < 0 || ny >= c.height || seen[n] || a[n * 4 + 3] <= 12) continue;
          seen[n] = 1; queue[tail++] = n;
        }
      }
      if (tail < 1000) continue;
      const crop = make(right - left + 1, bottom - top + 1), cc = crop.getContext("2d"), data = cc.createImageData(crop.width, crop.height);
      for (const p of queue.slice(0, tail)) {
        const dest = ((Math.floor(p / c.width) - top) * crop.width + p % c.width - left) * 4;
        data.data.set(a.slice(p * 4, p * 4 + 4), dest);
      }
      cc.putImageData(data, 0, 0);
      components.push({ crop, bbox: [left, top, right + 1, bottom + 1], pixels: tail });
    }
    components.sort((a, b) => Math.floor(a.bbox[1] / 341) - Math.floor(b.bbox[1] / 341) || a.bbox[0] - b.bbox[0]);
    if (components.length !== 12) throw new Error(`Expected 12 complete creatures, got ${components.length}`);
    const sheet = make(416 * 4, 320 * 3), sc = sheet.getContext("2d"), frames = [];
    for (const [i, component] of components.entries()) {
      const frame = make(416, 320), fc = frame.getContext("2d");
      const x = Math.round((416 - component.crop.width) / 2), y = 296 - clearance[i] - component.crop.height;
      if (x < 12 || y < 12) throw new Error(`Clipped frame ${i}`);
      fc.drawImage(component.crop, x, y);
      sc.drawImage(frame, (i % 4) * 416, Math.floor(i / 4) * 320);
      frames.push(frame);
      component.outputBounds = [x, y, x + component.crop.width, y + component.crop.height];
    }
    const checker = (canvas, cell = 16) => {
      const cc = canvas.getContext("2d");
      for (let y = 0; y < canvas.height; y += cell) for (let x = 0; x < canvas.width; x += cell) {
        cc.fillStyle = ((x / cell + y / cell) % 2) ? "#e0e6e8" : "#f2f4f4"; cc.fillRect(x, y, cell, cell);
      }
      return cc;
    };
    const contact = make(416 * 4, 350 * 3), pc = checker(contact);
    frames.forEach((f, i) => {
      const x = i % 4 * 416, y = Math.floor(i / 4) * 350;
      pc.drawImage(f, x, y); pc.strokeStyle = "#61808a"; pc.beginPath(); pc.moveTo(x + 12, y + 296); pc.lineTo(x + 404, y + 296); pc.stroke();
      pc.fillStyle = "#132831"; pc.font = "17px monospace"; pc.fillText(`${String(i + 1).padStart(2, "0")} ${phases[i]}`, x + 16, y + 332);
    });
    const ref = await load(canonical), previous = await load(old);
    const compare = make(1248, 630), bc = checker(compare);
    bc.fillStyle = "#102732"; bc.fillRect(0, 0, compare.width, 58); bc.fillStyle = "#ffffff"; bc.font = "20px sans-serif";
    ["Canonical P (mirrored)", "Old P / CONTACT", "New P / CONTACT"].forEach((label, i) => bc.fillText(label, i * 416 + 20, 36));
    // Same 370 px silhouette width for identity comparison; disclose this in the review.
    const drawFit = (image, sx, sy, sw, sh, column, mirror = false) => {
      const height = sh * 370 / sw;
      bc.save(); bc.translate(column * 416 + (mirror ? 393 : 23), 370 - height); if (mirror) bc.scale(-1, 1);
      bc.drawImage(image, sx, sy, sw, sh, 0, 0, 370, height); bc.restore();
    };
    drawFit(ref, 0, 0, ref.width, ref.height, 0, true);
    drawFit(previous, 0, 0, 256, 256, 1);
    drawFit(components[0].crop, 0, 0, components[0].crop.width, components[0].crop.height, 2);
    bc.fillStyle = "#102732"; bc.font = "17px sans-serif"; bc.fillText("Race-scale silhouettes / 110 px width", 20, 427);
    [ref, previous, components[0].crop].forEach((im, i) => {
      const silhouette = make(i === 1 ? 256 : im.width, i === 1 ? 256 : im.height), cc = silhouette.getContext("2d");
      cc.drawImage(im, 0, 0); cc.globalCompositeOperation = "source-in"; cc.fillStyle = "#152731"; cc.fillRect(0, 0, silhouette.width, silhouette.height);
      bc.save(); bc.translate(i * 416 + (i === 0 ? 263 : 153), 460); if (i === 0) bc.scale(-1, 1);
      bc.drawImage(silhouette, 0, 0, 110, silhouette.height * 110 / silhouette.width); bc.restore();
    });
    const race = make(4 * 240, 3 * 160), rc = checker(race);
    frames.forEach((f, i) => {
      const x = i % 4 * 240, y = Math.floor(i / 4) * 160;
      // Actual source frame width, including its shared transparent gutter.
      rc.drawImage(f, x + 60, y + 16, 120, 320 * 120 / 416);
      rc.fillStyle = "#132831"; rc.font = "14px monospace"; rc.fillText(`${i + 1} ${phases[i]}`, x + 20, y + 137);
    });
    return {
      sheet: sheet.toDataURL(), contact: contact.toDataURL(), comparison: compare.toDataURL(), race: race.toDataURL(),
      frames: frames.map(f => f.toDataURL()),
      audit: { frameCount: 12, layout: [4, 3], frameSize: [416, 320], sharedScale: 1, anchor: "bottom-center", baseline: 296, clearance, phases, components: components.map(({ crop, ...rest }) => rest) }
    };
  }, { raw: dataUrl(`${evidence}/generated-source.png`), canonical: dataUrl("public/concept/P.webp"), old: dataUrl(`${evidence}/old-p-run-sheet.webp`), phases, clearance });
  fs.mkdirSync(path.dirname(output), { recursive: true });
  const write = (file, url) => fs.writeFileSync(file, Buffer.from(url.split(",")[1], "base64"));
  const png = output.replace(/\.webp$/, ".png");
  write(png, result.sheet);
  execFileSync("magick", [png, "-define", "webp:lossless=true", output]);
  write(`${evidence}/contact-sheet.png`, result.contact);
  write(`${evidence}/canonical-old-new.png`, result.comparison);
  write(`${evidence}/race-size-contact-sheet.png`, result.race);
  fs.writeFileSync(`${evidence}/packing-audit.json`, JSON.stringify(result.audit, null, 2) + "\n");
  fs.mkdirSync("work/p-canonical/frames", { recursive: true });
  result.frames.forEach((url, i) => write(`work/p-canonical/frames/${String(i).padStart(2, "0")}.png`, url));
  const durations = [0.50,0.58,0.60,0.45,0.40,0.28,0.26,0.38,0.52,0.58,0.70,0.75];
  for (const [name, speed] of [["run-cycle.gif",1],["run-cycle-slow.gif",2]]) {
    const args = [];
    durations.forEach((duration, i) => args.push("-delay", String(Math.round(duration/(19*0.94*0.75)*100*speed)), `work/p-canonical/frames/${String(i).padStart(2,"0")}.png`));
    execFileSync("magick", [...args, "-background", "#e0e6e8", "-alpha", "remove", "-alpha", "off", "-loop", "0", `${evidence}/${name}`]);
  }
  console.log(JSON.stringify({ output, frameCount: 12, layout: "4x3", frameSize: [416, 320] }));
} finally { await browser.close(); }
