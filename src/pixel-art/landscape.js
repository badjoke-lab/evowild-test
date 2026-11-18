import * as THREE from 'three';
import { seededRandom, WORLD_SCALE } from './subjects.js';

export const SKY = new THREE.Color('#a8b59c');
export const FOG = .025 / WORLD_SCALE;
export const SUN = new THREE.Vector3(-3, 6, 4).normalize();

export function makeLandscape(scene) {
  scene.background = SKY;
  scene.fog = new THREE.FogExp2(SKY, FOG);
  scene.add(new THREE.HemisphereLight('#fff0c5', '#4c6860', 2.05));
  const sun = new THREE.DirectionalLight('#ffe1b5', 2.1);
  sun.position.copy(SUN);
  scene.add(sun);

  const random = seededRandom(29587);
  const environment = new THREE.Group();
  environment.scale.setScalar(WORLD_SCALE);
  scene.add(environment);
  const ground = new THREE.PlaneGeometry(135, 135, 90, 90).rotateX(-Math.PI / 2).toNonIndexed();
  const positions = ground.attributes.position;
  const tint = new THREE.Color();
  const colors = new Float32Array(positions.count * 3);
  const soil = new THREE.Color('#5c7052');
  for (let i = 0; i < positions.count; i += 3) {
    const x = positions.getX(i);
    const z = positions.getZ(i);
    const patch = Math.sin(x * .39 + z * .22) * Math.cos(z * .34);
    tint.copy(soil).multiplyScalar(.93 + patch * .10 + random() * .10);
    for (let j = 0; j < 3; j++) tint.toArray(colors, (i + j) * 3);
  }
  ground.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  environment.add(new THREE.Mesh(ground, new THREE.MeshLambertMaterial({ vertexColors: true })));

  const props = new THREE.Group();
  environment.add(props);
  const dummy = new THREE.Object3D();
  const set = (mesh, i, x, y, z, sx, sy, sz, yaw, color) => {
    dummy.position.set(x, y, z);
    dummy.scale.set(sx, sy, sz);
    dummy.rotation.set(0, yaw, 0);
    dummy.updateMatrix();
    mesh.setMatrixAt(i, dummy.matrix);
    mesh.setColorAt(i, tint.set(color));
  };
  const material = new THREE.MeshLambertMaterial({ flatShading: true });
  const trunks = new THREE.InstancedMesh(new THREE.CylinderGeometry(.65, 1, 1, 5), material, 46);
  const leaves = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 1, 6), material, 46 * 3);
  const rocks = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 0), material, 66);
  const grass = new THREE.InstancedMesh(grassGeometry(), new THREE.MeshLambertMaterial({ side: THREE.DoubleSide }), 690);
  for (let i = 0; i < trunks.count; i++) {
    const angle = i * 2.39996;
    const radius = 7.7 + random() * 33;
    const x = Math.cos(angle) * radius;
    const z = Math.sin(angle) * radius;
    const h = 1.4 + random() * 3.4;
    set(trunks, i, x, h * .27, z, .12, h * .54, .12, angle, '#483f33');
    for (let j = 0; j < 3; j++) {
      const r = h * (.31 - j * .057);
      set(leaves, i * 3 + j, x, h * (.53 + j * .20), z, r, h * .56, r, angle + j * .34,
        ['#3b563d', '#526849', '#657955'][j]);
    }
  }
  for (let i = 0; i < rocks.count; i++) {
    const angle = i * 2.39996 + .48;
    const radius = 2.05 + random() * 29;
    const size = .15 + random() ** 2 * .67;
    set(rocks, i, Math.cos(angle) * radius, size * .21, Math.sin(angle) * radius,
      size * 1.4, size * .73, size, angle, i % 3 === 0 ? '#869087' : '#65736b');
  }
  for (let i = 0; i < grass.count; i++) {
    const angle = i * 2.39996;
    const radius = i < 150 ? 1.18 + random() * 5.6 : 6.7 + random() * 30;
    const size = .08 + random() ** 2 * .27;
    set(grass, i, Math.cos(angle) * radius, .01, Math.sin(angle) * radius,
      size, size, size, random() * 6.28, ['#718052', '#8b8e55', '#476141', '#aaa369'][i % 4]);
  }
  props.add(trunks, leaves, rocks, grass);
  return props;
}

function grassGeometry() {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute([
    -.13, 0, 0, .13, 0, 0, -.48, .72, .05,
    -.10, 0, 0, .12, 0, 0, .33, 1.1, -.12,
    0, 0, -.12, 0, 0, .14, .23, .88, .48,
    .17, 0, .15, -.08, 0, -.08, -.29, .56, -.56
  ], 3));
  geometry.computeVertexNormals();
  return geometry;
}

export function makeContactShadows(scene, max) {
  const shadows = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2),
    new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      vertexShader: `varying vec2 vUV;
        void main() { vUV = uv; gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4(position, 1.0); }`,
      fragmentShader: `varying vec2 vUV;
        void main() {
          float distanceToCenter = length(vUV * 2.0 - 1.0);
          gl_FragColor = vec4(0.015, 0.03, 0.023, 0.35 * (1.0 - smoothstep(0.2, 1.0, distanceToCenter)));
          #include <colorspace_fragment>
        }`
    }), max);
  shadows.frustumCulled = false;
  scene.add(shadows);
  const matrix = new THREE.Matrix4();
  return (subjects, count) => {
    shadows.count = count;
    for (let i = 0; i < count; i++) {
      const { x, z } = subjects[i].placement;
      matrix.makeScale(.89 * WORLD_SCALE, 1, 1.95 * WORLD_SCALE).setPosition(x, .012, z);
      shadows.setMatrixAt(i, matrix);
    }
    shadows.instanceMatrix.needsUpdate = true;
  };
}
