"""Render the web decision sheet from the committed browser measurements."""
import json
from pathlib import Path
from statistics import mean

D=Path(__file__).resolve().parents[3]/'public/s-pixel-lab/v3/evidence'
def read(file):return json.loads((D/file).read_text())
def table(headers,rows):
    heads=''.join(f'<th>{x}</th>' for x in headers)
    cells=''.join('<tr>'+''.join(f'<td>{x}</td>' for x in row)+'</tr>' for row in rows)
    return f'<div class="scroll"><table><thead><tr>{heads}</tr></thead><tbody>{cells}</tbody></table></div>'
def link(url,title):return f'<a href="{url}">{title}</a>'

def main():
    raw={v:read(f'{v}-race.json') for v in ['v2','v3']};rows={(v,r['profile'],r['scenario']):r for v,data in raw.items() for r in data['rows']}
    names={'near1':'近景 1体','near10':'近景 10体','mixed50':'混在 50体','mixed100':'混在 100体','overview100':'全景 100体'}
    performance=[];distribution=[];summary=[]
    for p,label in [('desktop','PC幅'),('mobile','スマホ幅')]:
        for v in raw:summary.append([label+'・'+v,*[f"{rows[v,p,k]['fps']:.2f}" for k in names]])
        for key,name in names.items():
            for v in raw:
                r=rows[v,p,key];m=r['memory'];performance.append([label,name,v,f"{r['fps']:.2f}",f"{r['p95_ms']:.1f}",f"{r['gpu_ms']:.2f}",f"{r['draw_sync_ms']:.2f}",f"{r['triangles']['mean']:,.0f}",f"{r['draw_calls']['mean']:.1f}",f"{m['gl_mib']:.1f}",f"{m['js_heap_mib']:.1f}",f"{m['rss_mib']:.0f}"])
            r=rows['v3',p,key];distribution.append([label,name,*[f"{r['mix'][kind]['mean']:.1f}" for kind in ('near','mid','transition','sprite','offscreen')],f"{r['visibility']['centre']['min']}–{r['visibility']['centre']['max']}"])
    geom=read('greedy.json');ap=read('appearance.json');faces=read('facing-check.json');changed=read('regeneration-probe.json');variants=read('variants.json');exact=read('exact-check.json');levelmeta=json.loads((D.parent/'assets/surface/index.json').read_text());env=raw['v3']['environment']
    films=[('turntable','360°回転'),('gallop','四足走行・24姿勢'),('lod-transition','128層とLOD・同一カメラ'),('near10','近景10体'),('mixed50','混在50体'),('mixed100','混在100体')]
    clips=''.join(f'<figure><video controls playsinline preload="none" src="{f}.mp4"></video><figcaption>{title}　{link(f+".mp4","MP4")}</figcaption></figure>' for f,title in films)
    perpart=table(['全24姿勢×5方向','メッシュ IoU中央値','実際のLOD IoU中央値','実際のLOD IoU最小値'],[[name,f"{ap['gait']['summary'][k]['iou_median']:.3f}",f"{ap['gait_lod']['summary'][k]['iou_median']:.3f}",f"{ap['gait_lod']['summary'][k]['iou_min']:.3f}"] for k,name in [('body','全身'),('crest','頭冠を含む上端'),('feet','足先を含む下端'),('tail','尾の末端')]])
    geomtable=table(['メッシュ','三角形/体 最小–最大','原本占有体積に対する比率'],[[level,f"{min(q['levels'][level]['indices']//3 for q in levelmeta['poses']):,}–{max(q['levels'][level]['indices']//3 for q in levelmeta['poses']):,}",f"{min(q['levels'][level]['volumeRatio'] for q in levelmeta['poses'])*100:.1f}–{max(q['levels'][level]['volumeRatio'] for q in levelmeta['poses'])*100:.1f}%"] for level in levelmeta['levels']]); old=rows['v2','desktop','mixed100'];cur=rows['v3','desktop','mixed100'];nr=rows['v3','desktop','near10']
    variants_table=table(['条件','変更点','フレーム','fps','GPU ms','三角形/フレーム'],[[names[r['scenario']],{'all-faces':'全表面インデックス','facing':'視線方向で背面を除外','hero-0':'単体・追加MSAAなし','hero-2':'単体・2サンプル要求','hero-4':'単体・4サンプル要求','ray-1':'原本のレイ描画','ray-10':'原本のレイ描画'}[r['id']],r['frames'],f"{r['fps']:.2f}",f"{r['gpu_ms']:.2f}",f"{r['triangles']['mean']:,.0f}"] for r in variants]); flick=ap['turntable_flicker'];switch=ap['switch'];audit=geom[0];films_info=read('films.json')
    html=f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>S–01 v3 · レース標準の採用判定</title><style>
