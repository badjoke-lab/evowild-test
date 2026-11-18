import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { ASSET, WORLD_SCALE, createSubject, layoutSubjects, loadSubject } from './subjects.js';
import { makeContactShadows, makeLandscape } from './landscape.js';
import { createRenderPipeline, makePointMaterial } from './render.js';
import { COUNTS, createGpuTimer, geometryBytes, sceneGeometryBytes, summarize } from './benchmark.js';
import './lab.css';

const $ = id => document.getElementById(id);
const modes = { A: '既存 3D', B: '表面点群', C: 'ピクセル点群', D: 'Gaussian splats' };
const motionText = { idle: '静止', slow: '歩行相当 · 0.5×', run: '走行 · 1.0×' };
const speed = { idle: 0, slow: .5, run: 1 };
const sliders = {
  density: value => `${value.toLocaleString()} 点 / 体`, size: value => `${value} mm`,
  resolution: value => `${value}%`, colors: value => `${value} 色`,
  shading: value => `${value}%`, outline: value => `${value}%`
};
const settings = { mode: 'A', count: 1, motion: 'run', orbit: false, landscape: true };
for (const key of Object.keys(sliders)) settings[key] = Number($(key).value);
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const canvas = $('scene');

function download(url, name) {
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
}

function showError(error) {
  $('status').textContent = error.message;
  $('status').hidden = false;
  console.error(error);
}

