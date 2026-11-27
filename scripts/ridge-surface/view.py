"""Build a compact browser report from saved measurements."""
import csv
import json
from pathlib import Path
folder=Path('public/ridge-surface');out=folder/'evidence'
gpu=list(csv.DictReader((out/'gpu.csv').open()));perf=list(csv.DictReader((out/'performance.csv').open()))
summ=json.loads((out/'summary.json').read_text())
rows=[]
for screen in ('pc','phone'):
 for n in (18,50,100):
  for camera in ('race','follow'):
   key=f'{screen}-{n}-pixel-{camera}'
   for mode in ('base','group','color','both'):
    g=next(r for r in gpu if r['case']==key and r['mode']==mode)
    p=next(r for r in perf if r['case']==key and r['mode']==mode)
    vals=[screen,str(n),camera,mode,g['mesh_gpu_ms'],g['triangle_reduction_pct'],p['fps'],p['p95_ms']]
    rows.append('<tr>'+''.join('<td>'+v+'</td>' for v in vals)+'</tr>')
html='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Ridge Oval 表面限定試験</title>
<style>*{box-sizing:border-box}body{max-width:1120px;margin:0 auto;padding:24px 16px 64px;background:#f2f4ed;color:#1b2f32;font:16px/1.65 system-ui,sans-serif}h1{font-size:clamp(1.5rem,4vw,2.4rem)}a{color:#12586a}h2{margin-top:36px;border-top:1px solid #afbfb0;padding-top:14px}img,video{display:block;width:100%;height:auto}table{border-collapse:collapse;white-space:nowrap;font-variant-numeric:tabular-nums}th,td{padding:4px 10px;border-bottom:1px solid #acb8b0;text-align:right}.scroll{overflow-x:auto}.media{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(350px,100%),1fr));gap:12px}nav a{display:inline-block;margin:0 16px 8px 0}figure{margin:12px 0}</style>
<h1>Ridge Oval S型表面の限定最適化</h1>
<p><strong>REJECT</strong>。群カリング、単色領域、併用を試作・測定した。基準は2606922。通常ゲームは基準版を継続する。以下はChromium SwiftShaderの値。</p>
<nav><a href="README.md">採用判定と残存負荷</a><a href="PROOF.md">カリングと色参照の保守性</a><a href="evidence/gpu.csv">GPU・三角形CSV</a><a href="evidence/performance.csv">実RAF CSV</a><a href="evidence/raw.zip">計測JSON</a></nav>
<p>リポジトリで <code>python3 scripts/ridge-surface/serve.py</code> を実行すると、ポート8000で基準と三つの試作を選んで操作できる。</p>
<h2>画質の差</h2><p>画像の左は基準、群、単色、併用の順。右は基準に対するRGB差を64倍表示。黒は差が0。</p>
<div class="media">IMAGES</div>
<h2>50・100体の走行</h2><p>基準と併用版の実時間収録。各動画でRaceからFollowへ切り替える。画面内のゲーム時刻とレース状態は各収録の進行を示す。</p>
<div class="media">VIDEOS</div>
<h2>同条件の計測</h2><p>GPUは各7時点の平均、FPSとp95は予熱24フレーム後の96実RAF。三角形削減率は同じ開始HEADとの比較。baseは基準、groupは群、colorは単色、bothは併用。</p>
<div class="scroll"><table><thead><tr><th>画面</th><th>体数</th><th>カメラ</th><th>方式</th><th>表面GPU ms</th><th>三角形削減 %</th><th>FPS</th><th>p95 ms</th></tr></thead><tbody>ROWS</tbody></table></div>
<nav><a href="evidence/quality.csv">168組の画質</a><a href="evidence/summary.json">条件別の合否</a><a href="evidence/base/regression.json">基準回帰</a><a href="evidence/group/regression.json">群回帰</a><a href="evidence/color/regression.json">単色回帰</a><a href="evidence/both/regression.json">併用回帰</a></nav></html>'''
images=''.join(f'<figure><a href="evidence/{cam}-{n}-difference.png"><img loading="lazy" src="evidence/{cam}-{n}-difference.png" alt="{n}体 {cam} の画質差"></a><figcaption>{n}体 {cam}</figcaption></figure>' for n in (50,100) for cam in ('race','follow'))
videos=''.join(f'<figure><video controls preload="metadata" playsinline src="evidence/{mode}/race-{n}.mp4"></video><figcaption>{n}体 {mode}</figcaption></figure>' for n in (50,100) for mode in ('base','both'))
(folder/'index.html').write_text(html.replace('IMAGES',images).replace('VIDEOS',videos).replace('ROWS',''.join(rows)))
