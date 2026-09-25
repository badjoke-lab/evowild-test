import * as THREE from 'three';
import type { Ctx, IKart, System } from '../types';

type Runner = {
  kart: IKart;
  sprite: THREE.Sprite;
  texture: THREE.Texture;
};

const FRAME_COLS = 3;
const FRAME_ROWS = 2;
const FRAME_COUNT = 6;
const BASE_HEIGHT = 2.05;

export class EvoWildSpriteRunners implements System {
  private runners: Runner[] = [];
  private sourceAspect = 1.55;
  private loaded = false;

  init(ctx: Ctx) {
    const spriteUrl = new URL('s-run-sheet.webp', window.location.href).toString();
    (window as any).__evowildSLoadUrl = spriteUrl;
    (window as any).__evowildSReady = false;
    (window as any).__evowildSError = null;

    new THREE.TextureLoader().load(
      spriteUrl,
      (texture) => {
        texture.colorSpace = THREE.SRGBColorSpace;
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(1 / FRAME_COLS, 1 / FRAME_ROWS);

        const image = texture.image as { width?: number; height?: number };
        if (image?.width && image?.height) {
          this.sourceAspect = (image.width / FRAME_COLS) / (image.height / FRAME_ROWS);
        }

        for (const kart of ctx.race.karts) {
          const originalVisual = kart.object.children[0];
          if (originalVisual) originalVisual.visible = false;

          const tex = texture.clone();
          tex.needsUpdate = true;
          tex.wrapS = THREE.RepeatWrapping;
          tex.wrapT = THREE.RepeatWrapping;
          tex.repeat.set(1 / FRAME_COLS, 1 / FRAME_ROWS);

          const material = new THREE.SpriteMaterial({
            map: tex,
            color: 0xffffff,
            transparent: true,
            alphaTest: 0.035,
            depthTest: true,
            depthWrite: false,
            fog: true,
          });

          const sprite = new THREE.Sprite(material);
          sprite.name = 'evowild-s-runner';
          const height = kart.isPlayer ? BASE_HEIGHT * 1.08 : BASE_HEIGHT;
          sprite.scale.set(height * this.sourceAspect, height, 1);
          sprite.renderOrder = 10;
          ctx.scene.add(sprite);

          this.runners.push({ kart, sprite, texture: tex });
        }

        texture.dispose();
        this.loaded = true;
        (window as any).__evowildSReady = true;
      },
      undefined,
      (err) => {
        const message = err instanceof Error ? err.message : String(err);
        (window as any).__evowildSError = message;
        console.error('[evowild] S run sheet failed to load', spriteUrl, err);
      },
    );
  }

  update(ctx: Ctx) {
    if (!this.loaded) return;

    for (const runner of this.runners) {
      const { kart, sprite, texture } = runner;
      const speed = Math.hypot(kart.velocity.x, kart.velocity.z);
      const cadence = THREE.MathUtils.clamp(5.2 + speed * 0.32, 5.2, 14.0);
      const frame = speed < 0.8
        ? 0
        : Math.floor(ctx.time * cadence + kart.id * 0.73) % FRAME_COUNT;

      const col = frame % FRAME_COLS;
      const row = Math.floor(frame / FRAME_COLS);
      texture.offset.set(col / FRAME_COLS, row === 0 ? 0.5 : 0.0);

      sprite.position.copy(kart.position);
      sprite.position.y += 1.12;

      const pace = THREE.MathUtils.clamp(speed / 30, 0, 1);
      const height = (kart.isPlayer ? BASE_HEIGHT * 1.08 : BASE_HEIGHT) * (1 + pace * 0.035);
      sprite.scale.set(height * this.sourceAspect, height, 1);
      sprite.visible = true;
    }
  }

  dispose() {
    for (const r of this.runners) {
      r.sprite.parent?.remove(r.sprite);
      r.sprite.material.dispose();
      r.texture.dispose();
    }
    this.runners = [];
    this.loaded = false;
  }
}
