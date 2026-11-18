// Each entry describes artwork for a signed camera-relative heading.
// The angle quantizer uses the length of this table (e.g. 16 with new rows).
const front = {name:"front", row:0};
const frontRight = {name:"front-right", row:1};
export const RIGHT_VIEW = {name:"right", row:2, frames:6};
const rearRight = {name:"rear-right", row:3};
export const RUN_VIEWS = [
  front, frontRight, RIGHT_VIEW, rearRight, {name:"rear", row:4},
  {...rearRight, name:"rear-left", mirror:true},
  {...RIGHT_VIEW, name:"left", mirror:true},
  {...frontRight, name:"front-left", mirror:true}
];
export const CELL_WIDTH = 208;
export const CELL_HEIGHT = 144;
const FOOT_Y = 136;
const atlasRows = Math.max(...RUN_VIEWS.map(view => view.row)) + 1;
const atlasByMorph = new Map();

export async function loadRunAtlas(morph, base) {
  const image = new Image();
  image.src = base + "concept/stadium/" + morph.toLowerCase() + "-run.webp";
  await image.decode();
  if (image.width !== CELL_WIDTH * 12 || image.height !== CELL_HEIGHT * atlasRows) {
    throw new Error("Unexpected run atlas dimensions for " + morph);
  }
  atlasByMorph.set(morph, image);
}

export function runFrame(morph, view, phase) {
  const count = morph === "P" ? 12 : view.frames || 12;
  return Math.floor(phase * count);
}

export function drawRunSprite(ctx, runner, view, phase, x, y, height) {
  const atlas = atlasByMorph.get(runner.morph);
  if (!atlas) return;
  const width = height * CELL_WIDTH / CELL_HEIGHT;
  ctx.save();
  ctx.translate(x, y);
  if (view.mirror) ctx.scale(-1, 1);
  ctx.drawImage(atlas, runFrame(runner.morph, view, phase) * CELL_WIDTH, view.row * CELL_HEIGHT,
    CELL_WIDTH, CELL_HEIGHT, -width/2, -height * FOOT_Y / CELL_HEIGHT, width, height);
  ctx.restore();
}
