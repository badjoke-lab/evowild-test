"""Package the tested build over the frozen race distribution, preserving it."""
import sys,zipfile,hashlib,json,shutil,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
BUILD=Path(sys.argv[1]);OUT=ROOT/'public/s-form';E=OUT/'evidence'
base=ROOT/'public/ridge-performance/ridge-optimized.zip'
assert subprocess.check_output(['git','diff','--name-only','a93fa4b65ea398d4e8ec0560c600f0d50abe1e72','--',
 'src/main.js','public/s-pixel-lab','public/race-integration','public/ridge-performance','public/ridge-surface','art/s-creature/references'],cwd=ROOT)==b''
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=['src/main.js','public/s-form/s-form.glb','public/s-form/anatomy.json','src/s-form/model.js','src/s-form/race.js',
 'src/race-trial.js','scripts/s-form/build.py','art/s-creature/references/00_s_type_modeling_image_v1.png',
 'art/s-creature/studies/s-form-20261128/s-form.blend']
(E/'preserved.json').write_text(json.dumps({'start_head':'a93fa4b65ea398d4e8ec0560c600f0d50abe1e72',
 'old_game_assets_and_renderers_unchanged':True,'sha256':{p:sha(ROOT/p) for p in paths},
 'baseline_distribution_sha256':sha(base)},indent=2)+'\n')
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
im=Image.new('RGB',(1480,1000),'#edf1f2');d=ImageDraw.Draw(im)
def text(x,y,s,n=18):d.text((x,y),s,font=ImageFont.truetype(font,n),fill='#213344')
text(16,12,'Ridge Oval / 同じレース時刻・位置・カメラで新旧を比較',26)
for c,label in enumerate(['旧v4.1 / Race','新形状 / Race','旧v4.1 / Follow','新形状 / Follow']):text(c*370+12,65,label)
for r,count in enumerate([1,18,50]):
 y=110+r*285;text(12,y,str(count)+('体混走' if count==18 else '体 S'),17)
 for c,(mode,view) in enumerate([('pixel','race'),('form','race'),('pixel','follow'),('form','follow')]):
  frame=Image.open(E/f'pc-{count}-{mode}-{view}.png').crop((12,69,748,568)).resize((364,247),Image.Resampling.LANCZOS)
  im.paste(frame,(c*370+3,y+27))
im.save(E/'ridge-comparison.png',optimize=True)
recordings=json.loads((E/'recordings.json').read_text())['recordings']
videos=''.join(f'<figure><video controls playsinline preload="metadata" src="evidence/{v["name"]}.mp4"></video><figcaption>{v["name"]} · 実時間収録 {len(v["samples"])}描画 / {v["samples"][-1]["wall_ms"]/1000:.2f}秒</figcaption></figure>' for v in recordings)
html='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>S型 立体造形の比較と映像</title><style>body{margin:0;background:#eaf0f3;color:#203344;font:16px system-ui,sans-serif}main{max-width:1400px;margin:auto;padding:28px}h1{font-size:32px}a{color:#21668b}nav{display:flex;gap:20px;flex-wrap:wrap}img{width:100%;height:auto}figure{margin:24px 0}video{width:100%;max-height:640px;background:#172b3a}figcaption{font-size:13px;margin-top:8px}.clips{display:grid;grid-template-columns:1fr 1fr;gap:20px}.verdict{border-left:5px solid #c6903a;padding:14px 20px;background:#fff}p{line-height:1.8}@media(max-width:700px){main{padding:14px}.clips{display:block}h1{font-size:25px}}</style><main><h1>S型の立体構造を修正する</h1><p class="verdict"><b>REVISE</b> — 胸・肩・腰の厚みと四脚の区別を改善。原画の面の流れ、肩と胸の接続、尾の重なりには差が残るため、主役としての採用は未確定です。</p><nav><a href="../s-form.html">1体を操作する</a><a href="../?raceTrial=1&sForm=1&look=form&field=s&count=1">Ridge Oval 1体</a><a href="../?raceTrial=1&sForm=1&look=form&field=mixed&count=18">18体混走</a><a href="../?raceTrial=1&sForm=1&look=form&field=s&count=50">S型50体</a><a href="README.md">修正記録と制約</a></nav><h2>最上位原画と新旧の5方向</h2><p>旧128層・旧v4.1・新メッシュは列ごとに同じカメラと倍率。原画の上面は尾だけです。原画との視覚的な差を残したまま、数値で合格とはしません。</p><a href="evidence/five-views.png"><img src="evidence/five-views.png" alt="最上位基準原画と新旧の同倍率5方向比較"></a><h2>実際のRidge Oval</h2><a href="evidence/ridge-comparison.png"><img loading="lazy" src="evidence/ridge-comparison.png" alt="1、18、50体のRaceとFollowで旧v4.1と新形状を比較"></a><h2>実物の回転と走行</h2><p>ブラウザのWebGL画面を実時間で収録しました。SwiftShaderで50体を収録した動画は更新が少なく、滑らかな実機動作の証拠にはなりません。</p><div class="clips">'''+videos+'''</div><h2>編集と再検証</h2><p><a href="s-form.glb">GLB形状データ</a> · <a href="anatomy.json">断面・部位・24位相</a> · <a href="evidence/regression.json">レース状態回帰</a> · <a href="evidence/ui-check.json">操作と変形頂点の検査</a> · <a href="evidence/preserved.json">旧資産保持・ハッシュ</a> · <a href="evidence/recordings.json">動画の収録時刻</a></p><p>保存済みの旧原本、旧24姿勢、旧レンダラーは保持しています。修正版の表示切替はレースの順位・速度・進路・カメラを変更しません。</p></main></html>'''
(OUT/'index.html').write_text(html)
destination=OUT/'ridge-form-demo.zip'
files={}
for p in (BUILD/'assets').glob('*'):files['evowild-test/assets/'+p.name]=p
for name in ['index.html','s-form.html']:files['evowild-test/'+name]=BUILD/name
for p in OUT.rglob('*'):
 if p.is_file() and p.suffix!='.zip':files['evowild-test/s-form/'+str(p.relative_to(OUT))]=p
files['source/s-form.blend']=ROOT/'art/s-creature/studies/s-form-20261128/s-form.blend'
files['source/build.py']=ROOT/'scripts/s-form/build.py'
with zipfile.ZipFile(base) as source,zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as target:
 for name in source.namelist():
  if name not in files and name not in ['index.html','README.txt']:target.writestr(name,source.read(name))
 for name,p in files.items():target.write(p,name)
 target.writestr('index.html','<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=evowild-test/s-form/"><a href="evowild-test/s-form/">S型 造形比較デモ</a>')
 target.writestr('README.txt','S型の立体造形スタディ — REVISE\n\nこのフォルダーで python3 -m http.server 8000 --bind 0.0.0.0 を実行。\nhttp://localhost:8000/ をブラウザで開く。\nsource/s-form.blend は編集可能な原本。コードから再制作する場合は指定ブランチのリポジトリを利用する。\n物理GPU・Android実機は未検証。mainと旧資産は変更していない。\n')
assert destination.stat().st_size<100*1024*1024
with zipfile.ZipFile(destination) as z:assert z.testzip() is None
print(destination,round(destination.stat().st_size/1024/1024,2),'MiB')
