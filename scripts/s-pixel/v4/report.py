"""Generate the adoption page from the paired captures."""
import csv
import json
from pathlib import Path

out = Path(__file__).resolve().parents[3]/'public/s-pixel-lab/v4/evidence'
rows = list(csv.DictReader((out/'race-performance.csv').open()))
quality = json.loads((out/'appearance.json').read_text())
def read(name):
    return json.loads((out/name).read_text())
def n(v): return f'{float(v):.2f}'
def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>'+''.join(f'<th>{h}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{v}</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def paired(profile,case):
    return [next(r for r in rows if r['version']==v and r['scenario']==case and r['profile']==profile) for v in ('v3','v4')]
def pair(items,key):return ' → '.join(n(r[key]) for r in items)
names={'near1':'近景1体','near10':'近景10体','mixed50':'混在50体','mixed100':'混在100体','overview100':'全景100体'}
timing=[]
for profile in ['desktop','mobile']:
    for case,name in names.items():
        rr=paired(profile,case)
        timing.append(['PC幅' if profile=='desktop' else 'スマホ幅',name]+[pair(rr,k) for k in ('avg_fps','p95_frame_ms','gpu_ms','tris_mean','draws_mean','gl_mib')])
pass_rows=[]
for case in ['mixed50','mixed100']:
    for v in ['v3','v4']:
        r=next(r['mean'] for r in read(v+'-passes.json') if r['scenario']==case)
        tr=next(r['mean'] for r in read(v+'-transition-passes.json') if r['scenario']==case)
        pass_rows.append([names[case],v]+[n(r[k]) for k in ['floor_gpu_ms','shadow_gpu_ms','mesh_gpu_ms','sprites_gpu_ms','mesh_calls','classify_ms','transition']]+[n(tr['mesh_gpu_ms']+tr['sprites_gpu_ms'])])
def comparison(group,region,method='lod'):
    return ' → '.join(f'{quality[v+"-"+method]["summary"][group][region]["iou_median"]:.3f}' for v in ('v3','v4'))
def flicker(region,m):
    return ' → '.join(f'{100*quality[v+"-"+m]["orbit"][region]["fraction"]:.2f}%' for v in ('v3','v4'))
qrows=[]
for m,title in [('lod','標本表示'),('lod-race','群走と同じ単一サンプル')]:
    for group,caption in [('views','静止5視点'),('gait','24姿勢 × 5視点'),('front','正面24姿勢'),('rear','背面24姿勢'),('switch','遠景から近景73時点'),('fade','移行帯103〜113 px')]:
        qrows.append([title,caption]+[comparison(group,r,m) for r in ('body','crest','feet')])
def links(entries):
    return '　'.join(f'<a href="{href}">{name}</a>' for name,href in entries)
