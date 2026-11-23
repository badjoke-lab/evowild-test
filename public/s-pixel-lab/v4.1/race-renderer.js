import {RaceRenderer as V4} from '../v4/race-renderer.js';
import {Surface} from './surface.js';
export class RaceRenderer extends V4 {
 static Surface = Surface;
 effectiveCoverage(card){
  // Both passes use the same 4x4 Bayer ranks (0.5...15.5)/16.
  // Keep a float rounding margin at the comparisons.
  return card>15.5/16+1e-6?1:card<.5/16-1e-6?0:card;
 }
}
