import * as THREE from "three";
import "./visual_shader_lab.css";

const canvas = document.querySelector("#shader-lab-canvas");
const fpsEl = document.querySelector("#fps");
const modeEl = document.querySelector("#mode");
const toggleEl = document.querySelector("#toggle");

const isMobile = matchMedia("(pointer: coarse)").matches || innerWidth < 800;
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: !isMobile,
  powerPreference: "default",
  precision: "mediump"
});
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.setPixelRatio(Math.min(devicePixelRatio, isMobile ? 1.35 : 1.5));

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xa7c6cf);
scene.fog = new THREE.FogExp2(0xa7c6cf, 0.0095);

const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 260);
camera.position.set(20, 7, 24);

scene.add(new THREE.HemisphereLight(0xe6f2ff, 0x314133, 1.25));
const sun = new THREE.DirectionalLight(0xffedcf, 1.7);
sun.position.set(34, 48, 20);
scene.add(sun);

const groundGeometry = new THREE.PlaneGeometry(220, 180, 96, 80);
groundGeometry.rotateX(-Math.PI / 2);

const shaderUniforms = {
  uTime: { value: 0 },
  uEnabled: { value: 1 }
};

const groundShader = new THREE.ShaderMaterial({
  uniforms: shaderUniforms,
  vertexShader: `
    uniform float uTime;
    uniform float uEnabled;
    varying vec3 vWorld;
    varying float vMacro;
    varying float vRelief;

    void main() {
      vec3 p = position;
      float waveA = sin(p.x * 0.075) * cos(p.z * 0.065);
      float waveB = sin((p.x + p.z) * 0.035 + 1.4);
      float relief = (waveA * 0.08 + waveB * 0.045) * uEnabled;
      p.y += relief;

      vec4 world = modelMatrix * vec4(p, 1.0);
      vWorld = world.xyz;
      vMacro = waveA * 0.55 + waveB * 0.45;
      vRelief = relief;

      gl_Position = projectionMatrix * viewMatrix * world;
    }
  `,
  fragmentShader: `
    uniform float uEnabled;
    varying vec3 vWorld;
    varying float vMacro;
    varying float vRelief;

    float hash21(vec2 p) {
      p = fract(p * vec2(123.34, 456.21));
      p += dot(p, p + 45.32);
      return fract(p.x * p.y);
    }

    float valueNoise(vec2 p) {
      vec2 i = floor(p);
      vec2 f = fract(p);
      vec2 u = f * f * (3.0 - 2.0 * f);
      float a = hash21(i);
      float b = hash21(i + vec2(1.0, 0.0));
      float c = hash21(i + vec2(0.0, 1.0));
      float d = hash21(i + vec2(1.0, 1.0));
      return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
    }

    void main() {
      vec3 flatColor = vec3(0.36, 0.47, 0.31);

      float nLarge = valueNoise(vWorld.xz * 0.055);
      float nMedium = valueNoise(vWorld.xz * 0.16);
      float broadA = 0.5 + 0.5 * sin(vWorld.x * 0.034 + sin(vWorld.z * 0.026) * 1.2);
      float blendField = clamp(
        nLarge * 0.46 + nMedium * 0.20 + broadA * 0.22 + 0.12 + vMacro * 0.08,
        0.0,
        1.0
      );

      vec3 darkGrass = vec3(0.22, 0.32, 0.20);
      vec3 midGrass = vec3(0.35, 0.46, 0.29);
      vec3 lightGrass = vec3(0.46, 0.54, 0.34);

      vec3 procedural = mix(darkGrass, midGrass, smoothstep(0.08, 0.72, blendField));
      procedural = mix(procedural, lightGrass, smoothstep(0.66, 0.98, blendField) * 0.30);
      procedural += (nMedium - 0.5) * 0.018;
      procedural += vRelief * 0.22;

      vec3 color = mix(flatColor, procedural, uEnabled);

      float distanceFromCenter = length(vWorld.xz);
      float horizonMix = smoothstep(30.0, 115.0, distanceFromCenter);
      vec3 hazeGrass = vec3(0.43, 0.51, 0.38);
      color = mix(color, hazeGrass, horizonMix * 0.58);

      gl_FragColor = vec4(color, 1.0);
    }
  `
});

