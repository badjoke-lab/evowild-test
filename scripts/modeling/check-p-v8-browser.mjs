// Isolated static asset fixture: this does not modify a race or product review UI.
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {chromium,devices} from '@playwright/test';
const root=process.cwd(),out='docs/evidence/p-canonical-3d-v8-20261013';
const asset='/public/models/evowild-p/p-canonical-v8.glb';
const hash=crypto.createHash('sha256').update(await fs.readFile(root+asset)).digest('hex');
const html=`<!DOCTYPE html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>P v8 static GLB verification</title><style>body{margin:0;background:#343d46;color:white;font:16px sans-serif}canvas{display:block}#label{position:absolute;top:12px;left:18px}</style><div id="label">P canonical v8 / STATIC REVIEW / HOLD</div><script type="importmap">{"imports":{"three":"/node_modules/three/build/three.module.js"}}</script><script type="module">
import * as THREE from 'three';import {GLTFLoader} from '/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
const r=new THREE.WebGLRenderer({antialias:true});r.setSize(innerWidth,innerHeight);r.setPixelRatio(1);r.setClearColor(0x343d46);document.body.append(r.domElement);
const s=new THREE.Scene();s.add(new THREE.HemisphereLight(0xe9eef4,0x34313a,2.0));const l=new THREE.DirectionalLight(0xffffff,3);l.position.set(-4,7,5);s.add(l);
const halfHeight=Math.max(2.425,2.425*innerHeight/innerWidth);const c=new THREE.OrthographicCamera(-halfHeight*innerWidth/innerHeight,halfHeight*innerWidth/innerHeight,halfHeight,-halfHeight,.01,100);
const bytes=await(await fetch('${asset}')).arrayBuffer();const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
const gltf=await new GLTFLoader().parseAsync(bytes,'');s.add(gltf.scene);let meshes=0,vertices=0;gltf.scene.traverse(o=>{if(o.isMesh){meshes++;vertices+=o.geometry.attributes.position.count;}});
const box=new THREE.Box3().setFromObject(gltf.scene);
window.setView=name=>{const p={SIDE:[0,2.15,10],FRONT:[-10,2.15,0],FRONT34:[-6,3.4,10],REAR34:[6,3.4,10],BACK:[10,2.15,0]}[name];c.position.set(...p);c.lookAt(-.02,1.63,0);r.render(s,c);const projected=[];for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])projected.push(new THREE.Vector3(x,y,z).project(c));const inFrame=projected.every(p=>Math.abs(p.x)<.99&&Math.abs(p.y)<.99);return{triangles:r.info.render.triangles,calls:r.info.render.calls,inFrame};};
window.__result={asset:'${asset}',sha256:digest,meshes,vertices,animations:gltf.animations.length,bounds:{min:box.min.toArray(),max:box.max.toArray()},first:window.setView('FRONT34')};
</script></html>`;
const server=http.createServer(async(req,res)=>{try{if(req.url==='/favicon.ico'){res.writeHead(204).end();return;}if(req.url==='/check'){res.setHeader('Content-Type','text/html');res.end(html);return;}const p=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));if(!p.startsWith(root+path.sep)){res.writeHead(403).end();return;}const type=p.endsWith('.js')?'text/javascript':p.endsWith('.glb')?'model/gltf-binary':'application/octet-stream';res.setHeader('Content-Type',type);res.end(await fs.readFile(p));}catch{res.writeHead(404).end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--no-sandbox']});
const results=[];
try{for(const [name,options] of [['desktop',{viewport:{width:1100,height:900}}],['mobile',{...devices['Pixel 7']}]] ){
const context=await browser.newContext(options);const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
await page.goto('http://127.0.0.1:'+server.address().port+'/check');await page.waitForFunction(()=>window.__result,{timeout:30000});const data=await page.evaluate(()=>window.__result);
if(data.sha256!==hash||data.animations!==0||data.meshes<3||data.first.triangles<1000)throw new Error('Wrong or empty v8 asset: '+JSON.stringify(data));
const views=[];for(const view of name==='desktop'?['SIDE','FRONT','FRONT34','REAR34','BACK']:['FRONT34']){const rendered=await page.evaluate(v=>window.setView(v),view);if(rendered.triangles<1000||!rendered.inFrame)throw new Error('Empty or cropped render: '+JSON.stringify(rendered));views.push({view,...rendered});if(view==='FRONT34')await page.screenshot({path:path.join(out,'browser-'+name+'.png')});}
if(errors.length)throw new Error(errors.join('\n'));results.push({device:name,...data,views,errors});await context.close();
}}finally{await browser.close();server.close();}
await fs.writeFile(path.join(out,'browser-validation.json'),JSON.stringify({status:'PASS',scope:'Isolated static v8 GLB load/render, no gait or production approval',results},null,2)+'\n');console.log('v8 browser static asset checks PASS');
