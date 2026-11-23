// Build an instrumented copy alongside a normal build. Production code and
// the RAF acceptance trial never import these probes.
import {build} from 'esbuild';
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {root} from '../race-integration/browser.mjs';
const [dir, ref]=process.argv.slice(2);
if(!dir)throw Error('Pass the absolute built evowild-test directory and optionally its source ref');
const read=async file=>ref?execFileSync('git',['show',ref+':'+file],{cwd:root,encoding:'utf8'}):fs.readFile(path.join(root,file),'utf8');
function edit(s,old,next){
 if(!s.includes(old))throw Error('Missing probe seam: '+old);
 return s.replace(old,next);
}
let actor=await read('public/race-integration/actors.js');
actor=edit(actor,'    serial++;','    const lodStart = window.ridgeMeter.active ? performance.now() : null;\n    serial++;');
actor=edit(actor,'    const use=pass=>{','    if(lodStart!==null)window.ridgeMeter.add("sLod",performance.now()-lodStart);\n    const use=pass=>{');
actor=edit(actor,'surface.draw(batches,use,drift);',"window.ridgeMeter.part('pixelMesh',()=>surface.draw(batches,use,drift));");
actor=edit(actor,'sprites.far.draw(instances,',"window.ridgeMeter.part('sprite',()=>sprites.far.draw(instances,");
actor=edit(actor,'drift,sprites.buffer,use);','drift,sprites.buffer,use));');
await fs.mkdir(path.join(dir,'race-integration'),{recursive:true});
await fs.writeFile(path.join(dir,'race-integration/probe-actors.js'),actor);
await build({absWorkingDir:root,entryPoints:['src/main.js'],bundle:true,format:'esm',minify:true,target:'es2022',
 outfile:path.join(dir,'ridge-probe.js'),define:{'import.meta.env.BASE_URL':'"/evowild-test/"'},
 plugins:[{name:'measure-game',setup(b){
 b.onLoad({filter:/src\/race-trial\.js$/},async()=>({contents:(await read('src/race-trial.js')).replace('race-integration/actors.js','race-integration/probe-actors.js'),loader:'js',resolveDir:path.join(root,'src')}));
 b.onLoad({filter:/src\/main\.js$/},async()=>{
 let s=await read('src/main.js');
 s=edit(s,'renderer.setAnimationLoop(frame);',`
 const probe = window.ridgeMeter;
 probe.attach(renderer, racers, raceEnvironment, ground);
 window.ridgePrepare=(cameraName)=>{
   document.querySelector('[data-view="'+cameraName+'"]').click();
   resetRace();camera.position.set(-12,12,28);camera.up.set(0,1,0);camera.lookAt(0,.8,0);
 };
 window.ridgeAdvance=()=>{update(1000/30);trial.sync();setCamera();};
 window.ridgeStep=()=>frame(last+1000/30);
 window.ridgeActorsPhoto=()=>{
   const background=scene.background, visibility=raceEnvironment.map(o=>o.visible);
   try {
     raceEnvironment.forEach(o=>o.visible=false);scene.background=new THREE.Color(0);
     renderer.render(scene,camera);trial.draw(camera,view);return canvas.toDataURL().split(',')[1];
   } finally {scene.background=background;raceEnvironment.forEach((o,i)=>o.visible=visibility[i]);}
 };
 window.ridgeStatus=()=>({state:window.raceSnapshot(), size:[canvas.width,canvas.height], aa:renderer.getContext().getContextAttributes().antialias});
 `);
 for(const [orig,name] of [['update(trial?.step ?? dt);','simulation'],['trial?.sync();','sTravel'],['setCamera();','camera'],['renderer.render(scene, camera);','three'],['trial?.draw(camera,view);','pixel'],['updateHud();','ui'],['drawMiniMap();','ui'],['trial?.frame(now,view);','ui']]){
   const at=s.indexOf('function frame(now)');s=s.slice(0,at)+edit(s.slice(at),orig,'window.ridgeMeter.time("'+name+'",()=>{'+(name==='simulation'?'update(1000/30);':orig)+'});');
 }
 s=edit(s,'    const stride = Math.sin(elapsed','    const poseStart = window.ridgeMeter.active ? performance.now() : null;\n    const stride = Math.sin(elapsed');
 s=edit(s,'    });\n  }\n\n  ring.position','    });\n    if(poseStart!==null)window.ridgeMeter.add(r.morph==="S"?"classicSPose":"otherRigPose",performance.now()-poseStart);\n  }\n\n  ring.position');
 return {contents:s,loader:'js',resolveDir:path.join(root,'src')};
 });
 }}]});
let html=await fs.readFile(path.join(dir,'index.html'),'utf8');
html=html.replace(/<script type="module"[^>]*src="[^"]+"[^>]*><\/script>/,'<script type="module" src="./ridge-probe.js"></script>');
await fs.writeFile(path.join(dir,'probe.html'),html);
