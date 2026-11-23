"""Summarize matched race samples. Keep per-run and pooled results distinct."""
import csv
import json
import math
from pathlib import Path
from statistics import mean

out = Path(__file__).resolve().parents[3] / 'public/s-pixel-lab/v4.1/evidence'
versions = ('v4', 'v4.1')


def load(stem):
    return json.loads((out / (stem + '.json')).read_text())


def p95(values):
    return sorted(values)[math.ceil(.95 * len(values)) - 1]


def avg(samples, key):
    return mean(s[key] for s in samples)


def write_csv(name, rows):
    with (out / name).open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys(), lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: round(v, 4) if isinstance(v, float) else v for k, v in row.items()})


runs = {v: [load(f'{v}-round{i}') for i in (1, 2, 3)] for v in versions}
samples = {}
performance = []
for old, new in zip(*runs.values()):
    for a, b in zip(old['rows'], new['rows'], strict=True):
        for field in ('profile', 'scenario', 'width', 'height', 'cpu', 'number', 'frames', 'method'):
            assert a[field] == b[field]
        assert a['frames'] == len(a['samples']) == len(b['samples']) == 48
        for first, second in zip(a['samples'], b['samples']):
            assert all(first[k] == second[k] for k in ('camera', 'visible'))
            assert first['mix']['offscreen'] == second['mix']['offscreen']
            for shot in (first, second):
                assert sum(shot['mix'][k] for k in ('near','mid','transition','sprite','offscreen')) == a['number']
for ver in versions:
    for index in range(4):
        rows = [run['rows'][index] for run in runs[ver]]
        first = rows[0]
        for label, group in [('all', rows), *((str(i+1), [r]) for i,r in enumerate(rows))]:
            shots = [s for r in group for s in r['samples']]
            dt = [s['interval_ms'] for s in shots]
            if label == 'all':
                samples[ver, first['profile'], first['scenario']] = shots
            performance.append(dict(version=ver, profile=first['profile'], case=first['scenario'],
                raster=f"{first['width']}x{first['height']}", cpu=first['cpu'], run=label,
                frames=len(shots), fps=1000/mean(dt), p95_ms=p95(dt), mean_ms=mean(dt),
                gpu_ms=avg(shots,'gpu_ms'), submit_ms=avg(shots,'submit_ms'), sync_ms=avg(shots,'sync_ms'),
                calls=avg(shots,'calls'), triangles=avg(shots,'triangles'),
                visible_min=min(s['visible']['intersects'] for s in shots),
                visible_max=max(s['visible']['intersects'] for s in shots),
                gl_allocated_mib=mean(r['memory']['gl_mib'] for r in group)))
write_csv('performance.csv', performance)

tails = []
pass_rows = []
for ver in versions:
    shots = samples[ver, 'desktop', 'mixed100']
    ranked = sorted(enumerate(shots), key=lambda pair: -pair[1]['interval_ms'])
    for bucket, part in [('slowest8',ranked[:8]),('other136',ranked[8:])]:
        group = [x for i,x in part]
        tails.append(dict(version=ver, group=bucket, frames=len(part), interval_ms=avg(group,'interval_ms'),
            gpu_ms=avg(group,'gpu_ms'), submit_ms=avg(group,'submit_ms'), sync_ms=avg(group,'sync_ms'),
            outside_draw_ms=mean(s['interval_ms']-s['sync_ms'] for s in group),
            phase10_14=sum(10<=i%48<=14 for i,s in part)))
    for case in load(ver+'-passes'):
        for component in ('mesh','floor','shadow','sprites'):
            vals=[s[component+'_gpu_ms'] for s in case['samples']]
            pass_rows.append(dict(version=ver,case=case['scenario'],component=component,
                mean_gpu_ms=mean(vals),p95_gpu_ms=p95(vals),mean_draws=case['mean'][component+'_calls']))
write_csv('tail.csv', tails)
write_csv('passes.csv', pass_rows)

coverage = []
for flag in ('all','skip'):
    group = [r for r in load('coverage-ab') if r['coverage']==flag]
    assert len(group)==3
    ss = [s for r in group for s in r['samples']]
    peak = [s for r in group for s in r['samples'][10:15]]
    coverage.append(dict(policy=flag,frames=len(ss),fps=1000/avg(ss,'interval_ms'),
        p95_ms=p95([s['interval_ms'] for s in ss]),gpu_ms=avg(ss,'gpu_ms'),
        phase10_14_gpu_ms=avg(peak,'gpu_ms'),phase10_14_triangles=avg(peak,'triangles')))
write_csv('coverage-ab.csv', coverage)

def table(headers, rows):
    head=''.join(f'<th scope="col">{h}</th>' for h in headers)
    body=''.join('<tr>'+''.join(f'<td>{cell}</td>' for cell in row)+'</tr>' for row in rows)
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


results=table(['幅','体数','版','平均 FPS','p95 ms','GPU平均 ms','描画回数 / frame','三角形 / frame'],
    [('PC' if r['profile']=='desktop' else 'スマホ', r['case'][5:],r['version'],f"{r['fps']:.2f}",f"{r['p95_ms']:.1f}",f"{r['gpu_ms']:.2f}",f"{r['calls']:.1f}",f"{r['triangles']:,.0f}")
     for r in sorted((r for r in performance if r['run']=='all'),key=lambda r:(r['profile'],int(r['case'][5:]),r['version']))])
