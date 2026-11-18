import {ENTRANTS, makeRaceRecord} from '../../src/game_progress_2p5d.js';
// Isolated UI fixture only. Never included by the game or presented as a real race.
export const historyLayoutFixture=()=>({schemaVersion:1,selectedRunnerId:4,history:[makeRaceRecord({
  id:'ui-layout-fixture-not-a-real-race',finishedAt:Date.UTC(2026,9,25,0),selectedRunnerId:4,
  results:ENTRANTS.map((r,i)=>({...r,name:r.id===4?'表示検証サンプル':r.name,finishPlace:i+1,finishTime:45000+i*100})),
  agentDecisions:[
    {at:45000,command:'PUSH',result:'PARTIAL',reason:'疲労により加速が制限されました。周囲の個体との間隔を保ちながら、残りの直線で加速を試みました。'},
    {at:10000,command:'SHIFT_LINE',result:'FAILED',reason:'LongUnbrokenReason'.repeat(8)},
    {at:1000,command:'CONSERVE',result:'SUCCESS',reason:'Conserve stamina for the final straight while maintaining a safe gap from nearby runners.'}
  ]
})]});
