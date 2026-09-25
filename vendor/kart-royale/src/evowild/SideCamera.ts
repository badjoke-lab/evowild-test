import * as THREE from 'three';
import type { Ctx, System } from '../types';

const WORLD_UP = new THREE.Vector3(0, 1, 0);
const right = new THREE.Vector3();
const desired = new THREE.Vector3();
const target = new THREE.Vector3();
const look = new THREE.Vector3();

export class EvoWildSideCamera implements System {
  private ready = false;
  private shakeAmp = 0;
  private shakeT = 0;

  init(ctx: Ctx) {
    ctx.camera.fov = 52;
    ctx.camera.near = 0.2;
    ctx.camera.far = 3000;
    ctx.camera.updateProjectionMatrix();
    this.snap(ctx);
  }

  addShake(amount: number, seconds = 0.3) {
    this.shakeAmp = Math.max(this.shakeAmp, amount);
    this.shakeT = Math.max(this.shakeT, seconds);
  }

  private compose(ctx: Ctx) {
    const p = ctx.race.player;
    right.set(p.forward.z, 0, -p.forward.x);
    if (right.lengthSq() < 0.001) right.set(1, 0, 0);
    right.normalize();

    desired.copy(p.position)
      .addScaledVector(right, 6.4)
      .addScaledVector(p.forward, -2.0)
      .addScaledVector(WORLD_UP, 2.65);

    target.copy(p.position)
      .addScaledVector(p.forward, 0.9)
      .addScaledVector(WORLD_UP, 1.02);
  }

  private snap(ctx: Ctx) {
    this.compose(ctx);
    ctx.camera.position.copy(desired);
    ctx.camera.lookAt(target);
    this.ready = true;
  }

  lateUpdate(ctx: Ctx, dt: number) {
    if (!ctx.race.player) return;
    this.compose(ctx);

    if (!this.ready) {
      this.snap(ctx);
      return;
    }

    const posK = 1 - Math.exp(-dt * 6.8);
    ctx.camera.position.lerp(desired, posK);

    look.copy(target);

    if (this.shakeT > 0 && dt > 0) {
      this.shakeT = Math.max(0, this.shakeT - dt);
      const fade = Math.min(1, this.shakeT / 0.18);
      const a = this.shakeAmp * fade * 0.08;
      ctx.camera.position.x += Math.sin(ctx.time * 47) * a;
      ctx.camera.position.y += Math.cos(ctx.time * 53) * a * 0.55;
      if (this.shakeT <= 0) this.shakeAmp = 0;
    }

    ctx.camera.lookAt(look);

    const speed = Math.hypot(ctx.race.player.velocity.x, ctx.race.player.velocity.z);
    const targetFov = 52 + THREE.MathUtils.clamp(speed / 30, 0, 1) * 3.0 + ctx.fovPunch * 0.20;
    ctx.camera.fov += (targetFov - ctx.camera.fov) * (1 - Math.exp(-dt * 5.5));
    ctx.camera.updateProjectionMatrix();
  }
}
