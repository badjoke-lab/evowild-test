# S–01 v2 · 造形と群走LOD

[操作デモ](https://evowild-s01-sprite-stacking-lab.bracedllama8.chatgpt.site/v2/index.html) ／ [採用判定・実測表](https://evowild-s01-sprite-stacking-lab.bracedllama8.chatgpt.site/v2/evidence/review.html) ／ [v1の観察室](https://evowild-s01-sprite-stacking-lab.bracedllama8.chatgpt.site/index.html)

## 起動

```sh
git clone --branch exp/s-pixel-stacking-zero-20261121 --single-branch https://github.com/badjoke-lab/evowild-test.git
cd evowild-test
python3 -m http.server 4173 --bind 127.0.0.1 --directory public
```

[ローカルのv2](http://127.0.0.1:4173/s-pixel-lab/v2/index.html) を開く。生成・インストールは起動に不要。群走を見るには「走行コース」「50」または「100」を選ぶ。カメラ倍率を動かすと同じ走行中に積層・移行・スプライトの内訳が変わる。「積層のみ」「スプライトのみ」は同一視点・同一ポーズで方式を切り替える比較用。PCはドラッグ、スマートフォンはタッチで旋回できる。

## 入力と差分

開始コミットは `1179f4e295aafe6612cdad956517ab2522c409b3`。原画とv1の素材・証跡・配布ZIPは元のパスに保持した。[原画](../../../art/s-creature/references/00_s_type_modeling_image_v1.png) のSHA256は `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`。v2専用の素材・証跡は `public/s-pixel-lab/v2/` にある。v1とv2はカメラ投影・コース・四足のタイミング・断面のメッシュ化を共有する。

- [造形生成](bake.py) はv1の4方向部位画と同じ24ポーズを入力にする。頭冠は元の側面色帯の中心をポーズ変換し、量子化後の階段の隣接面を接続する。脚は接地時の前後位置を維持し、前脚と後脚の左右の軌道、遊脚中の横変位だけを調整した。原画の肩・骨盤・配色はそのまま使用した。
- [スプライト生成](atlas.mjs) はv2の128層PNGを本番Workerで読み、同じ着色面を48方位×10俯角に投影する。24走行＋静止の計12,000枚。固定ピボット、切り出し位置、前面深度、4点被覆を保存する。[色・深度ページの作成](pad-depth.py) で空画素側へ深度だけを延長し、細い先端の参照座標を安定させる。
- 距離LODは正投影の画面上の体長と視線方向の各個体の深さで決める。近景は選択した64/128層。補正後の体長が142～110 pxの帯で積層とスプライトを相補的に切り替える。110～94 pxは画素ごとの視差補正と6×6格子の視差補正を混ぜ、遠景では格子を使う。各カードは実際のポーズ・方向・俯角の色と深度を持ち、胴の後ろに隠れる脚や別個体との前後関係を処理する。
- 近景の頭冠は4サンプルの被覆で描画する（対応GPU、元の画面寸法に解決）。中・遠景はベイクした被覆を使う。静止した標本カメラでは同じ投影の床だけを再利用する。走行ポーズと影は毎フレーム更新し、コース移動・自動回転では床を再描画する。
- [5方向の比較画像](../../../public/s-pixel-lab/v2/evidence/comparison.png)、[連続ズーム・旋回誤差](../../../public/s-pixel-lab/v2/evidence/sweep.json)、[部位別の視認性](../../../public/s-pixel-lab/v2/evidence/morphology.json)、[操作試験](../../../public/s-pixel-lab/v2/evidence/ui.json)。

## 素材・計測・証跡を再生成

Linux、Python 3.12、NumPy・Pillow・SciPy、Node、Playwright、Chromium、FFmpeg/libx264。比較図の日本語にはNoto Sans CJKを使用。以下はリポジトリルートから実行する。

```sh
npm install
python3 -m pip install numpy pillow scipy
python3 scripts/s-pixel/v2/bake.py
python3 scripts/s-pixel/v2/stance.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory public
```

HTTPサーバーを起動したまま、別の端末で以下を順に実行する。ベイクはv1観察室のブラウザ環境内で、v2のWorkerとv2の断面を明示的に選ぶ。

```sh
export CHROMIUM_PATH=/usr/bin/chromium
node scripts/s-pixel/v2/atlas.mjs
python3 scripts/s-pixel/v2/pad-depth.py
node scripts/s-pixel/v2/inspect.mjs
python3 scripts/s-pixel/v2/plates.py
node scripts/s-pixel/v2/sweep.mjs
node scripts/s-pixel/v2/ui.mjs
node scripts/s-pixel/v2/media.mjs
node scripts/s-pixel/v2/measure.mjs v1 128
node scripts/s-pixel/v2/measure.mjs v2 128
node scripts/s-pixel/v2/measure.mjs v1 64
node scripts/s-pixel/v2/measure.mjs v2 64
node scripts/s-pixel/v2/course-measure.mjs
node scripts/s-pixel/v2/memory.mjs
python3 scripts/s-pixel/v2/report.py
```

動画は本番レンダラーから時刻指定で採取した24 fpsのH.264。性能は独立した実時間計測。比較表のGPU計時は拡張機能の有効なサンプルのみを使う。v1の初回報告値と今回のv1再計測値は判定書で区別している。
