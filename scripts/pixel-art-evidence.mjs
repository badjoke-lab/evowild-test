import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { cpus, tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { chromium, devices } from 'playwright';

const task = process.argv[2] ?? 'all';
assert(['all', 'capture', 'benchmark', 'heavy'].includes(task), 'Expected all, capture, benchmark, or heavy.');
const base = process.env.PIXEL_ART_URL ?? 'http://localhost:5173/evowild-test/';
const out = resolve(process.env.PIXEL_ART_OUT ?? 'docs/evidence/pixel-art');
const modes = ['A', 'B', 'C', 'D'];
const motions = ['idle', 'slow', 'run'];
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH,
  args: ['--enable-precise-memory-info', '--enable-unsafe-swiftshader', '--use-angle=swiftshader']
});
const pixel = devices['Pixel 7'];
const profiles = {
  desktop: { viewport: { width: 1360, height: 960 }, deviceScaleFactor: 1 },
  'pixel-7-emulated': {
    ...pixel, userAgent: pixel.userAgent.replace(/Chrome\/[\d.]+/, `Chrome/${browser.version()}`)
  }
};
await mkdir(out, { recursive: true });
const writeJson = (name, value) => writeFile(join(out, name), JSON.stringify(value, null, 2) + '\n');
const storePng = (name, png) => writeFile(name, Buffer.from(png.split(',')[1], 'base64'));

async function open(profile, errors) {
  const context = await browser.newContext(profile);
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => {
    if (message.type() === 'error' || /WebGL.*(INVALID|Error)/i.test(message.text())) errors.push(message.text());
  });
  await page.goto(new URL('pixel-art.html?evidence', base).href);
  await page.waitForFunction(() => !!window.pixelArtExperiment);
  assert(await page.getByRole('button', { name: 'D Gaussian splats' }).isEnabled());
  return { context, page };
}

async function smoke(page) {
  await page.getByRole('button', { name: 'C ピクセル点群' }).click();
  await page.locator('#motion').selectOption('slow');
  await page.locator('#count').selectOption('10');
  await page.locator('#density').fill('2200');
  await page.locator('#size').fill('60');
  await page.locator('#resolution').fill('45');
  await page.locator('#colors').fill('16');
  await page.locator('#shading').fill('40');
  await page.locator('#outline').fill('25');
  await page.locator('#landscape').uncheck();
  await page.locator('#orbit').click();
  await page.waitForFunction(() => Number(document.querySelector('#points').textContent.replace(/\D/g, '')) === 22000);
  assert.deepEqual(await page.evaluate(() => window.pixelArtExperiment.inspect().settings), {
    mode: 'C', count: 10, motion: 'slow', orbit: true, landscape: false, density: 2200, size: 60,
    resolution: 45, colors: 16, shading: 40, outline: 25
  });
  const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#capture').click()]);
  assert.equal(download.suggestedFilename(), 'evowild-C-slow-10.png');
  await page.locator('#reset-camera').click();
  const layout = await page.evaluate(() => ({ css: innerWidth, document: document.documentElement.scrollWidth }));
  assert(layout.document <= layout.css, 'The page should fit the viewport width.');
}

