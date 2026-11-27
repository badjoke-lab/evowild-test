import fs from 'node:fs/promises';
import path from 'node:path';
const [site,folder]=process.argv.slice(2);
await fs.mkdir(folder,{recursive:true});
await fs.mkdir(path.join(site,'ridge-surface'),{recursive:true});
await fs.copyFile('public/ridge-surface/candidate.js',path.join(site,'ridge-surface/candidate.js'));
for(const mode of ['group','color','both'])for(const probe of [false,true]){
  let source=await fs.readFile(path.join(site,'race-integration',probe?'probe-actors.js':'actors.js'),'utf8');
  source="import {prepareCandidate} from '../ridge-surface/candidate.js';\n"+source;
  source=source.replace('function gameProgram(gl, pass, mask, far = false)','function gameProgram(gl, pass, mask, far = false, candidate)');
  source=source.replace('  const next = program(gl, vs, fs);','  if(candidate&&!far)[vs,fs]=candidate.shader(vs,fs);\n  const next = program(gl, vs, fs);');
  source=source.replace('  try {\n    await surface.load();','  let candidate;\n  try {\n    await surface.load();');
  source=source.replace('surface.facing=new PerspectiveFaces(gl,surface,meta);',`surface.facing=new PerspectiveFaces(gl,surface,meta);\n    renderer.resetState();\n    candidate=await prepareCandidate(surface,meta,'${mode}');`);
  source=source.replace("gameProgram(gl, surface[key], 'instanceInfo.x')","gameProgram(gl, surface[key], 'instanceInfo.x',false,candidate)");
  source=source.replace('    const use=pass=>{','    candidate.prepare(batches,frustum,unit);\n    const use=pass=>{');
  await fs.writeFile(path.join(folder,mode+(probe?'-probe':'')+'.js'),source);
}