p100=paired('desktop','mixed100')
m100=next(r['mean'] for r in read('v4-passes.json') if r['scenario']=='mixed100')
env=read('v4-race.json')['environment']
content=f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width,initial-scale=1"><title>S型 v4 採用試験 | EvoWild Run</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f5f6ee;color:#203329;font:16px/1.65 system-ui,sans-serif}}main,header>div{{max-width:1320px;margin:auto;padding:22px clamp(15px,4vw,64px)}}header{{background:#21382e;color:white}}header a{{color:#b9e8ce}}h1{{font-size:clamp(28px,4vw,49px);margin:.4em 0}}h2{{margin:1.7em 0 .4em}}h3{{margin-bottom:.3em}}a{{color:#246044}}.scroll{{overflow:auto}}table{{border-collapse:collapse;background:white;min-width:max-content;width:100%;font-variant-numeric:tabular-nums}}td,th{{padding:7px 12px;text-align:right;border-bottom:1px solid #d8e1d6}}td:first-child,th:first-child{{text-align:left}}th{{background:#e1eadf}}img,video{{max-width:100%;height:auto}}figure{{margin:14px 0}}figcaption,small{{color:#476052}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));gap:15px}}.grid figure{{margin:0}}code{{overflow-wrap:anywhere}}</style></head>
<body><header><div><a href="../index.html">操作デモへ戻る</a><h1>S型 v4　採用判定 REVISE</h1><p>PC幅の混在50体は {n(paired('desktop','mixed50')[1]['avg_fps'])} fps、100体は {n(p100[1]['avg_fps'])} fps。両条件で目標の平均30 fpsを下回った。100体の p95 は {n(p100[1]['p95_frame_ms'])} ms。</p></div></header>
<main><h2>混在群走の実測</h2><p>各欄は v3 → v4。v3 と同じカーブの3秒を48時点で描画した。両版の全480組で走行時刻・方位・俯角・倍率、個体境界が画面に交差する数、画面内の中心数、全身が入る数、投影幅の最小・最大、LOD別の個体数が一致した。</p>
{table(['画面','条件','平均 fps','p95 ms','GPU ms','平均三角形','平均 draw','GL MiB'],timing)}
<p>Chromium {env['chromium']} / {env['renderer']}。PC幅は 877 × 414、スマホ幅は 352 × 335、CPU 4倍減速、DPR 1。物理GPU・スマートフォン実機は未計測。必要な素材を読み込み、3フレーム予熱。各RAFの最後に中央1画素を同期読出しし、実時間の平均と48間隔の46番目を掲載した。GPU値はタイマークエリ、GLメモリはバッファ・テクスチャ・レンダーバッファの論理割当。JSヒープ・プロセスRSS・GPU有効サンプル数もCSVに収録。</p>
{links([('性能CSV','race-performance.csv'),('v3 全フレーム','v3-race.json'),('v4 全フレーム','v4-race.json'),('試作の測定','trials.csv')])}
<h2>負荷の所在</h2><p>PC幅で同じ48時点を別に再生し、床・影・メッシュ・スプライトのGPU時間を個別に計測。移行個体GPU欄は追加リプレイで被覆率が0と1の間にある個体だけを取り出したメッシュ＋スプライトの値。別計測なので全景の時間からの差分ではない。</p>
{table(['条件','版','床 ms','影 ms','メッシュ ms','スプライト ms','メッシュ draw','分類 CPU ms','移行個体数','移行個体 GPU ms'],pass_rows)}
<p>v4 の混在100体ではメッシュ {n(m100['mesh_gpu_ms'])} ms と床 {n(m100['floor_gpu_ms'])} ms が残る。LOD分類は {n(m100['classify_ms'])} ms。密集時のメッシュ描画と同期完了までの時間が実用化の制約。多数個体の動的インデックス結合を試すと、100体全体の呼出しは平均5回に減ったがGPU時間が増えたため棄却した。</p>
{links([(v+' パス別',v+'-passes.json') for v in ['v3','v4']]+[(v+' 移行のみ',v+'-transition-passes.json') for v in ['v3','v4']])}
<h2>造形と動き</h2><p>最上位原画と v3 の25個のボクセル原本を保持。静止1姿勢と走行24姿勢の17色、接地する脚、ストライド、時刻は共通。精細メッシュの頭冠・足先を部分固定し、レース用メッシュは格子状の段差を平滑化してから頂点位置を最適化した。陰影と接地補正の重みを頂点に保存し、完全不透明と移行中のメッシュを別のシェーダーで処理。中距離は v3 のメッシュを使う。遠景は同じ奥行き付きスプライト、移行帯も同一。</p>
<figure><a href="original.png"><img src="original.png" alt="基準原画、128層原本、v3、v4 の5方向比較"></a></figure>
<p>表は128層原本に対するシルエットIoUの中央値。黒背景512 × 320で、最大色成分が12を超える画素を使用。頭冠は上端25%、足先は下端18%の範囲で、姿勢により他の部位も含む。</p>
{table(['描画条件','検査','全身IoU','頭冠IoU','足先IoU'],qrows)}
<div class="grid"><figure><a href="legs.png"><img src="legs.png" alt="正面・背面の同位相脚先"></a><figcaption>原本・v3・v4 を同じ倍率で比較</figcaption></figure><figure><a href="transition.png"><img src="transition.png" alt="遠景から近景への切り替え"></a><figcaption>スプライト、移行帯、メッシュの輪郭</figcaption></figure></div>
<p>360°回転（固定姿勢、2°刻み、投影幅156 px）で頭冠領域の1フレームだけ明暗が反転する被覆画素率は、標本表示 {flicker('crest','lod')}、単一サンプル {flicker('crest','lod-race')}。正面・背面では原本の足先領域の分離した186か所のうち、画素の半分以上が残り別々に見える箇所は標本表示で169 → 176、単一サンプルでは169 → 169。重なった脚を解剖学的に識別できることまでは示さない。</p>
<p>標本用の4サンプルAAは走行コースの計測には使っていない。個別の視点・姿勢には欠けが残る。単一サンプルでは遠近73時点の頭冠IoU中央値が {comparison("switch","crest","lod-race")} となり、この退行も採用見送りの理由とした。移行帯だけに限ると {comparison("fade","crest","lod-race")}。各時点の数値と最悪値を保存した。高速化試作の大きな頭冠・胴体の欠けを採用版に持ち込まないため、中距離の形状を原状に戻した。</p>
{links([('全画質測定','appearance.json'),('ブラウザ操作検査','ui.json')])}
<h2>同じ時点のレース画面</h2><div class="grid">'''+''.join(f'<figure><a href="{v}-{case}.png"><img src="{v}-{case}.png" alt="{v} {names[case]}"></a><figcaption>{v}　{names[case]}　19/48 周期位置</figcaption></figure>' for case in ('mixed50','mixed100') for v in ('v3','v4'))+'''</div>
<h2>実走行動画</h2><p>近景・混在の動画はブラウザの実時間でコースを走らせて収録。24 Hz の配信映像にはコマ保持があり、計測FPSとは異なる。旋回・単体走行・LOD検査は固定時刻の再生。</p><div class="grid">'''+''.join(f'<figure><video controls preload="none" src="{k}.mp4"></video><figcaption>{name}</figcaption></figure>' for k,name in [('mixed50','混在50体'),('mixed100','混在100体'),('near10','近景10体'),('turntable','360°回転'),('gallop','四足走行'),('lod-transition','原本とLOD移行')])+'''</div><p><a href="films.json">各動画の収録条件</a></p></main></body></html>'''
(out/'review.html').write_text(content)