async function poseAudit(context, page) {
  const review = await context.newPage();
  try {
    await review.goto(new URL('s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v2', base).href);
    await review.waitForFunction(() => !!window.sRunReview);
    const rows = [];
    for (const rate of [.5, 1]) {
      const steps = 120;
      const baseline = await review.evaluate(({ rate, steps }) => {
        const review = window.sRunReview;
        review.setRate(rate);
        review.setPhase(0, 'SIDE', false);
        const dt = 1 / (2.4 * Math.sqrt(rate) * steps);
        return Array.from({ length: steps + 1 }, (_, i) => {
          if (i) review.step(dt);
          return review.motionSample().contact.limbs.map(limb => limb.joints);
        });
      }, { rate, steps });
      const experiment = await page.evaluate(({ rate, steps }) => {
        const api = window.pixelArtExperiment;
        api.capture({ mode: 'A', motion: 'idle' });
        const { source, subjects: [subject] } = api.inspect();
        const { mesh } = subject;
        const { points } = source.surface;
        const ids = points.attributes.position;
        const uv = points.attributes.sampleUV;
        const a = mesh.position.clone();
        const b = a.clone();
        const c = a.clone();
        const sample = a.clone();
        const reference = a.clone();
        const texels = source.surface.vertices.image.data;
        const bind = mesh.bindMatrix.clone();
        const bone = bind.clone();
        const value = mesh.position.clone();
        const packedVertex = mesh.position.clone();
        const shaderVertex = (id, result) => {
          const offset = id * 12;
          packedVertex.fromArray(texels, offset).applyMatrix4(mesh.bindMatrix);
          result.set(0, 0, 0);
          for (let i = 0; i < 4; i++) {
            const weight = texels[offset + 8 + i];
            if (!weight) continue;
            bone.fromArray(mesh.skeleton.boneMatrices, texels[offset + 4 + i] * 16);
            result.addScaledVector(value.copy(packedVertex).applyMatrix4(bone), weight);
          }
          return result.applyMatrix4(mesh.bindMatrixInverse);
        };
        let maxSurfaceDeltaM = 0;
        let maxSupportGapM = 0;
        let maxPenetrationM = 0;
        let supportSamples = 0;
        const joints = [];
        subject.reset(rate);
        const dt = subject.kinematics(rate).period / steps;
        for (let i = 0; i <= steps; i++) {
          if (i) subject.step(dt, rate);
          mesh.skeleton.update();
          joints.push(subject.contact.limbs.map(limb => limb.joints));
          for (const [foot, patch] of source.footSurfaces.entries()) {
            if (!['CONTACT', 'PUSH'].includes(subject.contact.limbs[foot].stage)) continue;
            const y = Math.min(...patch.guardIds.map(id => mesh.localToWorld(mesh.getVertexPosition(id, a)).y));
            maxSupportGapM = Math.max(maxSupportGapM, y);
            maxPenetrationM = Math.max(maxPenetrationM, -y);
            supportSamples++;
          }
          for (let s = 0; s < 256; s++) {
            const ai = ids.getX(s), bi = ids.getY(s), ci = ids.getZ(s);
            const v = uv.getX(s), w = uv.getY(s), u = 1 - v - w;
            sample.copy(shaderVertex(ai, a)).multiplyScalar(u)
              .addScaledVector(shaderVertex(bi, b), v).addScaledVector(shaderVertex(ci, c), w);
            reference.copy(mesh.getVertexPosition(ai, a)).multiplyScalar(u)
              .addScaledVector(mesh.getVertexPosition(bi, b), v).addScaledVector(mesh.getVertexPosition(ci, c), w);
            maxSurfaceDeltaM = Math.max(maxSurfaceDeltaM, mesh.localToWorld(sample).distanceTo(mesh.localToWorld(reference)));
          }
        }
        return { joints, maxSurfaceDeltaM, maxSupportGapM, maxPenetrationM, supportSamples, samplesPerFrame: 256 };
      }, { rate, steps });
      const { joints, ...summary } = experiment;
      let maxJointDeltaM = 0;
      for (const [frame, limbs] of baseline.entries()) {
        for (const [foot, limb] of limbs.entries()) {
          for (const [index, joint] of limb.entries()) {
            maxJointDeltaM = Math.max(maxJointDeltaM, Math.hypot(...joint.map((x, axis) => x - joints[frame][foot][index][axis])));
          }
        }
      }
      assert(maxJointDeltaM < .00001, `D3-C joint drift: ${maxJointDeltaM} m`);
      assert(summary.maxSurfaceDeltaM < .00001, `Surface sampling drift: ${summary.maxSurfaceDeltaM} m`);
      assert(summary.maxSupportGapM < .001 && summary.maxPenetrationM < .001, 'Support should stay within 1 mm.');
      rows.push({ rate, frames: steps + 1, maxJointDeltaM, ...summary });
    }
    return rows;
  } finally {
    await review.close();
  }
}

