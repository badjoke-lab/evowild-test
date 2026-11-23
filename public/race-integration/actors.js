// The game owns the framebuffer, camera, course and racers. Only S geometry is
// submitted here. Import the frozen lab implementations and their original data.
import { common, program } from '../s-pixel-lab/renderer.js';
import { Surface } from '../s-pixel-lab/v4.1/surface.js';
import { RaceRenderer } from '../s-pixel-lab/v4.1/race-renderer.js';
import { Impostors } from '../s-pixel-lab/v2/impostors.js';

const trackHeight = 0.034; // The game's road surface is y=0.03.
export const actorScale = obj => obj.scale.x * 4.65 / 700;
const perspective = `
uniform mat4 courseVP;
uniform float modelUnit;
uniform vec3 uRight;
vec4 project(vec3 world){
  return courseVP * vec4(world * modelUnit + vec3(0., ${trackHeight}, 0.), 1.);
}`;

// Preserve the colour, dither, UV/depth reconstruction and original programs'
// vertex inputs. Replace the lab's orthographic projection at the shared seam.
// The fractional part of the foot-mask attribute carries each runner's own
// sub-pose travel; the uniform drift is the distance between sampled poses.
function gameProgram(gl, pass, mask, far = false) {
  const sources = new Map(gl.getAttachedShaders(pass.p).map(shader =>
    [gl.getShaderParameter(shader, gl.SHADER_TYPE), gl.getShaderSource(shader)]));
  let vs = sources.get(gl.VERTEX_SHADER);
  if (!vs.includes(common) || !vs.includes('p.x+=drift*')) throw Error('v4.1 頂点入力が一致しません');
  vs = vs.replace(common, perspective).replace('p.x+=drift*', 'p.x+=drift*fract('+mask+')*');
  if (far) vs = vs.replace('int(tile.w+.5)', 'int(tile.w)');
  const next = program(gl, vs, sources.get(gl.FRAGMENT_SHADER));
  gl.deleteProgram(pass.p);
  return next;
}

async function json(relative) {
  const response = await fetch(new URL('../s-pixel-lab/' + relative, import.meta.url));
  if (!response.ok) throw Error(relative + ' HTTP ' + response.status);
  return response.json();
}

