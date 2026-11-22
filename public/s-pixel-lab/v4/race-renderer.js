import {RaceRenderer as BaseRace} from '../v3/race-renderer.js';
import {RaceSurface} from './surface.js';
import {RaceFloor} from './track.js';

export class RaceRenderer extends BaseRace {
 static Surface = RaceSurface;
 static Floor = RaceFloor;

 beginFrame(s,ext,w,h) {
  if (s.number === 1 && !s.course && s.method !== 'exact' && s.method !== 'stack') {
   const samples=Math.min(s.heroAA ?? 4,this.maxCoverage);
   if(samples<2)return;
   if(this.coverage.samples!==samples){this.coverage.release();this.coverage.samples=samples;}
   this.coverage.begin(w,h);
   return;
  }
  super.beginFrame(s,ext,w,h);
 }
}
