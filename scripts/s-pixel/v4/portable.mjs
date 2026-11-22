// Package the tested renderer with its local assets so file:// works without
// CORS exceptions, a web server, or a connection to GitHub.
import fs from 'node:fs/promises';
import path from 'node:path';
import {build} from 'esbuild';
import {execFileSync} from 'node:child_process';
import {DEMO} from '../browser.mjs';

const base='https://offline.invalid/s-pixel-lab/';
const dir=process.argv[2];
if(!dir || !path.isAbsolute(dir))throw Error('Pass an absolute temporary output directory');
await fs.mkdir(dir,{recursive:true});
const data={},stacks={};
async function add(rel,map=data){
 const file=path.join(DEMO,rel);
 if((await fs.stat(file)).isDirectory()){
  for(const child of (await fs.readdir(file)).sort())await add(rel+'/'+child,map);
 }else map[new URL(rel,base).pathname]=(await fs.readFile(file)).toString('base64');
}
for(const entry of ['v2/assets/angles','v3/assets/directions.json','v3/assets/manifest.json','v3/assets/runtime/paint.gz','v3/assets/exact','v4/assets'])await add(entry);
await add('v3/assets/stack-128',stacks);

const runtime=`function assetBlob(url){
 const key=new URL(url,'${base}v3/').pathname;
 if(!Object.hasOwn(packed,key))throw Error('Missing asset '+key);
 const text=atob(packed[key]),bytes=new Uint8Array(text.length);
 for(let i=0;i<text.length;i++)bytes[i]=text.charCodeAt(i);
 return new Blob([bytes],{type:key.endsWith('.png')?'image/png':key.endsWith('.json')?'application/json':'application/octet-stream'});
}
const assetFetch=async url=>new Response(assetBlob(url));
const imageURL=url=>URL.createObjectURL(assetBlob(url));`;
const worker='const packed='+JSON.stringify(stacks)+';\n'+runtime+'\n'+(await fs.readFile(path.join(DEMO,'sections.js'),'utf8')).replace('await fetch(url)','await assetFetch(url)');
const result=await build({entryPoints:[path.join(DEMO,'v3/lab.js')],write:false,bundle:true,format:'iife',plugins:[{
 name:'offline-v4',
 setup(build){
  build.onResolve({filter:/^\.\/race-renderer\.js$/},args=>args.importer===path.join(DEMO,'v3/lab.js')?{path:path.join(DEMO,'v4/race-renderer.js')}:null);
  build.onLoad({filter:/\.js$/},async args=>{
   let code=await fs.readFile(args.path,'utf8');
   code=code.replaceAll('new Worker(new URL(\'./sections.js\',import.meta.url))','new Worker(workerURL)')
    .replace("new URL(key+'.png',new URL(document.body.dataset.viewImages || './assets/views/',import.meta.url))","imageURL(new URL(key+'.png',new URL(document.body.dataset.viewImages || './assets/views/',import.meta.url)))")
    .replaceAll('import.meta.url',JSON.stringify(new URL(path.relative(DEMO,args.path),base).href)).replace(/\bfetch\(/g,'assetFetch(');
   return {contents:code,loader:'js',resolveDir:path.dirname(args.path)};
  });
 }
}]});
const css=await Promise.all(['lab.css','v3/lab.css'].map(p=>fs.readFile(path.join(DEMO,p),'utf8')));
let html=await fs.readFile(path.join(DEMO,'v4/index.html'),'utf8');
html=html.replace(/<link rel="stylesheet"[^>]*>/g,'').replace('</head>','<style>'+css.join('\n')+'</style></head>')
 .replace(/<nav>.*?<\/nav>/,'<nav><a class="sel" href="#lab">v4</a></nav>')
 .replace('../v3/assets/voxels/index.json','voxels.json');
const script='const packed='+JSON.stringify(data)+';\n'+runtime+'\nconst workerURL=URL.createObjectURL(new Blob(['+JSON.stringify(worker)+'],{type:"text/javascript"}));\n'+result.outputFiles[0].text;
html=html.replace(/<script type="importmap">[\s\S]*?<\/script><script type="module"[^>]*><\/script>/,()=>'<script>'+script.replace(/<\/script/gi,'<\\/script')+'</script>');
await fs.writeFile(path.join(dir,'index.html'),html);
await fs.copyFile(path.join(DEMO,'v3/assets/voxels/index.json'),path.join(dir,'voxels.json'));
await fs.cp(path.join(DEMO,'v4/evidence'),path.join(dir,'evidence'),{recursive:true});
const archive=path.join(DEMO,'v4/evowild-v4-demo.zip');
execFileSync('python3',['-c',`import sys,zipfile
from pathlib import Path
root=Path(sys.argv[1])
with zipfile.ZipFile(sys.argv[2],'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5) as f:
 for p in sorted(root.rglob('*')):
  if p.is_file(): f.write(p,p.relative_to(root))
`,dir,archive]);
console.log(archive);