export async function loadActors(THREE, renderer, racers) {
  const [meta, atlas] = await Promise.all([json('v3/assets/manifest.json'), json('v2/assets/angles/index.json')]);
  const gl = renderer.getContext();
  const surface = new Surface(gl, meta);
  const sprites = new Impostors(gl, atlas);
  try {
    await surface.load();
    for (const key of ['pass', 'solid']) {
      surface[key] = gameProgram(gl, surface[key], 'instanceInfo.x');
      surface.configure(surface[key]);
    }
    sprites.far.pass = gameProgram(gl, sprites.far.pass, 'tile.w', true);
  } finally {
    renderer.resetState();
  }

  const unit = actorScale(racers[0].obj);
  const feet = meta.poses.map(p => ['nearF','farF','nearH','farH'].reduce(
    (bits, side, i) => bits | (Number(p.feet[side].contact) << i), 0));
  const vp = new THREE.Matrix4(), frustum = new THREE.Frustum(), bounds = new THREE.Sphere();
  const point = new THREE.Vector3(), requestedAt = new Map(), failures = new Set();
  const runners = racers.filter(r => r.morph === 'S');
  let serial = 0;
  function bankFor(index) {
    requestedAt.set(index, serial);
    if (!sprites.banks.has(index) && !failures.has(index)) {
      sprites.load(index).catch(() => failures.add(index)).finally(() => renderer.resetState());
    }
    return sprites.banks.get(index)?.ready;
  }
  return function draw(camera, travel, inspect = false) {
    serial++;
    const batches = new Map(), pages = new Map();
    const mix = { fine:0, race:0, mid:0, transition:0, sprite:0, outside:0 };
    const details = [];
    vp.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    frustum.setFromProjectionMatrix(vp);
    const focal = gl.drawingBufferHeight * camera.projectionMatrix.elements[5] / 2;
    for (const r of runners) {
      const root = r.obj.position;
      point.set(root.x, trackHeight + 214*unit, root.z);
      bounds.center.copy(point);
      bounds.radius = 460*unit;
      if (!frustum.intersectsSphere(bounds)) { mix.outside++; continue; }
      const dx=camera.position.x-point.x, dy=camera.position.y-point.y, dz=camera.position.z-point.z;
      const depth = -point.applyMatrix4(camera.matrixWorldInverse).z;
      const span = 700*unit*focal / Math.max(camera.near, depth);
      const theta = Math.PI - r.obj.rotation.y; // Canonical nose is -X, game nose is +X.
      const yaw = theta + Math.atan2(dx,dz);
      const elev = Math.atan2(dy,Math.hypot(dx,dz));
      const bank = Math.min(9, Math.max(0, Math.round(elev*18/Math.PI)));
      const tick = travel.get(r.id)/(unit*meta.stride)*meta.frames + (r.id-1)*7;
      const step = Math.floor(tick);
      const pose = r.speed > 0 ? 1+step%meta.frames : 0;
      const mask = feet[pose] + (pose ? Math.min(.99999,tick-step) : 0);
      const x=root.x/unit, z=root.z/unit;
      let card = RaceRenderer.prototype.effectiveCoverage(Math.min(1, Math.max(0, (113-span)/10)));
      if (card && !bankFor(bank)) card=0; // Draw the full surface while the exact bank streams.
      const level = span>=245?'fine':span>=148?'race':'mid';
      const lod = card===1?'sprite':card>0?'transition':level;
      mix[lod]++;
      if (inspect) details.push({id:r.id, pose, feet:feet[pose], fraction:mask-feet[pose], span, lod,
        direction:[-Math.cos(theta),-Math.sin(theta)], base:[root.x,trackHeight,root.z],
        screen: new THREE.Vector3(root.x,trackHeight+214*unit,root.z).project(camera).toArray()});
      if (card<1) {
        const key = pose+'/'+level;
        if (!batches.has(key)) batches.set(key,{pose,level,direction:null,places:[]});
        batches.get(key).places.push(x,z,Math.cos(theta),Math.sin(theta),mask,1-card);
      }
      if (card>0) {
        const n=atlas.directions, k=(Math.round(yaw*n/(2*Math.PI))%n+n)%n;
        const [page,u,v,w,h,tx,ty]=atlas.angles[bank].rects[pose*n+k];
        const key=bank+'/'+page;
        if (!pages.has(key)) pages.set(key,{bank,page,instances:[]});
        pages.get(key).instances.push(x,z,theta,k*2*Math.PI/n,u,v,w,h,tx,ty,card,mask);
      }
    }
    const use=pass=>{
      gl.useProgram(pass.p);
      gl.uniformMatrix4fv(pass.u.courseVP,false,vp.elements);
      gl.uniform1f(pass.u.modelUnit,unit);
      if (pass.u.uRight) gl.uniform3f(pass.u.uRight,1,0,0);
    };
    // Keep the actual course and other morphs' depth. Never clear between passes.
    try {
      gl.enable(gl.DEPTH_TEST); gl.depthMask(true); gl.depthFunc(gl.LEQUAL);
      gl.enable(gl.CULL_FACE); gl.cullFace(gl.BACK); gl.frontFace(gl.CCW); gl.disable(gl.BLEND);
      const drift = meta.stride/meta.frames;
      surface.draw(batches,use,drift);
      gl.enable(gl.BLEND); gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);
      for (const {bank,page,instances} of pages.values()) {
        const a=atlas.angles[bank].elev*Math.PI/180;
        sprites.far.draw(instances,sprites.banks.get(bank).pages[page],[Math.sin(a),Math.cos(a)],drift,sprites.buffer,use);
      }
      for (const [bank,at] of requestedAt) {
        if (serial-at>120 && sprites.banks.get(bank)?.ready) {
          sprites.release(bank); requestedAt.delete(bank);
        }
      }
    } finally {
      renderer.resetState();
    }
    return {mix,details, atlasPending:[...sprites.banks.values()].some(b=>!b.ready), atlasErrors:[...failures]};
  };
}