passes=table(['版','パス','GPU平均 ms','GPU p95 ms','平均描画回数'],
    [(r['version'],dict(mesh='表面',floor='床',sprites='遠景スプライト',shadow='影')[r['component']],f"{r['mean_gpu_ms']:.2f}",f"{r['p95_gpu_ms']:.2f}",f"{r['mean_draws']:.1f}") for r in pass_rows if r['case']=='mixed100'])
tail_table=table(['版','フレーム群','平均時間 ms','GPU平均 ms','CPU送信 ms','描画・同期 ms','描画外 ms','位相10–14の件数'],
    [(r['version'], '遅い8' if r['group']=='slowest8' else '残り136',*(f"{r[k]:.2f}" for k in ('interval_ms','gpu_ms','submit_ms','sync_ms','outside_draw_ms')),r['phase10_14']) for r in tails])
ab=table(['同じv4.1表面','平均 FPS','p95 ms','GPU平均 ms','位相10–14 GPU平均 ms','位相10–14 三角形 / frame'],
    [('全移行を送信' if r['policy']=='all' else '空の描画を省略',*(f"{r[k]:.2f}" for k in ('fps','p95_ms','gpu_ms','phase10_14_gpu_ms')),f"{r['phase10_14_triangles']:,.0f}") for r in coverage])
