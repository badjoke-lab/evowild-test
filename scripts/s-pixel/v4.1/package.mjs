// Build a self-contained device demo. These two elevation banks are all the
// five unmodified race trajectories request; use the original RGBA/depth PNGs.
import fs from 'node:fs/promises';
import path from 'node:path';
import {build} from 'esbuild';
import {execFileSync} from 'node:child_process';
import {DEMO} from '../browser.mjs';
const folder=process.argv[2];
if(!path.isAbsolute(folder||''))throw Error('Provide an absolute fresh packaging directory');
await fs.mkdir(folder,{recursive:true});
const root='https://offline.invalid/s-pixel-lab/',packed={};
async function add(name){packed[new URL(name,root).href]=(await fs.readFile(path.join(DEMO,name))).toString('base64');}
for(const file of ['v2/assets/angles/index.json','v3/assets/manifest.json','v3/assets/runtime/paint.gz','v4/assets/index.json','v4/assets/geometry.gz','v4/assets/detail.gz','v4.1/assets/index.json','v4.1/assets/geometry.gz'])await add(file);
const atlas=JSON.parse(await fs.readFile(path.join(DEMO,'v2/assets/angles/index.json')));
for(const i of [1,2])for(const files of atlas.angles[i].files)for(const j of [0,3])await add('v2/assets/angles/'+files[j]);
const app=await build({entryPoints:[path.join(DEMO,'v4.1/device.js')],bundle:true,write:false,format:'iife',plugins:[{
 name:'bundle-immutable-race-assets',setup(b){b.onLoad({filter:/\.js$/},async args=>{
  const text=await fs.readFile(args.path,'utf8');
  return {contents:text.replaceAll('import.meta.url',JSON.stringify(new URL(path.relative(DEMO,args.path),root).href))
   .replace(/\bfetch\(/g,'assetFetch('),resolveDir:path.dirname(args.path),loader:'js'};
 });}
}]});
const css=await fs.readFile(path.join(DEMO,'v4.1/meter.css'),'utf8');
const script='const assets='+JSON.stringify(packed)+`;
async function assetFetch(url){
 const src=assets[String(url)];if(!src)throw Error('素材がありません '+url);
 const data=Uint8Array.from(atob(src),c=>c.charCodeAt(0));
 return new Response(data,{headers:{'Content-Type':String(url).endsWith('.png')?'image/png':'application/octet-stream'}});
}
`+app.outputFiles[0].text;
let html=await fs.readFile(path.join(DEMO,'v4.1/index.html'),'utf8');
html=html.replace('<link rel="stylesheet" href="meter.css">','<style>'+css+'</style>')
 .replace('<script type="module" src="device.js"></script>',()=>'<script>'+script.replace(/<\/script/gi,'<\\/script')+'</script>');
await fs.writeFile(path.join(folder,'index.html'),html);
await fs.cp(path.join(DEMO,'v4.1/evidence'),path.join(folder,'evidence'),{recursive:true});
await fs.writeFile(path.join(folder,'README.txt'),`EvoWild Run / S型 v4.1
1. ZIPを展開し、index.htmlをWebGL 2対応ブラウザで開いてください。
2. PCとAndroidを同じWi-Fiで比較する場合は、展開フォルダーで python3 -m http.server 8000 --bind 0.0.0.0 を起動します。
   PCは http://localhost:8000/index.html 、AndroidのChromeは http://PCのLANアドレス:8000/index.html を開きます。
3. 同じ描画サイズを選び、端末名を入力して「2条件を測定」。タブを前面に保ち、完了後「JSONを保存」。
4. v4へのリンクで同じ操作を繰り返します。どちらの版も画面内でGPU名と結果を確認できます。
詳細とSwiftShader結果は evidence/review.html にあります。
`);
execFileSync('python3',['-c',`import zipfile,sys
from pathlib import Path
folder=Path(sys.argv[1])
with zipfile.ZipFile(sys.argv[2],'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in [folder/'README.txt',folder/'index.html',*sorted((folder/'evidence').rglob('*'))]:
  if p.is_file(): z.write(p,p.relative_to(folder))
`,folder,path.join(DEMO,'v4.1/device-demo.zip')]);
