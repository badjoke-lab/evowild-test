# EvoWild Run — Sprite Stacking 実証結果（2026-11-18）

**総合判定：REVISE（S型レースへの採用保留）。** 水平断面画像だけで立体・連続360°旋回・既存の四足走行・操作できる複数体コース走行は成立した。128層では35°の見え方が元モデルに近づく。一方、低角度の隙間、細い脚・角・尾の階段状欠損、接地の標本化誤差が残る。速度改善だけをKEEP理由にはしない。

Branch: `exp/2p5d-sprite-stacking-20261118`。main統合・本番素材変更・新規クリーチャー生成・有料サービス使用は行っていない。これは実装済みのレビュー実験であり、製品への昇格ではない。

## デモと成果物

- [通常版ブラウザデモ](../../../public/exp-sprite-stacking/index.html) — ローカルHTTPサーバーで開く。GitHubのソース表示自体では実行されない。
- [オフライン版ZIP](../../../public/exp-sprite-stacking-demo.zip) — ダウンロードして展開し、`index.html`をブラウザで開く。デモは通信・サーバー不要。動画とレポートを同梱。
- [HTML検証レポート](../../../public/exp-sprite-stacking/evidence/report.html)。ZIP内では直接開ける。
- [360°回転](../../../public/exp-sprite-stacking/evidence/rotation-360.mp4)、[四足走行](../../../public/exp-sprite-stacking/evidence/quadruped-run.mp4)、[既存方式との並列比較](../../../public/exp-sprite-stacking/evidence/parallel-comparison.mp4)、[コース走行](../../../public/exp-sprite-stacking/evidence/course-run.mp4)、[12/24/48ポーズ比較](../../../public/exp-sprite-stacking/evidence/pose-frame-comparison.mp4)。
- 5方向：[前方](../../../public/exp-sprite-stacking/evidence/comparison-front.png) / [前方3/4](../../../public/exp-sprite-stacking/evidence/comparison-front-quarter.png) / [側方](../../../public/exp-sprite-stacking/evidence/comparison-side.png) / [後方3/4](../../../public/exp-sprite-stacking/evidence/comparison-rear-quarter.png) / [後方](../../../public/exp-sprite-stacking/evidence/comparison-rear.png)。各画像は2D、GLB、16/32/64/128層の同条件比較。
- [性能CSV](../../../public/exp-sprite-stacking/evidence/performance.csv)、[全76条件・生フレーム時間JSON](../../../public/exp-sprite-stacking/evidence/performance.json)、[グラフ](../../../public/exp-sprite-stacking/evidence/performance-fps.svg)。

操作は←→ / A Dで連続旋回、↑↓ / W Sで加減速、SPACEで一時停止。タッチ操作、自由走行、自動コース追従、視点・層数・ポーズ数・1/6/18体・描画方式の切替を実装。

## 既存素材の選定と保全

main `cde1bd7`、D3-C authoring `ec969514`、full-body `8c7ad6a`、modeling `48b39d8`を調査。D3-C v2の既存23関節モデルと、既存の肩甲骨・上腕・肘・胴体制御、足裏IK、toe-rollを選定した。v3も確認したが、レビュー上の未解決点があり、指定されたv2を安定した比較元とした。元の壊れた足ウェイトや手続き形状への置換はしない。

