"""Update the static review with the measured data from this build."""
from pathlib import Path
import csv,json,zipfile
from html import escape
from bake import OUT,ROOT,SOURCE,PARTS
D=OUT.parent;E=D/'evidence'
def main():
    result=json.loads((E/'performance.json').read_text())
    rows=result['rows'];assert len(rows)==32
    q=json.loads((E/'quality.json').read_text())
    qa=json.loads((E/'qa.json').read_text())
    def rate(profile,n,c):return next(f"{r['fps']:.2f}" for r in rows if r['profile']==profile and r['layers']==n and r['count']==c)
    table=''
    for profile,label in [('desktop-1x','PC幅'),('mobile-viewport-4x','スマホ幅')]:
        for n in [16,32,64,128]:
            table+='<tr><td>'+label+'</td><td>'+str(n)+'</td>'+''.join('<td>'+rate(profile,n,c)+'</td>' for c in [1,10,50,100])+'</tr>'
    diagnostics=''
    for group in qa['artifacts']:
        n=group['layers'];c=q['connectivity'][str(n)];a=group['rotation'][1]
        diagnostics+=f"<tr><td>{n}</td><td>{max(f['islands'] for f in c)}</td><td>{max(f['loose_texels'] for f in c)}</td><td>{a['reversal_fraction']*100:.2f}%</td><td>{a['peak_fraction']*100:.2f}%</td></tr>"
    straight=q['contact']['24-straight'];bend=q['contact']['24-bend']
    prior='https://github.com/badjoke-lab/evowild-test/blob/e002736b22f91b9a020109e0a251b6042544915d/docs/experiments/sprite-stacking/README.md'
    html=f"""<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>S–01 採用判定 | EvoWild Run</title><style>
    *{{box-sizing:border-box}}body{{margin:auto;padding:30px 18px 65px;max-width:1000px;color:#26332d;background:#f5f6ed;font:16px/1.7 system-ui,sans-serif}}a{{color:#235e56}}h1{{font-size:clamp(36px,6vw,58px);line-height:1.1;margin:18px 0}}h2{{margin:34px 0 8px;font-size:25px}}h3{{margin-bottom:4px}}img,video{{max-width:100%;height:auto}}figure{{margin:14px 0}}figcaption,small{{font-size:13px;color:#465448}}table{{width:100%;border-collapse:collapse;background:#fffef9;font-variant-numeric:tabular-nums;font-size:14px}}th,td{{padding:6px;border-bottom:1px solid #ced4c8;text-align:right}}th:first-child,td:first-child{{text-align:left}}th{{background:#dce4d9}}pre{{background:#26332d;color:white;padding:12px;overflow:auto}}code{{overflow-wrap:anywhere}}.tag{{background:#a94a26;color:white;padding:3px 8px;border-radius:2px}}.media{{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:10px}}p{{margin:6px 0 12px}}li{{margin-bottom:7px}}</style>
    <a href="../index.html">← 観察室</a><h1>Sprint Morph</h1><p><b class="tag">REVISE</b>　S型レースへの採用は保留。</p>
    <p>原画の白い肩・臀部、暗い胸郭、長い左右の頭冠、青いCue Band、割れた足先と尾の羽片を新規作画し、同じ個体を24ポーズで走らせた。横と斜めではこれらを追える。真正面では頭冠の先が細く分断して見え、走行中に同側の脚が重なる。100体での速度も採用を見送る理由になった。</p>
    <figure><a href="comparison.png"><img src="comparison.png" alt="指定原画、5方向の128層描画、旧実験の側面"></a><figcaption>上段は原画の該当箇所、中段はWebGL実描画。上面の全身は側面の長さ、前後の肩幅・腰幅、尾の上面詳細から補った。斜め45°の実描画を原画の3/4図と照合した。</figcaption></figure>
    <div class="media">{''.join(f'<figure><video controls playsinline preload="metadata" src="{f}.mp4"></video><figcaption>{label}</figcaption></figure>' for f,label in [('turntable','静止姿勢・360°'),('gallop','四足走行・後半はカーブを追従'),('camera','走行中に低角から上面へ')])}</div>
    <p>動画はデモのWebGLフレームバッファを決定的な時刻で読み出し、24 fpsで符号化した。実時間の処理速度は下表で別に計測した。</p>
    <h2>造形と断面</h2><p>造形原本は <code>48b39d8 / art/s-creature/references/00_s_type_modeling_image_v1.png</code>。原本を開いてSHA256 <code>{SOURCE}</code> を照合した。全{len(PARTS)}部位の側面クラスター、上面の幅と稜線、正面・背面の輪郭と色面を17色＋透明で作画した。原画の画素や既存GLBの頂点を素材生成器へ読み込む工程はない。</p>
    <p>部位ごとに4枚の登録済みPNGから輪郭を交差させ、上面幅に合わせて角を丸め、各方向の色を転写する。隠れた面の厚みは推定値。関節の移動後に高さ帯ごとの断面を焼き、薄い先端は帯内で中央に近い有色画素を残す。Web Workerが実際の断面PNGから外面だけを組み、同色の隣接面を結合する。上下と側壁が高さ帯を埋め、深度バッファで前後を解決する。45°画像と方向サムネイルは検証用。</p>
    <p>4方向の作画レイヤー　<a href="../assets/drawings/side-parts.png">側面</a> / <a href="../assets/drawings/front-parts.png">正面</a> / <a href="../assets/drawings/rear-parts.png">背面</a> / <a href="../assets/drawings/top-parts.png">上面</a>。<a href="../assets/drawings/parts.json">部位順</a>は8列・左上から。<a href="../assets/stack-128/run-00.png">断面アトラス例</a>の高さ・トリム位置は<a href="../assets/manifest.json">manifest</a>に保存した。</p>
    <figure><a href="layer-study.png"><img src="layer-study.png" alt="同じ走行姿勢と俯角6度での4層数比較"></a><figcaption>高さ帯が厚い16・32層では頭冠と蹴り出し脚の階段が目立つ。64・128層では側面の色面を追いやすい。</figcaption></figure>
    <h2>接地と走行</h2><p>12ポーズを偶数番に焼き、同じ運動曲線から中間12ポーズを追加した。4脚ごとに接地の開始、支持、蹴り出し、回収をずらし、肩の滑走、骨盤、胸のピッチ、身体の上下動に連動させた。足先の軌道では第20～23コマが全脚の空中局面。128層の実断面では、第20・23コマの足先が最下帯に残り、足全体が離れるのは第21・22コマ（地上3.625、7.25作画単位）。足先位置を求めてから関節を解き、標本画面ではその場走行、コースでは直線と半円を移動する。</p>
    <figure><a href="gait-cycle.png"><img loading="lazy" src="gait-cycle.png" alt="走行1周期24コマ"></a></figure>
    <p>支持脚の下部をポーズ間の前進量だけ進行と逆向きにずらす。128層の足裏帯の重心を使い、連続する支持ポーズを8分割して区間開始からのワールド座標差を評価した。単位は側面作画座標で長手1テクセル＝3。24ポーズ・直線のP95は補正前 {straight['uncorrected_displacement']['p95']:.2f} → 補正後 {straight['corrected_displacement']['p95']:.2f}、半径1750のカーブでは {bend['uncorrected_displacement']['p95']:.2f} → {bend['corrected_displacement']['p95']:.2f}。接地アンカーと描画される足裏重心は足先の転がりで異なる。12ポーズ、最大値、標本数は <a href="quality.json">quality.json</a> に収録した。</p>
    <h2>欠け・ちらつき</h2><p>静止＋走行の25姿勢に対して、PNGの有色テクセルを26近傍で連結判定した。独立片は最大連結成分の外にある塊。回転時は静止姿勢を2°刻みで一周し、隣接する3画面の中央だけ占有状態が反転する画素の割合を合併シルエット面積に対して求めた。下表は俯角15°。細い正常な輪郭の横切りも含まれるため、この指標だけでちらつきの合否は決めていない。</p>
    <table><tr><th>層</th><th>独立片数 最大</th><th>独立テクセル 最大</th><th>単発反転 全周</th><th>最悪角</th></tr>{diagnostics}</table><p><a href="qa.json">俯角3°・15°・60°の全検出値と操作結果</a></p>
    <h2>描画性能</h2><p>表は実測fps。Chromium {escape(result['browser'])}、同一クラウドCPU・SwiftShader。PC幅1280×900 / モバイル幅390×844・タッチ入力・CPU 4倍スロットル。内部描画面積が異なる。スマートフォン実機GPUでの値は未測定。</p>
    <table><tr><th>表示</th><th>層</th><th>1体</th><th>10体</th><th>50体</th><th>100体</th></tr>{table}</table>
    <p>同じ24ポーズの標本走行を位相をずらして全体表示。3フレームの予熱後、各条件1回、1.2秒以上かつ5フレーム以上。各フレーム1画素の同期読出しを含む。高負荷条件は少数標本。<a href="performance.csv">CSV</a> / <a href="performance.json">全フレーム間隔、p95、三角形数、レンダラー</a> / <a href="course-100.png">100体の走行画面</a></p>
    <h2>旧実験との比較と採用判定</h2><ul>
    <li><b>造形・色面</b>　旧版は無彩色のD3-C v2を切断した。今回の白・紺・青とCue BandでS型の横顔、肩、尾の読み取りが改善した。原画より正面の胸の面分けが硬く、斜めで頭冠の縁にまだざらつきがある。</li>
    <li><b>旋回・カメラ</b>　旧版の薄い水平面は低俯角で板間の空間が露出した。今回の側壁付き断面は水平から真上まで厚みを保つ。低層数では頭冠や足の厚みを過大に描き、128層でも小さな独立片が残る。</li>
    <li><b>走行・接地</b>　旧版は既存の48ポーズIKを使った。今回の独立した4脚と支持脚補正で直線・旋回を走行できる。後方・真正面の左右重なり、着地時の量子化、平面以外での接地は解決していない。</li>
    <li><b>負荷</b>　既報のWebGL・64層・24ポーズ・1体はPC幅60.2 fps、モバイル幅60.0 fps。今回の同じ層・ポーズ・体数は {rate('desktop-1x',64,1)} / {rate('mobile-viewport-4x',64,1)} fps。旧計測はGPU同期読出しを課しておらず、画面寸法と描画内容も異なる。倍率の直接比較はできない。今回の50・100体ではポリゴン処理量が大きい。</li></ul>
    <p><b>近景16・32層はREJECT。64・128層と総合はREVISE。</b> 少数体の検証を続ける。製品採用には頭冠・尾端の孤立、正面の読みやすさ、実機での群走性能の改善・確認が必要。<a href="{prior}">旧実験の判定と計測条件</a> / <a href="previous-side.png">旧版の実画像</a></p>
    <h2>再現</h2><p>配布ZIPを展開して <code>python3 start-demo.py</code> を実行するとブラウザが開く。WebGL 2対応ブラウザを使用。作業ブランチから直接起動する場合は次の手順を使う。</p>
    <pre>git switch exp/s-pixel-stacking-zero-20261121
python3 -m http.server 4173 --bind 127.0.0.1 --directory public
# http://127.0.0.1:4173/s-pixel-lab/</pre>
    <p>作画・動画・数値の再生成コマンドはリポジトリの <code>scripts/s-pixel/README.md</code>。ブラウザ確認画面　<a href="desktop.png">PC</a> / <a href="mobile.png">モバイル幅</a>。</p></html>"""
    (E/'review.html').write_text(html)
if __name__=='__main__':main()
