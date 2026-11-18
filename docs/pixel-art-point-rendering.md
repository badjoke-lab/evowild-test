# EvoWild｜D3-C v2 Pixel-art 点群描画実験

対象は S の D3-C v2 確定 GLB。`exp/d3c-scapula-authoring` で v2 を検証した `9689bbbc` から `exp/pixelart-point-rendering` を作成した。GLB の SHA-256 は `6edb45e7aeb3179104d5b406d09eaa1f34da6baf09ddc9a6a0535d7e96f3f1c0`。23 関節、材質、骨格、既存の走行・接地モジュールをそのまま使用する。モデルと既存ランタイムに対する差分はゼロ。

## 比較ページ

```sh
npm install --no-package-lock
npm run dev
```

[http://localhost:5173/evowild-test/pixel-art.html](http://localhost:5173/evowild-test/pixel-art.html) を開く。A〜D を切り替えてもカメラと走行位相は引き継がれる。点群の密度・サイズ・陰影は B〜D、内部解像度・色数・深度輪郭は C/D で調整できる。PNG 保存と、全方式・4 個体数の計測結果の JSON 保存に対応する。

静止は現在の姿勢を固定する。歩行相当は D3-C v2 の走行制御を 0.5× で実行する。専用歩行クリップは収録されていない。元のワールド座標で走行と接地を解いた後、比較用カメラでは個体の移動量を相殺して定点表示する。

| 方式 | 描画 |
| --- | --- |
| A 既存 3D | D3-C v2 のスキン付き三角形メッシュと GLB の材質。全方式で同じ背景・カメラを使う。 |
| B 表面点群 | 面積比で決定的にサンプルした表面点を画面解像度の不透明円で描画し、深度テストする。 |
| C ピクセル点群 | B と同じ表面点。背景と合わせて低解像度で描画し、深度差から輪郭を付け、指定パレットに減色して最近傍拡大する。 |
| D Gaussian splats | 同じ表面点に、変形後の三角形の接平面に沿う 3D Gaussian を配置する。投影した共分散から画面上の楕円を計算し、背景深度と元メッシュの深度で遮蔽してから、加重合成と C と同じ後処理を行う。 |

B〜D では各点に元の面の頂点 ID と重心座標を保存する。シェーダーでその三頂点を A と同じ骨行列とウェイトで変形し、その後で点の座標を補間する。点の生成はロード時に 1 回だけ。密度変更は同じ点列の表示件数を変える。画面上で点が見え隠れすることと、点の中心が面から離れることは別々に評価した。

D は `EXT_color_buffer_float` を使う。表面由来の Gaussian を外側のメッシュ深度で選別し、RGBA16F に累積する方式。学習済み 3DGS のビューデペンデントな色や、深度順ソートによる厳密な透過合成はこの実装の範囲外。草・樹木・岩はシード固定のインスタンスで生成し、C/D では動物と同じ後処理を通す。

## 比較画像と動画

| 方式 | 静止 | 歩行相当 0.5× | 走行 1.0× | MP4 |
| --- | --- | --- | --- | --- |
| A | [PNG](evidence/pixel-art/A-idle.png) | [PNG](evidence/pixel-art/A-slow.png) | [PNG](evidence/pixel-art/A-run.png) | [動画](evidence/pixel-art/A.mp4) |
| B | [PNG](evidence/pixel-art/B-idle.png) | [PNG](evidence/pixel-art/B-slow.png) | [PNG](evidence/pixel-art/B-run.png) | [動画](evidence/pixel-art/B.mp4) |
| C | [PNG](evidence/pixel-art/C-idle.png) | [PNG](evidence/pixel-art/C-slow.png) | [PNG](evidence/pixel-art/C-run.png) | [動画](evidence/pixel-art/C.mp4) |
| D | [PNG](evidence/pixel-art/D-idle.png) | [PNG](evidence/pixel-art/D-slow.png) | [PNG](evidence/pixel-art/D-run.png) | [動画](evidence/pixel-art/D.mp4) |

[4 方式の同期比較 MP4](evidence/pixel-art/comparison.mp4) は静止 0.5 秒、固定カメラの低速 1 秒、走行と 360° 回転 3.5 秒。各方式 120 枚の実 WebGL フレームを 24 fps に符号化した。動画の 24 fps は実行時 FPS とは無関係。静止画・動画の各フレームは描画方式間で同じ位相とカメラ角を指定して撮影した。 [デスクトップの操作画面](evidence/pixel-art/desktop-ui.png) · [Pixel 7 画面エミュレーション](evidence/pixel-art/pixel-7-ui.png)

## 測定条件

走行 1.0×、自動回転、背景あり、4,000 点/体、44 mm、陰影 65%、C/D 解像度 35%、24 色、輪郭 60%。各条件は 1.2 秒ウォームアップし、3 秒以上の `requestAnimationFrame` の間隔を計測。既存のビューアーと同じく、シミュレーションの 1 フレームの進みは 50 ms を上限とする。FPS はフレーム数を実測時間で割った値。GPU 時間は `EXT_disjoint_timer_query_webgl2` の有効サンプルの中央値で、ポーズ計算と描画提出を含む CPU 時間とは別に記録した。GPU メモリは使用バッファと描画ターゲットの概算。ドライバのメモリ、既定フレームバッファ、ブラウザ全体のメモリは含まない。JSON の JS ヒープはブラウザが返した計測時点の値で、先行試行のキャッシュや GC の影響を含む。

PC 条件は 1360×960 CSS px・DPR 1、Pixel 7 条件は 412×839 CSS px・モバイルタッチ設定・端末 DPR 2.625、描画 DPR 上限 1.5。A/B のバッファは PC 条件 1,012×673 px、Pixel 7 条件 573×442 px。C/D はそれぞれ 354×236 px、201×155 px。どちらも同一 Linux VM の Chromium/ANGLE SwiftShader。記録した GPU 時間はソフトウェア WebGL の処理時間であり、実機 GPU の稼働率や電力・熱、物理 Pixel 7 と GPU 搭載 PC の FPS は未測定。実機では比較ページ下の計測ボタンで同じ条件を取得できる。

[デスクトップ条件の全データ](evidence/pixel-art/desktop-benchmark.json) · [Pixel 7 条件の全データ](evidence/pixel-art/pixel-7-emulated-benchmark.json)

| 方式 | 個体数 | 総点数 | PC 条件 FPS | Pixel 7 条件 FPS | PC 条件 GPU ms | Pixel 7 条件 GPU ms | GPU バッファ概算 PC / Pixel 7 (MiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 1 | 0 | 14.1 | 23.5 | 47.3 | 25.1 | 3.82 / 3.82 |
| A | 10 | 0 | 5.8 | 8.3 | 137.5 | 109.9 | 3.84 / 3.84 |
| A | 50 | 0 | 2.1 | 2.3 | 419.1 | 391.7 | 3.93 / 3.93 |
| A | 100 | 0 | 1.2 | 1.2 | 754.2 | 840.6 | 4.04 / 4.04 |
| B | 1 | 4,000 | 13.0 | 20.7 | 62.5 | 28.5 | 4.13 / 4.13 |
| B | 10 | 40,000 | 8.8 | 13.0 | 97.2 | 75.8 | 4.15 / 4.15 |
| B | 50 | 200,000 | 3.9 | 4.2 | 218.1 | 210.5 | 4.23 / 4.23 |
| B | 100 | 400,000 | 2.5 | 3.0 | 370.8 | 312.8 | 4.34 / 4.34 |
| C | 1 | 4,000 | 6.1 | 13.4 | 145.0 | 72.7 | 4.76 / 4.36 |
| C | 10 | 40,000 | 4.4 | 10.7 | 192.5 | 87.7 | 4.78 / 4.38 |
| C | 50 | 200,000 | 3.3 | 4.6 | 280.5 | 210.3 | 4.87 / 4.47 |
| C | 100 | 400,000 | 2.3 | 2.8 | 509.2 | 337.2 | 4.98 / 4.58 |
| D | 1 | 4,000 | 5.3 | 12.2 | 181.5 | 80.2 | 7.74 / 6.54 |
| D | 10 | 40,000 | 3.6 | 5.2 | 235.6 | 194.8 | 7.76 / 6.56 |
| D | 50 | 200,000 | 1.3 | 2.1 | 722.1 | 568.6 | 7.85 / 6.65 |
| D | 100 | 400,000 | 0.7 | 0.8 | — | 1031.9 | 7.96 / 6.76 |

D の 100 体は標準窓で GPU サンプルが PC 条件 0 件、Pixel 7 条件 1 件だった。計測窓を 15 秒に延ばした追試では、PC 条件 0.81 FPS・GPU 中央値 1,186.2 ms（10 件）、Pixel 7 条件 0.89 FPS・1,108.1 ms（12 件）。 [PC 追試](evidence/pixel-art/desktop-d100-benchmark.json) · [Pixel 7 追試](evidence/pixel-art/pixel-7-emulated-d100-benchmark.json)

## 画質と接地

- **A** は角の先端、胸と脚の境界、前後に重なった細部が読みやすい。回転すると面の陰影は大きく変わる。元の高い金属度のため、角度によって腹側が暗い。
- **B** は 360° 回転しても点の集まりが同じ体表を追従する。丸い点が先端を太く見せ、脚と角の細分が丸まりやすい。シーンの解像度は A と同じなので背景は滑らかに見える。
- **C** は動物、草、樹木、岩の色と縁に同じピクセルの粒度が出る。輪郭の見分けやすさが上がる一方、接近した前脚や角の分岐が同じ画素に入ると A より判別しづらい。走行と回転中は細い脚先で画素単位の明滅が見える。
- **D** は斜めから見た面の粒状感を弱める。重なった脚と角の周辺では、深度選別と加重合成で C より縁が軟らかくなる。画風の統一性に対する追加効果は小さい。

既存 `s-run-review.html` と同じ設定で 0.5× と 1.0× を 1 周期ずつ、各 121 フレーム比較した。全脚の関節座標差は最大 `2.78e−15 m`。実際の足裏頂点の測定では支持脚の最大浮きが **0.416 mm**、貫通が **0 mm**。各フレーム 256 点について、シェーダーのパック済み頂点と骨行列を CPU で再計算した位置と、Three.js の変形三角形上の重心補間との差は最大 **0.00017 mm**。これは点の中心の検証で、点半径とピクセル化による画面上の太さは別に観察した。両ビューポートで切り替え、全スライダー、PNG 保存、表示幅を検証し、ブラウザエラーは 0 件。 [ブラウザ検証結果](evidence/pixel-art/validation.json)

## 採用判定

**レース標準への採用は保留。C を少数表示の演出候補として残す。** C は背景と S の画風がそろい、低速・走行とも関節の軌道を維持できた。細い部位の明滅と後処理時間が残るため、近接展示やリプレイなど、見せる個体が少ない場面での候補とする。B は多数描画の比較では有望だが、丸い点が既存モデルの細部を均すため、レース標準への切り替えは保留。D は同じ点数でメッシュ深度を含む 4 パスを要し、輪郭の改善も限定的なので見送る。

100 体の標準計測では、PC 条件で A 1.2、B 2.5、C 2.3、D 0.7 FPS、Pixel 7 条件で A 1.2、B 3.0、C 2.8、D 0.8 FPS。C は 1 体では両条件で A より遅く、D は 50〜100 体で A を下回った。ソフトウェア WebGL 上の傾向であり、本番の判定には対象端末で画質とフレーム時間を再測定する必要がある。

## 再現

Vite ビルドと配信用ビルドの描画を検証済み。D3-C v2 の既存停止・反復フレーム検証はデスクトップと Pixel 7 エミュレーションで 2/2 件合格した。

Vite サーバーを起動した状態で実行する。Playwright 用の Chromium を使う場合は `CHROMIUM_PATH` を省略できる。動画生成には FFmpeg の `libx264` と `drawtext` を使う。

```sh
python3 scripts/verify_s_d3c_v2.py
npm run build
CHROMIUM_PATH=/usr/bin/chromium node scripts/pixel-art-evidence.mjs all
CHROMIUM_PATH=/usr/bin/chromium node scripts/pixel-art-evidence.mjs heavy
```

## 参照した資料

- `pixelart-gaussiansplat` の surfel、スクリーン空間に固定した低解像度表示、減色・輪郭処理を参照した。点のアニメーションは EvoWild の三角形と既存 IK から独自に評価する。 [pixelart-gaussiansplat](https://github.com/cobanov/pixelart-gaussiansplat)
- `shapeshift-labs-ink-studio` のコードによる環境生成と共分散を持つ splat を参照した。実験に両リポジトリのコード・アセット・追加依存は持ち込んでいない。 [ink-studio](https://github.com/siliconjungle/shapeshift-labs-ink-studio)
- Web G Pixel とライセンスページはこの環境から HTTP 403 のため閲覧できなかった。 [Web G Pixel](https://amix-design.com/tl/web-g-pixel/) · [ライセンス](https://amix-design.com/tl/web-g-pixel/license.html)