モデルは `public/models/evowild-s/review/d3c-scapula-author-v2.glb` の不変コピー（SHA256 `6edb45e7aeb3179104d5b406d09eaa1f34da6baf09ddc9a6a0535d7e96f3f1c0`）。造形基準は指定の `art/s-creature/references/00_s_type_modeling_image_v1.png`（modeling branch `48b39d8`、SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`）。共有reference sheet/indexと2.5D lockも確認した。六つの既存制御モジュールのバイト一致は [provenance.json](../../../public/exp-sprite-stacking/evidence/provenance.json) に記録。

**素材の制約：D3-C v2とmainのcanonical GLBには、material・UV・texture image・COLOR_0がない。** 無彩色の既存レビュー形状をそのまま使用し、外側の透明度を保持した。参照画の白青テクスチャを「再利用した」とは主張しない。新しい彩色や造形を作って補っていない。元モデル自身の参照画との差と、既存走行の前脚集中・弱い胸部／骨盤連動も解決済みとはしない。

既存1600m ovalの同じ中心線と直線・カーブを、実験内で均一に0.08倍して使用。元のコースコード・既存3D/2.5D入口・本番manifestを変更していない。実装は `public/exp-sprite-stacking/` と `scripts/stacking-*` に分離。

## Phase 1 — 実際の水平断面

GLBを上から描いた画像を積み重ねる近似ではなく、スキニング後の三角形と水平面の交線を求め、断面内部を偶奇規則で埋めた。16/32/64/128の各高さ帯の中央で採取し、断面外はalpha=0、内部は元のopaque default white。透明境界の被覆率をPNGに保持し、トリミング・atlas化した。128層×48ポーズだけでなく全4条件192atlasを保存（合計11,851,908 bytes）。

比較光はクリーチャー基準のLambert（ambient .28 / diffuse .72 / light normalize(.4,.85,.35)）。GLBも同じ式・同じ正投影・同じポーズで描く。RGBAだけの断面は世界に固定された光に応じた再照明ができない。接地影は全方式で共通の楕円影であり、モデル由来の投影影・自己遮蔽の再現を承認したものではない。

| 層数 | 判定 | 5方向近似IoU | 最下段中心高 mm | 24ポーズ PNG MB | 復号RGBA MiB | PC Canvas FPS | Mobile Canvas FPS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | REJECT | 0.649–0.790 | 90.9 | 0.44 | 15.0 | 60.2 | 43.5 |
| 32 | REJECT | 0.813–0.896 | 45.5 | 0.82 | 16.7 | 60.2 | 26.4 |
| 64 | REVISE | 0.917–0.956 | 22.7 | 1.61 | 32.2 | 53.7 | 17.9 |
| 128 | REVISE | 0.960–0.973 | 11.4 | 3.06 | 58.8 | 31.0 | 10.3 |


35°・位相.625・48ポーズ条件の5方向近似シルエット指標。グレースケール画素からの近似IoUであり、アンチエイリアス端や白いハイライトを除外しうる。品質合格率ではない。数値より実比較PNGを優先する。

16/32層は胴体・脚・角が分離した板状になるためREJECT。64層は遠景サイズで読めるが、角・脚・尾に階段と隙間が明瞭。128層は35°で近似IoU .960–.973に改善するが、細い部位の筋と接地差は残る。最下段面の中央は地面から半層高にある（128層でも11.4mm）。元の足を無断で伸ばしたり、全体を下げて誤差を隠したりしていない。

カメラ俯角5/15/35/60/80°も同じGLBと比較。128層の側方近似IoUはそれぞれ .686/.905/.963/.963/.953。特に[5°](../../../public/exp-sprite-stacking/evidence/elevation-5.png)で断面間の空間が大きく見える。360°yawが可能でも、任意カメラ角度で元モデル同等の品質とはいえない。roll/pitch、地形に合わせた体軸変形はこの水平積層では未実装。

## Phase 2 — 胴体上下動による代用なし

GLBのnative clipだけでは元レビューの接地を再現できないため、既存D3-C v2のbody/authored drive/IK/toe-rollを評価し、一周期を**実時間積分した48個のスキニング結果**として保存した。12は4枚おき、24は2枚おき、48は全枚。画像変形・光学補間・新規ポーズ生成を使わず、元モデルの四肢・肩甲骨・胸部・頭・尾を保持。

実足裏頂点の回収高は前左63.6cm、前右65.2cm、後左48.0cm、後右48.0cm。骨盤の上下幅は約1.54cmなので、胴体の上下だけで脚運動を代用していない。肩甲骨は局所Z方向に左16.45cm／右19.22cmの移動幅、頭・尾・胸部も独立した元のポーズ変化がある。ただしこの数値は力強いスプリントの視覚合格を意味しない。

| ポーズ数 | 接地頂点 最大位置誤差 mm | RMS mm |
| --- | --- | --- |
| 12 | 131.9 | 72.1 |
| 24 | 62.5 | 36.6 |
| 48 | 27.8 | 17.0 |


上表は、既存の連続IKを240ステップで再評価し、「IKがstanceかつ実際の足裏頂点が地面1mm以内」の同一頂点を、離散ポーズ保持＋連続root移動の再生と比較した384サンプル。ターゲット座標の測定ではない。[詳細](../../../public/exp-sprite-stacking/evidence/contact-quantization.json)。48ポーズでも最大約2.8cmあり、元のIKの1mm級接地をそのまま維持できない。12/24はさらに大きい。旋回時の支持足の世界固定と、加減速時の可変ストライドIKは実行時に残しておらず、追加のずれがありうる。固定ストライドに走行距離で位相を結び付けた実証である。

## Phase 3 — 操作できるコース

Canvas 2Dを最初に実装し、層数／体数に比例する性能低下を実測したため、同じ断面PNGを描くWebGL比較も追加した。WebGL版も元のクリーチャーメッシュを描かず、断面画像の平面quadを描く。GLBは明示的な比較モードだけが読み込む。Canvas初期表示でGLBが読み込まれないことをブラウザテストで確認。

直線からカーブへの連続走行、加速・減速、yaw旋回、位置追従カメラ、1/6/18体を実装。地面を先に描き、奥の柵→距離順の走者→手前の柵で前後関係を示す。平面コースと柵の範囲の実証であり、起伏地形、斜面接地、全オブジェクトの厳密な相互depth解決を主張しない。

PC 1440×1080、モバイル390×844で実際のキー操作・タッチhold/cancel・自由旋回・描画方式の往復・層数／ポーズ数・18体・横overflowなしを検証。両方PASS、page/console errorとHTTP失敗0。実画面は `evidence/desktop-course.png`、`mobile-course.png`。モバイルの並列3画面は比較用の小表示であり、操作走行は単画面を使う。

## Phase 4 — 性能と既存方式

同じSモデル・同じスキンポーズ・同じカメラ・同じ陰影で、既存の2D billboard方式、GLBメッシュ描画方式、Canvas積層、WebGL積層を比較した。元の本番2Dシートはモデル／ポーズが違うため、**同じGLBから16方向・35°の画像を再ベイク**し、同一素材比較を成立させた。これは既存の本番2D画面全体のベンチマークではない。2Dの方向は22.5°刻みで、俯角は35°固定。

各方式へ同じ離散骨ポーズを渡し、**全方式で元IK計算はオフライン**。GLB比較も生のIKを毎フレーム回す本番総コストではなく、描画方式を切り分けた比較である。共通コース、影、UI、CSS pixel 1倍を使用。PCの描画面は1150×558、モバイルは356×464。各環境内で方式間は同条件。

| 環境 | 方式 | FPS | 平均間隔 ms | p95 ms | 初期表示 s | JS heap MiB | Chrome RSS MiB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pc-equivalent | 2D同一素材ベイク | 60.2 | 16.6 | 16.7 | 1.04 | 4.6 | 763 |
| pc-equivalent | GLB元モデル | 11.6 | 86.6 | 100.1 | 1.35 | 18.8 | 771 |
| pc-equivalent | Canvas積層 | 53.7 | 18.6 | 33.3 | 0.75 | 3.5 | 697 |
| pc-equivalent | WebGL積層 | 60.0 | 16.7 | 16.7 | 0.92 | 14.8 | 820 |
| mobile-equivalent | 2D同一素材ベイク | 60.2 | 16.6 | 16.7 | 6.18 | 3.5 | 674 |
| mobile-equivalent | GLB元モデル | 8.2 | 121.2 | 166.7 | 6.57 | 21.6 | 646 |
| mobile-equivalent | Canvas積層 | 17.9 | 55.9 | 66.8 | 2.82 | 3.3 | 600 |
| mobile-equivalent | WebGL積層 | 40.5 | 24.7 | 33.4 | 3.06 | 7.5 | 683 |


6体・24ポーズ・積層64層の抜粋。[全76条件](../../../public/exp-sprite-stacking/evidence/performance.csv)には16/32/64/128×12/24/48、各方式1/6/18体を含む。各条件の冷キャッシュ初期表示、4秒の実時間frame間隔、CPU描画時間、生配列、JS heap、Chrome process RSS、素材bytes、復号RGBAを保存。

**測定環境の限界：** Chromium 151、SwiftShaderのソフトウェアWebGL、同じクラウドCPU。PC相当はCPU1×・100Mbps/20ms、モバイル相当はCPU4×throttle・10Mbps/80ms。実機PC GPUやスマートフォンGPUの性能を代表する数値ではない。単回・1秒warmup＋4秒sampleで統計的なハード保証はしない。GLBが遅いことを一般のGPU端末に外挿しない。

JS heap、画像RGBA見積り、Chrome RSSは違う範囲。RSSはChromeプロセスを合算し共有ページを二重計上しうる。GPU/driver領域も網羅しない。WebGL積層のテクスチャはCPU画像に加えて同寸法のGPU backingを持ちうる。素材容量とRAMを混同しない。オフライン単一HTMLは全素材を埋め込むため、この通常版ベンチマークとはロード／メモリ条件が異なる。

24ポーズ時、16/32/64/128層PNGは .44/.82/1.61/3.06MB、復号RGBAは15.0/16.7/32.2/58.8MiB。GLBは2.04MB＋骨ポーズJSON約.20MB（Three等のコードは別途）。同一素材の16方向2Dは5.92MB、RGBA96MiB。フレーム数の増加は方向画像と断面の両方で素材／画像RAMを増やす。元本番2D WebPとこの16方向PNGを同じ圧縮条件とみなさない。

## KEEP / REVISE / REJECTの根拠

- **REVISE（総合・64/128層）：** 技術の実動は確認。128層の通常俯角は相当近いが、低角度の欠損、接地誤差、固定光、メモリ増加を残す。既存S造形／モーション自身もREVISEであり、軽量化を理由に本番KEEPへ昇格させない。
- **REJECT（16/32層をSの近景表示に使用）：** 脚・角・胴が明瞭に離断した板状になる。軽いだけでは成立しない。
- **KEEPなし（本番採用）：** 柵の前後関係と操作テストのPASSは、斜面接地、世界光、実機モバイル、指定参照画のテクスチャ一致のPASSに代わらない。

次の技術判断を変える条件は、造形を変えずに薄い部位の隙間と低角度を改善できること、標本化／旋回中の支持足誤差を許容範囲へ抑えられること、実機GPUを含めた条件で品質と性能の両方を満たすこと。今回の成果物を本番へ混ぜず、別実験として残す。

## 再現

```sh
git switch exp/2p5d-sprite-stacking-20261118
npm install
python3 -m pip install -r scripts/requirements-sprite-stacking.txt
node scripts/stacking-poses.mjs
python3 scripts/stacking-slices.py --workers 4
python3 scripts/stacking-validate.py
node scripts/stacking-contact.mjs
npx vite --host 127.0.0.1 --port 4173
# 別端末。CHROMIUM_PATHを利用可能なChrome/Chromiumへ設定
CHROMIUM_PATH=/usr/bin/chromium node scripts/stacking-bake-sprites.mjs
CHROMIUM_PATH=/usr/bin/chromium node scripts/stacking-qa.mjs
CHROMIUM_PATH=/usr/bin/chromium node scripts/stacking-benchmark.mjs
# 性能計測を終えてから動画を収録し、負荷を混ぜない
CHROMIUM_PATH=/usr/bin/chromium node scripts/stacking-capture.mjs
CHROMIUM_PATH=/usr/bin/chromium node scripts/stacking-capture-frames.mjs
python3 scripts/stacking-quality.py
python3 scripts/stacking-report.py
node scripts/stacking-package.mjs
npm run build
```

通常版URLは `http://127.0.0.1:4173/evowild-test/exp-sprite-stacking/index.html`。Viteのディレクトリfallbackを避けるため `index.html` まで指定する。Blenderや有料生成APIは不要。Python/numpy/Pillowによる三角形切断、既存Three.js制御のNode評価、Playwright、FFmpegのみ。FFmpeg/H.264は動画作成時に必要。

元のsprite-stacking参考repositoryの技術説明は確認し、コードはコピーしていない。UI8 `/fly` は環境のネットワーク許可先に含まれず取得できなかったため、見たと主張しない。Three.js MIT licenseを同梱。初回2Dベイクにfavicon 404が1件あったが、favicon設定後の最終QA・性能・動画収録にはbrowser error 0。キャプチャの初回待機失敗は、決定的収録でRAFを停止したためで、待機を100ms pollingへ修正して完了した。合格基準を下げていない。