async function captureAll() {
  const errors = [];
  const { context, page } = await open(profiles.desktop, errors);
  const temp = await mkdtemp(join(tmpdir(), 'evowild-pixel-art-'));
  try {
    const phaseChecks = [];
    for (const mode of modes) {
      const dir = join(temp, mode);
      await mkdir(dir);
      for (const motion of motions) {
        const seconds = motion === 'idle' ? 0 : .25;
        const { png, phase, points } = await page.evaluate(
          options => window.pixelArtExperiment.capture(options), { mode, motion, seconds }
        );
        assert.equal(points, mode === 'A' ? 0 : 4000);
        phaseChecks.push({ mode, motion, phase, points });
        await storePng(join(out, `${mode}-${motion}.png`), png);
      }
      for (let frame = 0; frame < 120; frame++) {
        const motion = frame < 12 ? 'idle' : frame < 36 ? 'slow' : 'run';
        const seconds = motion === 'idle' ? 0 : (frame - (motion === 'slow' ? 12 : 36)) / 24;
        const azimuth = 1.14 + (motion === 'run' ? (frame - 36) / 84 * Math.PI * 2 : 0);
        const { png } = await page.evaluate(options => window.pixelArtExperiment.capture(options), { mode, motion, seconds, azimuth });
        await storePng(join(dir, `${String(frame).padStart(3, '0')}.png`), png);
      }
      execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '24', '-i', `${dir}/%03d.png`,
        '-vf', 'scale=840:-2', '-c:v', 'libx264', '-threads', '1', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', join(out, `${mode}.mp4`)]);
      console.log(`Captured mode ${mode}`);
    }
    const tiles = modes.map((mode, i) => `[${i}:v]scale=620:-2,drawtext=text=${mode}:x=16:y=12:fontcolor=white:fontsize=22:box=1:boxcolor=black@0.65:boxborderw=6[${mode}]`).join(';');
    execFileSync('ffmpeg', ['-v', 'error', '-y', ...modes.flatMap(mode => ['-i', join(out, `${mode}.mp4`)]),
      '-filter_complex_threads', '1', '-filter_complex', `${tiles};[A][B][C][D]xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0`,
      '-c:v', 'libx264', '-threads', '1', '-crf', '21', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', join(out, 'comparison.mp4')], { stdio: 'pipe' });
    const contact = await poseAudit(context, page);
    await page.evaluate(() => window.pixelArtExperiment.capture({ mode: 'C', motion: 'run', seconds: .25 }));
    await page.screenshot({ path: join(out, 'desktop-ui.png'), fullPage: true });
    await page.evaluate(() => window.pixelArtExperiment.resume());
    await smoke(page);
    const mobile = await open(profiles['pixel-7-emulated'], errors);
    try {
      await mobile.page.evaluate(() => window.pixelArtExperiment.capture({ mode: 'C', motion: 'run', seconds: .25 }));
      await mobile.page.screenshot({ path: join(out, 'pixel-7-ui.png'), fullPage: true });
      await mobile.page.evaluate(() => window.pixelArtExperiment.resume());
      await smoke(mobile.page);
    } finally {
      await mobile.context.close();
    }
    await writeJson('validation.json', { browser: browser.version(), errors, phaseChecks, contact, motionFramesPerMode: 120, encodedFps: 24 });
    assert.deepEqual(errors, []);
  } finally {
    await context.close();
    await rm(temp, { recursive: true, force: true });
  }
}

async function benchmarkAll(heavy = false) {
  for (const [name, profile] of Object.entries(profiles)) {
    const errors = [];
    const { context, page } = await open(profile, errors);
    try {
      console.log(`Benchmarking ${name}${heavy ? ' / D100' : ''}`);
      const result = await page.evaluate(heavy => window.pixelArtExperiment.benchmark(heavy ? {
        warmup: 1800, windowMs: 15000, filter: ({ mode, count }) => mode === 'D' && count === 100
      } : undefined), heavy);
      assert.equal(result.results.length, heavy ? 1 : 16);
      assert(result.results.every(row => row.frames > 0 && row.fps > 0 && row.pointCount === (row.mode === 'A' ? 0 : 4000 * row.count)));
      const suffix = heavy ? 'd100-benchmark' : 'benchmark';
      await writeJson(`${name}-${suffix}.json`, { ...result, profile: name, browser: browser.version(), cpu: cpus()[0].model, cpuThreads: cpus().length, errors });
      assert.deepEqual(errors, []);
    } finally {
      await context.close();
    }
  }
}

try {
  if (task !== 'capture') await benchmarkAll(task === 'heavy');
  if (task === 'all' || task === 'capture') await captureAll();
} finally {
  await browser.close();
}
