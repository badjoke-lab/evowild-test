// All versions share the same moving cameras. A phase from 0 to 1 covers
// 3 seconds on the first bend and crosses all 24 gallop poses.
export const RACES = Object.freeze({near1:1, near10:10, mixed50:50, mixed100:100, overview100:100});

function courseHeading(distance) {
  const bendLength = Math.PI * 1750;
  const length = 7600 + 2 * bendLength;
  const laps = Math.floor(distance / length);
  const at = distance - laps * length;
  const firstBend = Math.max(0, Math.min(bendLength, at - 3800));
  const secondBend = Math.max(0, Math.min(bendLength, at - 7600 - bendLength));
  return laps * 2 * Math.PI + (firstBend + secondBend) / 1750;
}

export function raceState(key, phase, width, height, meta) {
  if (!(key in RACES)) throw new RangeError(`Unknown race ${key}`);
  const number = RACES[key];
  const time = 1.10 + 3 * phase;
  const wave = Math.sin(2 * Math.PI * phase);
  // Track the tangent of the bend, with a transverse orbit on top of it.
  const distance = time * meta.stride / meta.period + 3690;
  const rows = Math.ceil(number / Math.ceil(Math.sqrt(number)));
  const tangent = courseHeading(distance - (rows-1)*380);
  const yaw = (-tangent * 180 / Math.PI) + (key==='near10' ? 80 : key==='mixed50' && width>600 ? -73 : key.startsWith('mixed') ? -86 : -22) + 10 * wave;
  const tilt = 13 + 3 * Math.sin(2 * Math.PI * phase + 0.35);
  // Normalize camera distance in physical canvas pixels. The renderer adds a
  // final fit around each runner for unusual angles and narrow screens.
  const cols = Math.ceil(Math.sqrt(number));
  const extent = number===1 ? Math.max(293,420*height/width)*1.36 :
    Math.max(445,(cols*810*.53+rows*445*.24)*height/width,rows*230+210,rows*475);
  const span = key==='near1' ? Math.min(335, width*.68) + 25*wave : key==='near10' ? 197+10*wave : 124+5*wave;
  const magnification = key==='overview100' ? 0.96 + .04 * wave : span * 2 * extent / (700 * height);
  return {number, time, yaw, tilt, magnification, zoom:1, samples:24, layers:128,
    idle:false, course:true, mask:false, spin:true, playing:true, method:'lod'};
}