async function start() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
  renderer.info.autoReset = false;
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  const gl = renderer.getContext();
  const camera = new THREE.PerspectiveCamera(40, 1, .08 * WORLD_SCALE, 130 * WORLD_SCALE);
  const scene = new THREE.Scene();
  const props = makeLandscape(scene);
  const updateShadows = makeContactShadows(scene, Math.max(...COUNTS));
  const landscapeBytes = sceneGeometryBytes(scene);
  const controls = new OrbitControls(camera, canvas);
  controls.enablePan = false;
  controls.enableDamping = false;
  controls.minPolarAngle = .25;
  controls.maxPolarAngle = 1.48;
  controls.autoRotateSpeed = 4.5;
  const timer = createGpuTimer(gl);
  const pipeline = createRenderPipeline(renderer, scene, camera);
  const source = await loadSubject();
  const meshBytes = geometryBytes(source.mesh.geometry);
  const surfaceBytes = geometryBytes(source.surface.points) + source.surface.vertices.image.data.byteLength;
  const subjects = [];
  let active = [];
  let radius = 0;
  let manual = false;
  let lost = false;
  let lastTimestamp = null;
  let measurement;
  let liveGpu = null;
  let lastRefresh = 0;
  let report;

  function syncUI() {
    for (const button of modeButtons) {
      button.disabled = !!measurement || (button.dataset.mode === 'D' && !pipeline.canGaussian);
      button.setAttribute('aria-pressed', String(button.dataset.mode === settings.mode));
    }
    const pixelated = ['C', 'D'].includes(settings.mode);
    for (const [key, format] of Object.entries(sliders)) {
      $(key).disabled = !!measurement || settings.mode === 'A' || (['resolution', 'colors', 'outline'].includes(key) && !pixelated);
      $(key).value = settings[key];
      $(`${key}-value`).value = format(settings[key]);
    }
    for (const id of ['motion', 'count', 'landscape', 'orbit', 'reset-camera', 'capture', 'benchmark']) $(id).disabled = !!measurement || lost;
    $('export').disabled = !report || !!measurement;
    $('orbit').setAttribute('aria-pressed', String(settings.orbit));
    $('mode-label').textContent = `${settings.mode} · ${modes[settings.mode]}`;
    $('motion-label').textContent = motionText[settings.motion];
    $('motion').value = settings.motion;
    $('count').value = settings.count;
    $('landscape').checked = settings.landscape;
    $('control-note').textContent = {
      A: 'D3-C v2 の GLB メッシュと元の材質を使用。',
      B: '表面に固定した不透明な点を、画面解像度で描画。',
      C: '点群と背景を低解像度で描画し、パレットと深度輪郭を適用。',
      D: '面に沿う Gaussian を深度で選別し、加重合成後にピクセル化。'
    }[settings.mode];
    if (!pipeline.canGaussian) $('control-note').textContent += ' この環境は D に必要な浮動小数点描画に未対応です。';
  }

  function setCamera(azimuth = 1.14, elevation = .23) {
    const distance = settings.count === 1 ? (camera.aspect < 1.2 ? 3.35 : 3.05) * WORLD_SCALE : 2.15 * WORLD_SCALE + radius * (camera.aspect < 1.2 ? 1.49 : 1.08);
    const horizontal = distance * Math.cos(elevation);
    controls.target.set(0, (settings.count === 1 ? .74 : .65) * WORLD_SCALE, 0);
    camera.position.copy(controls.target).add(new THREE.Vector3(
      Math.sin(azimuth) * horizontal, Math.sin(elevation) * distance, Math.cos(azimuth) * horizontal
    ));
    controls.minDistance = settings.count === 1 ? 1.85 * WORLD_SCALE : distance * .7;
    controls.maxDistance = Math.max(12 * WORLD_SCALE, distance * 1.6);
    controls.update();
  }

  function setCount(count) {
    while (subjects.length < count) {
      const subject = createSubject(source, makePointMaterial, subjects.length);
      subjects.push(subject);
      scene.add(subject.root);
    }
    active = subjects.slice(0, count);
    radius = layoutSubjects(subjects, count);
    updateShadows(subjects, count);
    for (const subject of active) subject.reset(speed[settings.motion]);
  }

  function configure(change) {
    const countChanged = change.count !== undefined && change.count !== settings.count;
    Object.assign(settings, change);
    if (countChanged) {
      setCount(settings.count);
      setCamera(1.14, settings.count === 1 ? .23 : .59);
    }
    props.visible = settings.landscape;
    syncUI();
  }

  function resize() {
    const { clientWidth: width, clientHeight: height } = canvas;
    if (!width || !height) return;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }

  function render(dt, frameMs, measuredCase) {
    const cpuStart = performance.now();
    if (dt && speed[settings.motion]) {
      for (const subject of active) subject.step(dt, speed[settings.motion]);
    }
    const query = timer.begin();
    const info = pipeline.draw(settings, active);
    timer.end(query, ms => {
      liveGpu = ms;
      measuredCase?.gpu.push(ms);
    });
    const { calls, triangles, points } = renderer.info.render;
    const boneBytes = active.length * active[0].mesh.skeleton.boneTexture.image.data.byteLength;
    const buffers = landscapeBytes + boneBytes + info.targetBytes + (settings.mode !== 'A' ? surfaceBytes : 0)
      + (settings.mode === 'A' || settings.mode === 'D' ? meshBytes : 0);
    return { ...info, calls, triangles, points, gpuBufferEstimateBytes: buffers, frameMs, cpuMs: performance.now() - cpuStart };
  }

  function finishCase(now) {
    const sample = measurement.current;
    if (!sample) return;
    measurement.results.push({
      mode: sample.mode, count: sample.count,
      ...summarize(sample.frames, sample.gpu, Math.round(now - sample.recordFrom))
    });
  }

  function nextCase(now) {
    if (measurement.queue.length) {
      const sample = measurement.queue.shift();
      measurement.current = { ...sample, recordFrom: now + measurement.warmup, frames: [], gpu: [] };
      configure(sample);
      for (const subject of active) subject.reset(1);
      setCamera(1.14, sample.count === 1 ? .23 : .59);
      $('benchmark-status').textContent = `${measurement.results.length + 1} / ${measurement.total} · ${sample.mode} / ${sample.count} 体`;
      return;
    }
    const batch = measurement;
    measurement = null;
    report = { ...batch.metadata, results: batch.results };
    configure(batch.previous);
    $('benchmark-status').textContent = `${batch.results.length} 条件の計測が完了しました。`;
    batch.resolve(report);
  }

  const liveFrames = [];
  let previousSampleFrame;
  function updateMetrics(data, fps) {
    $('fps').textContent = Number.isFinite(fps) ? fps.toFixed(1) : '—';
    $('points').textContent = data.points.toLocaleString();
    $('gpu').textContent = liveGpu === null ? (timer.available ? '計測中' : '未対応') : `${liveGpu.toFixed(2)} ms`;
    $('memory').textContent = `${(data.gpuBufferEstimateBytes / 1048576).toFixed(2)} MiB`;
  }

  function animate(now) {
    if (!lost && !manual) {
      const frameMs = lastTimestamp === null ? 0 : now - lastTimestamp;
      const dt = Math.min(frameMs / 1000, .05);
      lastTimestamp = now;
      let sample = measurement?.current;
      if (previousSampleFrame?.sample === sample && sample && frameMs > 0) {
        sample.frames.push({ ...previousSampleFrame.frame, frameMs });
      }
      timer.poll();
      if (measurement && (!sample || sample.frames.length && now >= sample.recordFrom + measurement.windowMs)) {
        finishCase(now);
        nextCase(now);
        sample = measurement?.current;
      }
      const recording = sample && now >= sample.recordFrom;
      controls.autoRotate = settings.orbit;
      controls.update(dt);
      const frame = render(dt, frameMs, recording ? sample : null);
      previousSampleFrame = recording ? { sample, frame } : null;
      if (frameMs > 0) liveFrames.push(frameMs);
      if (now - lastRefresh > 600) {
        const average = liveFrames.reduce((sum, value) => sum + value, 0) / liveFrames.length;
        updateMetrics(frame, 1000 / average);
        liveFrames.length = 0;
        lastRefresh = now;
      }
    }
    requestAnimationFrame(animate);
  }

  function benchmark({ warmup = 1200, windowMs = 3000, filter = () => true } = {}) {
    if (measurement || lost || manual) throw new Error('描画の準備が完了してから計測してください。');
    const queue = Object.keys(modes).filter(mode => mode !== 'D' || pipeline.canGaussian)
      .flatMap(mode => COUNTS.map(count => ({ mode, count }))).filter(filter);
    if (!queue.length) throw new Error('該当する計測条件がありません。');
    const debug = gl.getExtension('WEBGL_debug_renderer_info');
    const metadata = {
      timestamp: new Date().toISOString(), asset: ASSET, clip: source.clip.name, authoredClip: source.authored.name,
      ua: navigator.userAgent, gpuRenderer: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : null,
      viewport: { cssWidth: canvas.clientWidth, cssHeight: canvas.clientHeight, rendererDpr: renderer.getPixelRatio(), deviceDpr: devicePixelRatio },
      settings: { ...settings, motion: 'run', orbit: true }, warmupMs: warmup, windowMs,
      timerQueryAvailable: timer.available, gaussianAvailable: pipeline.canGaussian
    };
    return new Promise((resolve, reject) => {
      measurement = { queue, total: queue.length, previous: { ...settings }, metadata, warmup, windowMs, results: [], resolve, reject };
      configure({ motion: 'run', orbit: true });
    });
  }

  for (const button of modeButtons) button.addEventListener('click', () => configure({ mode: button.dataset.mode }));
  for (const key of Object.keys(sliders)) $(key).addEventListener('input', event => configure({ [key]: +event.target.value }));
  $('motion').addEventListener('change', event => configure({ motion: event.target.value }));
  $('count').addEventListener('change', event => configure({ count: +event.target.value }));
  $('landscape').addEventListener('change', event => configure({ landscape: event.target.checked }));
  $('orbit').addEventListener('click', () => configure({ orbit: !settings.orbit }));
  $('reset-camera').addEventListener('click', () => setCamera(1.14, settings.count === 1 ? .23 : .59));
  $('capture').addEventListener('click', () => {
    render(0, 0);
    download(canvas.toDataURL('image/png'), `evowild-${settings.mode}-${settings.motion}-${settings.count}.png`);
  });
  $('benchmark').addEventListener('click', () => benchmark().catch(error => { $('benchmark-status').textContent = error.message; }));
  $('export').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' }));
    download(url, 'evowild-pixel-art-benchmark.json');
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    lost = true;
    if (measurement) {
      const batch = measurement;
      measurement = null;
      configure(batch.previous);
      batch.reject(new Error('WebGL コンテキストが失われたため計測を中断しました。'));
    }
    syncUI();
    $('status').textContent = 'WebGL の復旧を待っています…';
    $('status').hidden = false;
  });
  canvas.addEventListener('webglcontextrestored', () => location.reload());

  resize();
  setCount(1);
  setCamera();
  new ResizeObserver(resize).observe(canvas);
  $('status').hidden = true;
  syncUI();
  requestAnimationFrame(animate);

  // Evidence capture only. The visible UI uses the same render and configuration paths.
  if (new URLSearchParams(location.search).has('evidence')) {
    window.pixelArtExperiment = {
      benchmark,
      capture({ mode, motion, count = 1, seconds = 0, azimuth = 1.14, elevation = .23 }) {
        manual = true;
        configure({ mode, motion, count, orbit: false });
        controls.autoRotate = false;
        setCamera(azimuth, elevation);
        for (const subject of active) subject.reset(speed[motion], seconds);
        const data = render(0, 0);
        updateMetrics(data, NaN);
        return { ...data, phase: active[0].contact.cycles % 1, png: canvas.toDataURL('image/png') };
      },
      resume() { manual = false; lastTimestamp = null; },
      inspect() { return { source, subjects: active, settings, pipeline, renderer }; }
    };
  }
}

start().catch(showError);
