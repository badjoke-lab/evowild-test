import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import crypto from 'node:crypto';

function glb(path){
  const bytes=fs.readFileSync(path), size=bytes.readUInt32LE(12);
  const json=JSON.parse(bytes.subarray(20,20+size).toString());
  const binary=bytes.subarray(28+size);
  return {bytes,json,accessor(index){
    const a=json.accessors[index],v=json.bufferViews[a.bufferView];
    const width={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16}[a.type];
    const component={5121:1,5123:2,5125:4,5126:4}[a.componentType];
    const offset=(v.byteOffset||0)+(a.byteOffset||0);
    return binary.subarray(offset,offset+a.count*width*component);
  }};
}

test('S repair preserves canonical geometry bytes and changes only review skin/bind tracks',()=>{
  const source=glb('public/models/evowild-s/focus-rigged-v5.glb');
  const candidate=glb('public/models/evowild-s/review/focus-bind-repair-v1.glb');
  expect(crypto.createHash('sha256').update(source.bytes).digest('hex')).toBe('e879cae6835f405f93787b96dfbcc1858ff540dadaf12988d549d56d922362a2');
  const a=source.json.meshes[0].primitives[0],b=candidate.json.meshes[0].primitives[0];
  for(const name of Object.keys(a.attributes).filter(k=>!['JOINTS_0','WEIGHTS_0'].includes(k))){
    expect(candidate.accessor(b.attributes[name]).equals(source.accessor(a.attributes[name])),name).toBe(true);
  }
  expect(candidate.accessor(b.indices).equals(source.accessor(a.indices))).toBe(true);
  expect(candidate.json.materials).toEqual(source.json.materials);
  expect(candidate.json.skins[0].joints).toEqual(source.json.skins[0].joints);
  for(const animation of source.json.animations){
    for(const channel of animation.channels){
      const sampler=animation.samplers[channel.sampler];
      expect(candidate.accessor(sampler.input).equals(source.accessor(sampler.input))).toBe(true);
      if(source.json.nodes[channel.target.node].name!=='root')
        expect(candidate.accessor(sampler.output).equals(source.accessor(sampler.output))).toBe(true);
    }
  }
  expect(JSON.parse(fs.readFileSync('public/models/evowild-s/manifest.json')).focus_runtime.path).toContain('/focus-rigged-v5.glb');
});

test('S bind candidate loads and moves four weighted feet in rear-quarter view',async({page},testInfo)=>{
  test.setTimeout(60000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/evowild-test/s-run-review.html?rig=bind-v1');
  await page.waitForFunction(()=>window.sRunReview);
  const a=await page.evaluate(()=>window.sRunReview.setPhase(0,'REAR_3_4'));
  const b=await page.evaluate(()=>window.sRunReview.setPhase(.25,'REAR_3_4'));
  const repeated=await page.evaluate(()=>window.sRunReview.setPhase(.25,'REAR_3_4'));
  expect(repeated.feet).toEqual(b.feet); // No one-frame stale parent matrix in telemetry.
  expect(a.asset).toBe('review/focus-bind-repair-v1.glb');
  expect(a.vertices).toBe(38813);expect(a.bones).toBe(19);
  for(let i=0;i<4;i++){
    expect(a.feet[i].weightBone).toBe(a.feet[i].name);
    expect(a.feet[i].maxFootInfluence).toBeGreaterThan(.3);
    // Diagnostic groups must be on the legs, not the head (>1.5m in original).
    expect(Math.max(a.feet[i].y,b.feet[i].y)).toBeLessThan(.7);
    const movement=Math.hypot(a.feet[i].y-b.feet[i].y,(a.feet[i].z-a.distance)-(b.feet[i].z-b.distance));
    expect(movement).toBeGreaterThan(.02);
  }
  await page.screenshot({path:testInfo.outputPath('rear-quarter.png')});
  expect(errors).toEqual([]);
  // Contact/slip and identity require separate visual review. No KEEP assertion.
});