*{{box-sizing:border-box}}body{{background:#f6f6ef;color:#203229;max-width:1340px;margin:auto;padding:28px clamp(15px,4vw,55px) 60px;font:16px/1.62 system-ui,sans-serif}}a{{color:#286146}}nav{{display:flex;gap:20px}}h1{{font-size:clamp(36px,5.6vw,68px);line-height:1.05;letter-spacing:-.045em;margin:22px 0 12px}}h2{{margin:35px 0 8px;font-size:26px}}p{{margin:9px 0 14px}}.decision{{color:#803921;background:#f4d6c4;padding:2px 9px;border-radius:3px}}.scroll{{overflow:auto;margin:12px 0 20px}}table{{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}}td,th{{white-space:nowrap;text-align:right;border-bottom:1px solid #cad5c9;padding:6px 9px}}th{{background:#dae6da}}td:first-child,th:first-child{{text-align:left}}img,video{{width:100%;display:block;background:#23362b}}figure{{margin:12px 0}}figcaption{{font-size:14px}}.clips{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}}video{{aspect-ratio:11/6}}code,pre{{font-family:ui-monospace,monospace}}pre{{overflow:auto;background:#23362b;color:#f6f6ed;padding:12px}}details{{margin:14px 0}}summary{{cursor:pointer;font-weight:650}}</style>
<nav>{link('../index.html','v3 操作デモ')}{link('../../v2/index.html','v2 観察室')}{link('../../index.html','v1 観察室')}</nav><h1>Voxel Race Lab / S–01</h1><p><b class="decision">REVISE</b>　共通原本と近景描画は継続採用。近景を含む群走のレース標準は保留。</p>
<p>PC幅で10体すべてが近景に映るカーブ走行は平均 {nr['fps']:.2f} fps。100体の混在走行はv2の {old['fps']:.2f} fpsから {cur['fps']:.2f} fpsに改善したが、目標30 fpsを下回った。同条件のGPU時間は {old['gpu_ms']:.1f} msから {cur['gpu_ms']:.1f} ms、p95フレーム時間は {old['p95_ms']:.1f} msから {cur['p95_ms']:.1f} ms。全景だけでは判定していない。</p>
{table(['平均fps',*names.values()],summary)}
<h2>近景・中景・遠景の実測</h2><p>全条件で走行、コースの曲がり、カメラ旋回、俯角と倍率の変化を同時に与えた。v2・v3の全48フレームの姿勢時刻、方位、俯角、倍率、画面寸法を突き合わせた。PCは1280×900・描画877×414。スマホ幅は390×844・描画352×335・CPU 4倍減速のタッチエミュレーション。物理スマホは未計測。</p>
{table(['表示','条件','版','fps','p95 ms','GPU ms','同期込 ms','三角形','draw','GL MiB','JS MiB','RSS MiB'],performance)}
<p>Chromium {env['chromium']}、ANGLE / SwiftShader、DPR 1。3フレームの予熱後、各RAFで1画素を同期読出し。GPU列はEXT_disjoint_timer_query_webgl2の経過時間。三角形とdrawは床・影込みのフレーム平均。GLは実際のバッファ・テクスチャ・レンダーバッファの論理割当、RSSはChromeのプロセス和で共有ページの重複を含む。速度は定常状態を評価した。{link('race-performance.csv','20条件CSV')} ／ {link('v2-race.json','v2 生データ')} ／ {link('v3-race.json','v3 生データ')}</p>
<details><summary>実際の描画内訳と画面内の個体数</summary>{table(['表示','条件','近','中','移行','遠','画面外','中心が画面内（最小–最大）'],distribution)}</details>
<h2>原本とメッシュ</h2><p>静止1姿勢、走行24姿勢の原本は17色＋透明の整数格子。原本から再生成した各姿勢の64/128層はv2と全セルの色・占有位置が一致した。128層から原本への復元でも差分0。48方位×10俯角×25姿勢の遠景は、入力・生成コード・ページのハッシュを確認してv2と共有する。一時原本の静止姿勢だけで色番号を交換する検査では、{changed['idleChangedViews']}方向に色差が現れ、走行24姿勢の色差と深度ページの差はいずれも0。{link('../assets/voxels/index.json','原本・形式・SHA256')} ／ {link('voxel-roundtrip.json','往復検証')} ／ {link('regeneration-probe.json','再生成検証')}</p>
<p>静止姿勢の色付きGreedy Meshingは {audit['stackQuads']:,} 四角形。閉じた空洞の面を捨てて {audit['outsideColorQuads']:,}、色を別テクスチャに分離して2方向の走査から長方形を選ぶと {audit['dualScanQuads']:,}。近景には原本の外表面から頭冠・四脚・尾の端点を拘束して簡略化したメッシュを使用し、色は原本から引く。48方位の遠景にはv2の深度スプライトを使用する。{link('greedy.json','25姿勢の面数')}</p>{geomtable}
<p>全姿勢の頂点を共有バッファ化し、同じ姿勢・LOD・視線区間の個体をインスタンス描画する。視線区間の全域、かつ支持脚補正の両端で裏を向く三角形を発行前に除外した。完全な面リストと比べた{faces['frames']}画面で変化した画素は {faces['changedPixels']:,}、最大色差は {faces['maxChannelDelta']}/255。レースでは追加MSAAを外し、拡大した単体標本と積層比較にはサンプル被覆を使用する。{link('facing-check.json','背面除去の画素検査')}</p>
<details><summary>背面除去、アンチエイリアス、原本レイ描画の比較</summary>{variants_table}<p>いずれもPC幅。サンプル数はWebGLに要求した値。原本レイ描画は疎なブロックごとにセルを交差判定し深度を書き込む。5方向の単体静止で同じ単一サンプルの積層と比較した輪郭IoUは {min(r['maskIoU'] for r in exact['rows'][:5]):.3f}–{max(r['maskIoU'] for r in exact['rows'][:5]):.3f}。近景10体ではピクセルごとの交差判定が重く、標準LODには軽量メッシュを選んだ。{link('exact-check.json','原本レイ画素比較')} ／ {link('variants.json','追加計測')}</p></details>
<h2>造形と走行</h2><a href="comparison.png"><img src="comparison.png" alt="指定基準画・v2・v3積層・v3表面メッシュの5方向比較"></a><p>比較は同じ姿勢・画角・縮尺。元の設計画に上面の全身はなく、尾の資料を示した。各画面の上25%を頭冠域、下18%を脚先域、横向きの端18%を尾域として計測した。これらは画面領域で、解剖学的な部位の切り抜きとは異なる。</p>{perpart}
<p>体長156 pxで2°ずつ360°回転したとき、頭冠域で1コマだけ有無が反転した割合はv2積層 {flick['v2-stack']['crest']['fraction']*100:.2f}%、v3距離LOD {flick['v3-lod']['crest']['fraction']*100:.2f}%。脚先域は {flick['v2-stack']['feet']['fraction']*100:.2f}%、{flick['v3-lod']['feet']['fraction']*100:.2f}%。手前・遠方を連続でまたぐ73フレームの輪郭IoU中央値 {switch['summary']['body']['iou_median']:.3f}、積層との差を差し引いたフレーム間重心移動は最大 {switch['max_extra_centroid_motion_px']:.2f} px。小さい頭冠・足先の被覆と近遠混在時のフレーム時間が残る課題である。{link('gait-24.png','全24ポーズ')} ／ {link('lod-study.png','切替の比較図')} ／ {link('appearance.json','画素計測')} ／ {link('ui.json','操作・急な俯角変更')}</p>
<h2>走行映像</h2><p>回転、24姿勢、切替比較の3本は時刻指定の24 fps。近景10体・混在50体・混在100体は実時間のカーブ走行録画で、遅い描画は映像でもその時間だけ保持している。録画時の固有描画回数は順に {films_info['near10']['unique_draws']}、{films_info['mixed50']['unique_draws']}、{films_info['mixed100']['unique_draws']}。{link('films.json','録画時刻とLODの内訳')}</p><div class="clips">{clips}</div>
<h2>再現</h2><pre>git switch exp/s-pixel-stacking-zero-20261121\npython3 -m http.server 4173 --bind 127.0.0.1 --directory public</pre><p>ローカルの <code>/s-pixel-lab/v3/index.html</code> を開く。生成と計測の全コマンドはリポジトリの {link('https://github.com/badjoke-lab/evowild-test/blob/exp/s-pixel-stacking-zero-20261121/scripts/s-pixel/v3/README.md','再現手順')}。</p></html>'''
    (D/'review.html').write_text(html)

if __name__=='__main__':main()
