import fs from 'node:fs/promises';import path from 'node:path';import {build} from 'esbuild';import {execFileSync} from 'node:child_process';import crypto from 'node:crypto';
const root='public/exp-sprite-stacking',assets={};
async function walk(dir){for(const entry of await fs.readdir(dir,{withFileTypes:true})){const file=path.join(dir,entry.name);if(entry.isDirectory())await walk(file);else{const key=path.relative(root,file).replaceAll('\\','/');if(entry.name==='reference.png')continue;const mime=entry.name.endsWith('.png')?'image/png':entry.name.endsWith('.json')?'application/json':'application/octet-stream';assets[key]={mime,base64:(await fs.readFile(file)).toString('base64')};}}}
await walk(root+'/assets');const ref=(await fs.readFile(root+'/assets/reference.png')).toString('base64');
const bundle=await build({entryPoints:[root+'/app.js'],bundle:true,minify:true,format:'esm',target:'es2022',write:false,legalComments:'inline',logLevel:'warning'});
const preload=`const __embedded=${JSON.stringify(assets)};const __fetch=globalThis.fetch.bind(globalThis);globalThis.fetch=async(input,options)=>{const url=typeof input==='string'?input:input.url||String(input);const marker=url.indexOf('assets/');const key=marker>=0?url.slice(marker).split(/[?#]/)[0]:'';const entry=__embedded[key];if(!entry)return __fetch(input,options);const s=atob(entry.base64),a=new Uint8Array(s.length);for(let i=0;i<s.length;i++)a[i]=s.charCodeAt(i);return new Response(a,{status:200,headers:{'Content-Type':entry.mime}});};\n`;
let html=await fs.readFile(root+'/index.html','utf8');html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+await fs.readFile(root+'/style.css','utf8')+'</style>');html=html.replace(/<script type="importmap">.*?<\/script>/s,'');html=html.replace('src="assets/reference.png"',`src="data:image/png;base64,${ref}"`);const js=(preload+bundle.outputFiles[0].text).replaceAll('</script','<\\/script');html=html.replace('<script type="module" src="app.js"></script>',()=>'<script type="module">'+js+'</script>');await fs.writeFile(root+'/standalone.html',html);
const note=`EvoWild Run — Sprite Stacking 実証デモ\n\nZIPを展開し index.html をChrome/Edge等のブラウザで開く構成です。\n検証環境ではfile://直開きが管理ポリシーで拒否されたため、file originでの動作は未検証です。\n直接開けない場合は python3 start-demo.py を実行して表示されるlocalhost URLを開いてください。\nローカルHTTPからHTMLを読んだ後、通信を遮断して全描画方式・全層/ポーズ条件を検証しています。\n全素材を埋め込み、通常版の全層/全ポーズ・2D/GLB/Canvas/WebGL切替を含みます。\n検証結果は evidence/report.html 。5動画、5方向比較、性能CSV/JSONを同梱。\n←→/AD: 連続旋回、↑↓/WS: 加減速、SPACE: 一時停止。タッチ操作もあります。\n連続IK基準は元制御1×を評価する比較専用です。\n\n判定: REVISE。元のSモデル・既存四足走行を使用。新規クリーチャー生成なし。\n単一HTMLには全素材を埋め込むため、ロードとメモリは通常版の計測とは異なります。\nこのZIPを性能計測の通常版データに混ぜないでください。\n\n再現スクリプトと全ソース:\nhttps://github.com/badjoke-lab/evowild-test/tree/exp/2p5d-sprite-stacking-20261118\n`;
await fs.mkdir('work/sprite-stacking/package',{recursive:true});
await fs.writeFile('work/sprite-stacking/package/start-demo.py',`from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os, webbrowser
os.chdir(Path(__file__).resolve().parent)
url = 'http://127.0.0.1:8765/index.html'
print('EvoWild Sprite Stacking: '+url)
print('Stop: Ctrl+C')
webbrowser.open(url)
ThreadingHTTPServer(('127.0.0.1',8765),SimpleHTTPRequestHandler).serve_forever()
`);await fs.writeFile('work/sprite-stacking/package/README.txt',note);
execFileSync('python3',['-c',`from pathlib import Path
import zipfile
root=Path('public/exp-sprite-stacking')
files=[(root/'standalone.html','index.html'),(Path('work/sprite-stacking/package/README.txt'),'README.txt'),(Path('work/sprite-stacking/package/start-demo.py'),'start-demo.py'),(root/'vendor/THREE-LICENSE.txt','THREE-LICENSE.txt')]+[(p,'evidence/'+p.name) for p in sorted((root/'evidence').iterdir()) if p.is_file()]
with zipfile.ZipFile('public/exp-sprite-stacking-demo.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p,name in files:
  info=zipfile.ZipInfo(name,date_time=(2026,11,18,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,p.read_bytes())
`]);
const data={htmlBytes:Buffer.byteLength(html),htmlSha256:crypto.createHash('sha256').update(html).digest('hex'),embeddedAssets:Object.keys(assets).length,zipBytes:(await fs.stat('public/exp-sprite-stacking-demo.zip')).size,note:'Offline package embeds all comparison assets. Performance numbers apply to normal HTTP version, not embedded HTML.'};await fs.writeFile('work/sprite-stacking/package/build.json',JSON.stringify(data,null,2));console.log(data);
