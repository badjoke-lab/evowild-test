import {test, expect} from '@playwright/test';
import {classifyFinishCrossings} from '../src/race_finish_2p5d.js';
import {ENTRANTS, makeRaceRecord, validateRaceRecord} from '../src/game_progress_2p5d.js';

test('same-step finish order follows actual crossing time rather than entrant array order', () => {
  const slow={id:1}, fast={id:18};
  const crossings=[
    {runner:slow, fromDistance:1599.1, toDistance:1600.1},
    {runner:fast, fromDistance:1599.8, toDistance:1600.8}
  ];
  expect(classifyFinishCrossings(crossings, {
    stepEndMs:50020, stepMs:20, finishCount:3, finishDistance:1600
  })).toBe(5);
  expect(fast.finishPlace).toBe(4);
  expect(slow.finishPlace).toBe(5);
  expect(fast.finishTime).toBeCloseTo(50004,6);
  expect(slow.finishTime).toBeCloseTo(50018,6);
  expect(fast.finishTime).toBeLessThan(slow.finishTime);
  // Reordering engine storage must not change a distinct crossing order.
  classifyFinishCrossings([...crossings].reverse(), {
    stepEndMs:50020, stepMs:20, finishCount:3, finishDistance:1600
  });
  expect(fast.finishPlace).toBe(4);
  expect(slow.finishPlace).toBe(5);
});

test('archive rejects a unique but chronologically false classification', () => {
  const record=makeRaceRecord({id:'finish-regression-1', finishedAt:Date.now(), selectedRunnerId:4,
    results:ENTRANTS.map((r,i)=>({...r,finishPlace:i+1,finishTime:50000+i*10}))});
  expect(validateRaceRecord(record)).toBe(true);
  record.results[1].timeMs=record.results[0].timeMs-1;
  expect(validateRaceRecord(record)).toBe(false);
});