raw_links=' · '.join(f'<a href="{v}-round{i}.json">{v} 第{i}回</a>' for v in versions for i in (1,2,3))
(out/'review.html').write_text(f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EvoWild Run｜S型 v4.1 採用試験</title><style>
*{{box-sizing:border-box}}body{{margin:auto;max-width:1080px;padding:20px clamp(14px,3vw,32px) 56px;background:#f5f4ea;color:#172d26;font:16px/1.65 system-ui,sans-serif}}h1,h2,h3{{line-height:1.3}}h2{{border-top:1px solid #a8b7ac;padding-top:20px;margin-top:36px}}a{{color:#145146}}img,video{{width:100%;height:auto;display:block;background:#dce4de}}figure{{margin:18px 0}}figcaption{{padding-top:4px;font-size:.91em}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}.scroll{{overflow:auto}}table{{background:#fff;border-collapse:collapse;white-space:nowrap}}th,td{{padding:6px 12px;text-align:right;border-bottom:1px solid #ccd4ce}}th{{background:#253d32;color:white}}td:first-child{{text-align:left}}code{{overflow-wrap:anywhere}}@media(max-width:650px){{.pair{{display:block}}}}
</style><main><a href="../index.html">レース計測デモを開く</a><h1>S型 v4.1 採用試験</h1>
<p><strong>REVISE</strong>　レースと同じ単一サンプルで頭冠の目標を達成した。混在50体・100体の平均が30fpsを下回り、遅いフレームには33.3msのフレーム予算を大きく超えるものがある。物理Android端末とGPU搭載PCでの結果は未取得。</p>
<h2>頭冠と脚先</h2><p>姿勢ごとの128層原本を基準に、同じ投影位置で輪郭の共通部分を和集合で割った。走りながら投影幅を60→262pxに変えた73時点で、頭冠の中央値はv4の0.72419から0.79575に回復した（v3基準0.763）。最低値は0.59504→0.64683。スプライトと表面が実際に重なる103–113pxは3時点で、中央値は0.72845→0.75000。全73時点には切替後の中・近景も含む。標本用4サンプルAAはこの比較で使っていない。</p>
<figure><a href="lod.png"><img src="lod.png" alt="128層原本とv4、v4.1の距離別頭冠比較"></a></figure>
<p>24姿勢の正面と背面では、原本で分離した脚先186箇所のうち、半分以上重なり別々に識別できた数は169→174。半分以上重なった数は169→175。5視点×24姿勢で足元IoUの中央値は0.75000→0.77272、最低値は0.65839→0.63871。全身の中央値は0.86135→0.84286、尾部は0.74574→0.70337。頭冠と脚先の改善に対し、胴・尾のシルエットに修正が残る。</p>
<figure><a href="feet.png"><img loading="lazy" src="feet.png" alt="正面と背面、3つの走行姿勢における脚先"></a></figure>
<figure><a href="original.png"><img loading="lazy" src="original.png" alt="S型基準原画、128層原本、v4・v4.1の5方位比較"></a></figure>
<p>近・中景の表面を既存ボクセルの外面に合わせ、頭冠の両側と脚先の支持点を保護した。量子化前に各姿勢の占有範囲に収め、足底の負座標が符号なし整数で反転する問題を修正した。17色の既存ペイント、24走行姿勢、接地補正と遠景の方位スプライトを共用する。<a href="quality.json">全時点の品質指標</a></p>
<h2>切替と実コースの走行</h2><figure><video controls playsinline preload="metadata" src="lod-switch.mp4"></video><figcaption>左 v4 ／ 右 v4.1。全73時点を往復。24fpsの固定時刻再生、6.04秒。</figcaption></figure>
<figure><video controls playsinline preload="metadata" src="mixed100.mp4"></video><figcaption>左 v4 ／ 右 v4.1。混在100体の実コースを同一の48時点で描画。3秒間の走行を16fpsで収録。</figcaption></figure>
<h3>混在50体</h3><div class="pair"><figure><a href="v4-mixed50.png"><img loading="lazy" src="v4-mixed50.png" alt="混在50体 v4"></a><figcaption>v4</figcaption></figure><figure><a href="v4.1-mixed50.png"><img loading="lazy" src="v4.1-mixed50.png" alt="混在50体 v4.1"></a><figcaption>v4.1</figcaption></figure></div>
<h3>混在100体</h3><div class="pair"><figure><a href="v4-mixed100.png"><img loading="lazy" src="v4-mixed100.png" alt="混在100体 v4"></a><figcaption>v4</figcaption></figure><figure><a href="v4.1-mixed100.png"><img loading="lazy" src="v4.1-mixed100.png" alt="混在100体 v4.1"></a><figcaption>v4.1</figcaption></figure></div>
<h2>性能と遅いフレーム</h2><p>Chromium 151 / ANGLE SwiftShader、DPR 1。PC幅は877×414、スマホ幅は352×335でCDPのCPU速度を1/4に設定。5種類の観察条件のうち採用試験は混在2条件。各回3フレームの予熱後、既存の軌道・走行位相を48時点再生。各版3回で実行順を交替した。全576組でカメラ・表示範囲・画面と交差する個体数が両版で一致。PC幅では全時点で50体／100体、スマホ幅では46–50体／87–100体が画面と交差した。</p>
<p>各フレーム末に中央1画素を同期読出し。平均FPSは全144時点の平均完了間隔の逆数、p95は昇順137番目。GPU時間はWebGL 2タイマークエリ。GL割当量、反復別の数値、元データも保存した。</p>{results}
<p><a href="performance.csv">性能CSV</a>　{raw_links}</p>
<h3>PC幅・100体のパス別GPU時間</h3>{passes}<p>独立した48時点の再生。表面と床のコストが大きい。スプライトの平均時間は増えた。各パスのp95は発生位相が異なる。<a href="passes.csv">パス別CSV</a></p>
<h3>PC幅・100体の遅い8フレーム</h3>{tail_table}<p>GPU待ちを含む描画・同期時間と、その外側の待ち時間の両方が尾を伸ばす。CPUの送信時間は小さい。v4.1で遅い8フレームは第1回に集中し、位相10–14以外でも発生した。SwiftShaderホストのスケジューリングと各パスの因果関係を個々のフレームに割り当てることはできない。<a href="tail.csv">遅延内訳CSV</a></p>
<h3>描画を省ける移行フレーム</h3><p>4×4ディザの閾値を通過する画素がない側を送信から外した。混在100体の位相10–14で毎回40個体分、全48時点で計200個体・フレーム分の空メッシュを省けた。50体では計69。画面と交差する個体数を維持した。同じ修正済み表面を使い、条件の実行順を交替して3回ずつ再生した結果を示す。</p>{ab}
<p>不可視の裏面を方位ごとに除き、収まる場合に16ビット索引を使う。静的な表面と移行中の表面でシェーダーを選び、インスタンスを1回で送る。PC幅の2条件×48時点でフル索引との比較、全ディザ描画との比較ともにRGB不一致は0画素。比較の単位は同じv4.1形状。低解像度の床や描画順変更は初期試験で改善が続かず除外した。<a href="submission-check.json">画素比較</a> · <a href="coverage-ab.csv">移行処理の対照試験</a> · <a href="trials.csv">座標修正前の探索記録</a></p>
<h2>Android／GPU搭載PCでの測り方</h2><ol><li>配布ZIPをPCで展開し、そのフォルダーで <code>python3 -m http.server 8000 --bind 0.0.0.0</code> を実行する。</li><li>PCでは <code>http://localhost:8000/</code>、同じWi-FiのAndroid Chromeでは <code>http://PCのLANアドレス:8000/</code> を開く。WebGL 2対応ブラウザを使用する。</li><li>比較する端末・版で同じ描画サイズを選ぶ。端末名を入力して「2条件を測定」を押し、前面のまま待つ。画面のFPS・p95・個体数・LOD内訳と、完了時のGPU名を確認する。</li><li>「JSONを保存」。上部のv4／v4.1で版を切り替え、各版3回、実行順を交替して保存する。端末の電源・省電力設定、ブラウザのバージョンも記録する。</li></ol>
<p>デモの通常表示は直近48フレームのライブ値。採用試験ボタンは同期読出しを使い、両版共通の決まった軌道を測る。高DPR端末でも描画バッファは選択した寸法に固定。端末のCPU倍率は変更しない。GPUタイマー非対応の端末ではGPU時間をnullとし、完了間隔とp95を保存する。ブラウザUIとJSON保存はSwiftShaderのPC・タッチ環境で検証した。</p>
</main></html>''', encoding='utf-8')
