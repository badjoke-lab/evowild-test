"""Write the review from the archived browser, process and geometry measurements."""
from pathlib import Path
import csv,json,statistics
D=Path(__file__).resolve().parents[3]/'public/s-pixel-lab/v2/evidence'
def read(name):return json.loads((D/name).read_text())
def median(values):return statistics.median(values)
def table(head,rows):
    return '<div class="table"><table><thead><tr>'+''.join(f'<th>{v}</th>' for v in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{v}</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def main():
    rows=[]
    for n in (128,64):
        for code in ('v1','v2'):
            file=code+('' if n==128 else '-64')+'-measurement.json'
            for r in read(file)['rows']:rows.append(dict(r,layers=n))
    mem={(r['profile'],r['method'],r['number']):r for r in read('memory.json')}
    for r in rows:
        memrow=mem.get((r['profile'],r['method'],r['number'])) if r['layers']==128 else None
        r['rss_mib_separate_run']=round(memrow['rss_mib'],2) if memrow else ''
        r['model_gpu_mib']=round(r['mesh_mib']+r['atlas_mib']+r.get('aux_mib',0),2)
        mix=r.get('mix') or {'near':r['number']}
        for l in ['near','transition','sprite','offscreen']:r[l]=mix.get(l,0)
    keys='profile method layers number width height frames fps p95_ms submit_ms draw_sync_ms gpu_ms gpu_samples triangles draw_calls blits js_heap_mib mesh_mib atlas_mib aux_mib model_gpu_mib rss_mib_separate_run near transition sprite offscreen'.split()
    with (D/'performance.csv').open('w') as f:
        writer=csv.DictWriter(f,keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(rows)
    methods={'v1':'v1 積層','stack':'v2 積層','lod':'v2 距離LOD'}
    def row(p,method,count,layers=128):return next(r for r in rows if (r['profile'],r['method'],r['number'],r['layers'])==(p,method,count,layers))
    def measurements(n):
        items=[]
        for p,name in [('desktop-1x','PC幅'),('mobile-4x','スマホ幅')]:
            for count in [1,10,50,100]:
                for mode in methods:
                    r=row(p,mode,count,n);items.append([name,methods[mode],count,r['fps'],r['p95_ms'],r['submit_ms'],r['draw_sync_ms'],r['gpu_ms'],f"{round(r['triangles']):,}",r['draw_calls'],r['js_heap_mib'],r['model_gpu_mib'],r['rss_mib_separate_run'] or '—'])
        return table(['表示','方式','体','fps','p95 ms','発行 ms','同期込 ms','GPU ms','三角形','draw','JS MiB','GL MiB','RSS MiB'],items)
    morph=read('morphology.json');appearance=read('appearance.json');sweep=read('sweep.json');views=read('five-view-iou.json');ab=read('bottleneck.json');course=read('course-measurement.json')
    legs=[]
    for view,label in [('front','正面'),('rear','背面')]:
        legs.append([label,*[f"{min(min(p[v+'_legs'][view]) for p in morph)*100:.1f}%" for v in ['v1','v2']]])
    arc=[]
    for r in course:
        mixes=r['mixSamples'];med=lambda k:median([x.get(k,0) for x in mixes])
        arc.append(['PC幅' if r['profile']=='desktop-1x' else 'スマホ幅','全景' if r['scenario']=='overview' else '近遠混在',r['count'],f"{r['zoom']:.2f}×",f"{r['fps']:.2f}",f"{r['p95_ms']:.1f}",f"{r['draw_sync_ms']:.1f}",f"{med('near'):g} / {med('transition'):g} / {med('sprite'):g} / {med('offscreen'):g}"])
    stance=read('stance.json')
    boundary=[]
    for span in (68,102,126):
        a=[r for r in appearance['switchTests'] if r['desiredSpan']==span]
        boundary.append([span,f"{min(r['iou'] for r in a):.3f}",f"{median(r['iou'] for r in a):.3f}",f"{max(r['centroid_delta_px'] for r in a):.2f}",f"{median(r['rgb_mae_255'] for r in a):.1f}"])
    cv=sweep['zoom'];orbit=sweep['rotating-gallop']
    summary=table(['表示・128層指定','1体','10体','50体','100体'],[[pname+' / '+methods[m],*[f"{row(p,m,n)['fps']:.2f}" for n in (1,10,50,100)]] for p,pname in [('desktop-1x','PC幅'),('mobile-4x','スマホ幅')] for m in ('v1','lod')])
    html=f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>S–01 v2 · 造形と群走の採用判定</title><style>
*{{box-sizing:border-box}}body{{max-width:1320px;margin:auto;padding:26px clamp(14px,4vw,55px) 60px;background:#f6f6ee;color:#26352b;font:16px/1.65 system-ui,sans-serif}}a{{color:#285c48}}h1{{font-size:clamp(33px,5vw,60px);margin:12px 0;line-height:1.1;letter-spacing:-.04em}}h2{{font-size:25px;margin:32px 0 8px}}p{{margin:8px 0 14px}}.verdict{{display:inline-block;padding:3px 10px;background:#a94826;color:white;border-radius:3px}}img,video{{width:100%;height:auto;display:block}}figure{{margin:12px 0}}figcaption,small{{font-size:13px;color:#4e6051}}.films{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px}}.table{{overflow-x:auto;margin:10px 0 18px}}table{{border-collapse:collapse;width:100%;font:14px/1.35 system-ui,sans-serif;font-variant-numeric:tabular-nums}}th,td{{padding:7px 9px;text-align:right;white-space:nowrap;border-bottom:1px solid #cdd7c9}}th{{background:#dbe5d8}}th:first-child,td:first-child{{text-align:left}}tbody tr:nth-child(odd){{background:#fbfcf6}}details{{margin:10px 0}}summary{{cursor:pointer;font-weight:650}}code,pre{{font-family:ui-monospace,monospace}}pre{{background:#27362c;color:#f1f3ea;padding:14px;overflow:auto}}</style>
<a href="../index.html">v2 観察室</a>　<a href="../../index.html">v1 観察室</a><h1>Sprint Morph · v2</h1>
<p><b class="verdict">REVISE</b>　遠景群走のLODを継続採用。レース標準への採用は保留。</p>
<p>頭冠の左右それぞれが全25姿勢で連結し、正面・背面で隠れる下脚が減った。全景100体を128層指定で走らせたPC幅の標本計測は、v1の {row('desktop-1x','v1',100)['fps']:.2f} fpsから {row('desktop-1x','lod',100)['fps']:.2f} fpsに改善。同じ100体をコース旋回中に測るとPC幅の全景で {course[1]['fps']:.2f} fps、手前を拡大した近遠混在で {course[3]['fps']:.2f} fps。</p>
{summary}
<h2>基準画と5方向</h2><figure><a href="comparison.png"><img src="comparison.png" alt="基準画・v1・v2を同じ向きで比較"></a><figcaption>v1/v2は同一の静止姿勢、カメラ、縮尺。上面の全身はv1の推定を継承。白い肩・腿、青いCue Band、頭冠と尾羽は元の作画を使用した。</figcaption></figure>
<p>側面の輪郭IoUは {views['side']:.3f}、斜め45°は {views['quarter']:.3f}。正面・背面で脚の外側と内側の軌道を分けた。下表は下脚44層で、各脚を単独投影した面積に対して他の脚に隠れずに見える面積の比率。全25姿勢×4脚の最小値を示す。</p>
{table(['可視率の下限','v1','v2'],legs)}
<p>頭冠だけを対象に面が接する6近傍で調べると、v1の成分数は {min(x['v1_crest_components_6'] for x in morph)}～{max(x['v1_crest_components_6'] for x in morph)}、v2は全姿勢で2。原画の細い中心線をポーズ変換した後に断面の段差を接続した。俯角12°で2°ずつ一周させ、輪郭の上25%で1コマだけ反転する画素の割合は {appearance['v1']['coverage_reversal_fraction']*100:.2f}% → {appearance['v2']['coverage_reversal_fraction']*100:.2f}%、単発の輝度反転は255段階で {appearance['v1']['mean_luma_reversal_255']:.1f} → {appearance['v2']['mean_luma_reversal_255']:.1f}。近景には4サンプル被覆も適用した。細い輪郭の画素変化は残る。<a href="morphology.json">部位の検査値</a> / <a href="appearance.json">画面上の検査値</a></p>
<h2>走行・回転・切替</h2><div class="films">{''.join(f'<figure><video controls playsinline preload="metadata" src="{k}.mp4"></video><figcaption>{name}</figcaption></figure>' for k,name in [('gallop','四足走行 · 側面、正面、背面'),('turntable','24ポーズの走行を360°回転'),('lod-transition','左は128層、右は距離LOD。同時刻・同一投影。')])}</div>
<p>積層の支持脚を個別に追跡し、足裏の最低断面の重心が支持ポーズの間にワールド座標で動いた距離を測った。24ポーズのP95は直線で {stance['v1']['24-straight']['p95']:.2f} → {stance['v2']['24-straight']['p95']:.2f}、半径1750のカーブで {stance['v1']['24-bend']['p95']:.2f} → {stance['v2']['24-bend']['p95']:.2f}（側面作画の単位、長手1テクセル＝3）。各支持区間を8分割し、着地姿勢をまたぐ転がりも含む。<a href="stance.json">12・24ポーズの接地評価</a></p>
<p>遠景は同じ128層の色・深度・被覆から作った48方位×10俯角×25姿勢。支持脚の補正と向きは積層と共有する。正投影の画面占有幅に視線方向の距離補正を加えて切り替え、切替帯は画素を相補的に割り当てる。頭冠や遠側の足先には角度量子化と半透明縁の差がある。</p>
{table(['投影幅 px','輪郭IoU 最小','輪郭IoU 中央','重心差 最大 px','色差 中央 /255'],boundary)}
<p>上表は7方位×5俯角、同じ走行ポーズの全積層とスプライトの対。連続ズームでは投影幅72～160 pxを81画面で横断し、積層との差を差し引いた余分な重心移動は最大 {max(r['extra_motion_px'] for r in cv):.2f} px。走りながらの遠景360°では最大 {max(r['extra_motion_px'] for r in orbit):.2f} px、輪郭IoUの最小は {min(r['iou'] for r in orbit):.3f}。重心差が小さくても、細片のすべてが一致するわけではない。<a href="sweep.json">全261画面</a></p>
<h2>ボトルネック</h2><p>旧版のPC幅・128層・100体で、床・影・ポーズ別の呼び出しを保持して積層の個体数だけを変えた。全個体は約{ab[0]['last_runner_triangles']/1e4:.0f}万三角形で {ab[0]['draw_sync_ms']:.1f} ms、各ポーズ1体で {ab[1]['draw_sync_ms']:.1f} ms、個体の三角形を除くと {ab[2]['draw_sync_ms']:.1f} ms。Workerは読み込み時にメッシュを作る。群走中に増えていたのは主に同じ面を個体数分処理するGPU負荷だった。<a href="bottleneck.json">切り分け計測</a></p>
<h2>カーブ追走と旋回</h2><p>24ポーズ、俯角12°、カメラは毎秒40°旋回。コース上の影・床・個体を毎フレーム更新した。全景は倍率1×、近遠混在は開始時の体長が約122 pxになる倍率（上限7×）。個体はすべてシミュレートし、ズーム時は画面の外に完全に出た個体の本体を描画対象から外す。内訳はフレーム間の各中央値。</p>
{table(['表示','カメラ','総体数','倍率','fps','p95 ms','同期込 ms','積層 / 移行 / 2D / 画面外'],arc)}
<p><a href="course-measurement.json">各フレームの間隔と内訳</a> / <a href="crowd.png">100体コースの実画面</a></p>
<h2>同条件の全計測</h2><p>Chromium {read('v1-measurement.json')['chromium']} / ANGLE・SwiftShader。PCは1280×900・描画877×414・CPU 1×、スマホ幅は390×844・描画352×335・CPU 4×。物理スマートフォンは未測定。v1の既報1.80 fpsと今回の再計測は別の実行。性能表は全方式で同じカメラ、位相分布、24ポーズと1画素の同期読出しを使った。3フレーム予熱後、1.2秒以上かつ5フレーム以上の単回計測。高負荷のp95は少数標本。</p>
<p>「発行」はJSの描画呼び出し時間。「同期込」は描画開始から読出し終了まで。「GPU」は有効なEXT_disjoint_timer_query_webgl2による描画区間。p95は表示フレーム間隔。三角形・drawは最終計測フレームで実際に発行した値（床・影を含む）。Framebuffer転送はCSVのblits列。全景の標本比較は全個体が画面内に収まる。</p>
<details open><summary>128層指定 · 24条件</summary>{measurements(128)}</details><details><summary>64層指定 · 24条件</summary>{measurements(64)}</details>
<p>JSはCDPの使用ヒープ。GLはメッシュバッファ、ロード中の角度の色・深度テクスチャ、床キャッシュ、近景MSAAの主な論理割当量。ドライバの実VRAM総量は未計測。RSSは128層の別実行でChromeの各プロセスのVmRSSを合算し、共有ページが重複しうる。64層はJS・GL割当を収録した。スマホ幅のほうが描画面積は小さい。<a href="performance.csv">48条件CSV</a> / <a href="memory.json">RSS内訳</a></p>
<h2>採用判断</h2><p><b>群走の遠景LODはKEEP、レース標準はREVISE。</b> 全景では走行位相と17色の作画を保って大幅に高速化した。手前に積層が集まると、近景の被覆計算と切替帯で両方を描く負荷が増える。PC幅の128層・10体の標本ビューは {row('desktop-1x','lod',10)['fps']:.2f} fps。全景100体の値だけでレース標準を承認しない。<a href="ui.json">操作試験</a> / <a href="desktop.png">PC画面</a> / <a href="mobile.png">タッチ画面</a></p>
<h2>再現</h2><pre>git switch exp/s-pixel-stacking-zero-20261121
python3 -m http.server 4173 --bind 127.0.0.1 --directory public
# http://127.0.0.1:4173/s-pixel-lab/v2/index.html</pre><p>リポジトリ内の <code>scripts/s-pixel/v2/README.md</code> に作画、ベイク、動画・計測の全コマンドを記載した。</p></html>'''
    (D/'review.html').write_text(html)
if __name__=='__main__':main()
