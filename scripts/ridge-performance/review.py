"""Render the downloadable results page from its measured CSV."""
import csv
import json
import sys
from pathlib import Path

folder=Path(sys.argv[1])
with (folder/'evidence/performance.csv').open() as f:
    results=list(csv.DictReader(f))
checks=json.loads((folder/'evidence/checks.json').read_text())
by_key={(r['id'],r['build']):r for r in results}
tables=[]
for screen,title in [('pc','PC幅'),('phone','スマホ幅')]:
    rows=[]
    for count in (18,50,100):
        for cam in ('race','follow'):
            for look in ('classic','pixel'):
                key=f'{screen}-{count}-{look}-{cam}'
                before,after=[by_key[key,v] for v in ('before','after')]
                cells=['18体混走' if count==18 else f'S型{count}体',cam.capitalize(),'従来' if look=='classic' else 'ピクセル']
                cells.extend(f"{float(entry[k]):.2f}" for entry in (before,after) for k in ('fps','p95_ms'))
                rows.append('<tr>'+''.join('<td>'+c+'</td>' for c in cells)+'</tr>')
    tables.append(f'<h3>{title}</h3><div class="scroll"><table><thead><tr><th>編成</th><th>カメラ</th><th>表示</th><th>前 FPS</th><th>前 p95 ms</th><th>後 FPS</th><th>後 p95 ms</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>')
pairs=sum(r['state_pairs'] for r in checks)
mask=sum(r['mask_changed'] for r in checks)
decision='REVISE' if any(r['pass_both']!='True' for r in results if r['build']=='after') else '実機確認待ち'
html='''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Ridge Oval｜統合レースの負荷解析</title>
<style>*{box-sizing:border-box}body{max-width:1080px;margin:0 auto;padding:24px 16px 64px;background:#f2f4ed;color:#1b2f32;font:16px/1.65 system-ui,sans-serif}h1{font-size:clamp(1.6rem,4vw,2.5rem);line-height:1.3}h2{margin:36px 0 12px;border-top:1px solid #acbab2;padding-top:14px}h3,figure{margin:20px 0 8px}a{color:#12586a}table{border-collapse:collapse;white-space:nowrap;font-variant-numeric:tabular-nums}td,th{padding:5px 12px;border-bottom:1px solid #bcc6be;text-align:right}td:first-child,th:first-child{text-align:left}.scroll{overflow-x:auto}img,video{display:block;width:100%;height:auto}.media{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr));gap:16px}figcaption{margin:6px 0 16px}nav a{display:inline-block;margin:0 18px 8px 0}details{margin:16px 0}</style>
<h1>Ridge Oval 統合レースの負荷解析</h1>
<nav><a href="../?raceTrial=1">18体混走を操作</a><a href="../?raceTrial=1&amp;field=s&amp;count=50">S型50体</a><a href="../?raceTrial=1&amp;field=s&amp;count=100">S型100体</a><a href="../race-integration/compare.html">実機JSONを比較</a></nav>
<p><strong>DECISION</strong>　Chromium / ANGLE SwiftShaderによる採用試験。目標は平均30 FPS以上・p95 33.3 ms以下。物理GPU搭載PCとAndroid実機は未測定。</p>
<h2>1800mの実走行</h2><div class="media"><figure><video src="evidence/race-50.mp4" controls preload="metadata" playsinline></video><figcaption>S型50体・Race → Follow</figcaption></figure><figure><video src="evidence/race-100.mp4" controls preload="metadata" playsinline></video><figcaption>S型100体・Race → Follow</figcaption></figure></div>
<h2>改修前後の画質</h2><p>各画像の左が開始HEAD、右が改修後。同じレース時刻・カメラ・出走編成で比較した。PAIRS組の全個体状態・提出ID・姿勢・LODが一致。個体画像の前景マスク差はMASK画素。</p>
<figure><a href="evidence/race-pc.png"><img src="evidence/race-pc.png" alt="PC幅のS型100体、従来表示とピクセル表示の改修前後"></a><figcaption>PC幅・S型100体・Race</figcaption></figure>
<div class="media"><figure><a href="evidence/pack-detail.png"><img loading="lazy" src="evidence/pack-detail.png" alt="密集するS型の同一部位を2倍に拡大"></a><figcaption>100体の頭冠・脚先・尾を等位置で2倍拡大</figcaption></figure><figure><a href="evidence/follow-phone.png"><img loading="lazy" src="evidence/follow-phone.png" alt="スマホ幅の18体混走、Followの前後比較"></a><figcaption>スマホ幅・通常18体混走・Follow</figcaption></figure></div>
<h2>フレーム時間</h2><p>1条件につき24フレーム予熱後の96実RAF。PCは736×500・AA有、スマホ幅は561×859・AA無。同条件の平均FPSとp95を左右に表示する。</p>
<figure><a href="evidence/frame-times.png"><img loading="lazy" src="evidence/frame-times.png" alt="S型100体、全96フレームの実RAF間隔"></a><figcaption>S型100体・レース時刻ごとのフレーム間隔</figcaption></figure>
TABLES
<h2>測定ファイル</h2><nav><a href="evidence/performance.csv">性能CSV</a><a href="evidence/cpu-gpu.csv">CPU・GPU内訳</a><a href="evidence/slow-replay.csv">低速区間の再計測</a><a href="evidence/quality.csv">画素比較</a><a href="evidence/regression.json">操作回帰</a><a href="evidence/raw.zip">全計測JSON</a><a href="README.md">判定と技術報告</a></nav>
<h2>実機で測る</h2><p>ゲームの「出走設定」で編成を選び、「新しいレース」を押す。RaceまたはFollowを選び、「実機計測」で端末名を入力して96フレームを測定する。終了後にJSONを保存する。同じ端末・画面向きで従来表示とピクセル表示を交互に各3回測り、JSON比較画面で平均とp95を確認する。</p></html>'''
(folder/'index.html').write_text(html.replace('DECISION',decision).replace('TABLES','\n'.join(tables)).replace('PAIRS',str(pairs)).replace('MASK',str(mask)))