const ground = new THREE.Mesh(groundGeometry, groundShader);
ground.position.y = -0.08;
scene.add(ground);

const curve = new THREE.CatmullRomCurve3(
  [
    [-37, -8], [-28, -20], [-5, -25], [20, -20], [38, -8],
    [39, 10], [24, 23], [0, 27], [-24, 21], [-39, 8]
  ].map(([x, z]) => new THREE.Vector3(x, 0, z)),
  true,
  "centripetal",
  0.45
);

function offsetPoint(t, offset, y = 0.13) {
  const p = curve.getPointAt(t);
  const tangent = curve.getTangentAt(t).normalize();
  const side = new THREE.Vector3(-tangent.z, 0, tangent.x);
  return p.clone().addScaledVector(side, offset).setY(y);
}

function makeTrack() {
  const samples = 220;
  const halfWidth = 6.2;
  const vertices = [];
  const indices = [];

  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    for (const offset of [-halfWidth, halfWidth]) {
      const q = offsetPoint(t, offset, 0.09);
      vertices.push(q.x, q.y, q.z);
    }
  }

  for (let i = 0; i < samples; i++) {
    const a = i * 2;
    indices.push(a, a + 2, a + 1, a + 1, a + 2, a + 3);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();

  const material = new THREE.MeshStandardMaterial({
    color: 0xc09262,
    roughness: 0.98,
    side: THREE.DoubleSide
  });
  const track = new THREE.Mesh(geometry, material);
  scene.add(track);

  const edgeMaterial = new THREE.LineBasicMaterial({
    color: 0xe8ddc5,
    transparent: true,
    opacity: 0.9
  });

  for (const offset of [-halfWidth, halfWidth]) {
    const points = [];
    for (let i = 0; i <= samples; i++) {
      points.push(offsetPoint(i / samples, offset, 0.14));
    }
    scene.add(
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(points),
        edgeMaterial
      )
    );
  }
}
makeTrack();

const markerMaterial = new THREE.MeshStandardMaterial({
  color: 0x647668,
  roughness: 1,
  flatShading: true
});

for (let i = 0; i < 34; i++) {
  const a = (i / 34) * Math.PI * 2;
  const radius = 54 + (i % 5) * 2.6;
  const h = 1.8 + (i % 4) * 0.7;
  const marker = new THREE.Mesh(
    new THREE.ConeGeometry(0.8 + (i % 3) * 0.15, h, 6),
    markerMaterial
  );
  marker.position.set(Math.cos(a) * radius, h * 0.5, Math.sin(a) * radius * 0.72);
  scene.add(marker);
}

let shaderEnabled = true;
toggleEl.addEventListener("click", () => {
  shaderEnabled = !shaderEnabled;
  shaderUniforms.uEnabled.value = shaderEnabled ? 1 : 0;
  modeEl.textContent = shaderEnabled ? "SHADER ON" : "SHADER OFF";
});

let last = performance.now();
let fpsAccum = 0;
let fpsFrames = 0;
let fpsWindowStart = last;

function resize() {
  const width = innerWidth;
  const height = innerHeight;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

function animate(now) {
  requestAnimationFrame(animate);
  const dt = Math.min((now - last) / 1000, 0.05);
  last = now;

  shaderUniforms.uTime.value += dt;

  const t = (now * 0.000018) % 1;
  const focus = curve.getPointAt(t);
  const tangent = curve.getTangentAt(t).normalize();
  const side = new THREE.Vector3(-tangent.z, 0, tangent.x);

  camera.position.copy(focus)
    .addScaledVector(side, 12.5)
    .add(new THREE.Vector3(0, 5.6, 0))
    .addScaledVector(tangent, -8.5);
  camera.lookAt(
    focus.clone()
      .addScaledVector(tangent, 10)
      .add(new THREE.Vector3(0, 0.55, 0))
  );

  renderer.render(scene, camera);

  const instFps = dt > 0 ? 1 / dt : 0;
  fpsAccum += instFps;
  fpsFrames += 1;
  if (now - fpsWindowStart > 700) {
    fpsEl.textContent = `FPS ${Math.round(fpsAccum / Math.max(1, fpsFrames))}`;
    fpsAccum = 0;
    fpsFrames = 0;
    fpsWindowStart = now;
  }
}
requestAnimationFrame(animate);
