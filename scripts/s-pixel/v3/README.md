# EvoWild Run · S–01 ボクセル版 v3

[操作デモ](https://evowild-s01-sprite-stacking-lab.bracedllama8.chatgpt.site/v3/index.html) ／ [実測・採用判定](../../../public/s-pixel-lab/v3/evidence/review.html) ／ [共通ボクセル原本](../../../public/s-pixel-lab/v3/assets/voxels/index.json)

```sh
git clone --single-branch --branch exp/s-pixel-stacking-zero-20261121 https://github.com/badjoke-lab/evowild-test.git
cd evowild-test
python3 -m http.server 4173 --bind 127.0.0.1 --directory public
```

ブラウザで [v3観察室](http://127.0.0.1:4173/s-pixel-lab/v3/index.html) を開く。実行に必要な素材は同梱している。「混在100体」を押すと走行、曲線追走、旋回、ズームを開始する。ドラッグやスライダーで任意のカメラへ移れる。「積層と並列比較」は同じ時刻・投影で2つのキャンバスを描く。性能計測は単画面で行った。

## 原本からの再生成

原画とv2の部位別作画・配色・足運びを継承した。原本は静止1姿勢と走行24姿勢、それぞれ128×60×283の色番号配列である。形式、ハッシュ、元の作画からの復元、変更した原本から断面・遠景アトラスを更新する方法は [SOURCE.md](SOURCE.md) に記載した。ボクセル原本を直接編集した後は `volume.py stacks` から始める。

以下はリポジトリのルートで実行する。Python環境には NumPy、Pillow、SciPy、VTK 9 が必要。メッシュ軽量化だけに使用する Node の依存関係を `scripts/s-pixel/v3/` に分離した。

```sh
npm ci --prefix scripts/s-pixel/v3
python3 scripts/s-pixel/v3/volume.py all
python3 scripts/s-pixel/v3/surface.py
python3 scripts/s-pixel/v3/pack.py
python3 scripts/s-pixel/v3/exact.py
python3 scripts/s-pixel/v3/directions.py
python3 scripts/s-pixel/v3/greedy.py
```

`surface.py` は外気に接する輪郭面を抽出し、頭冠・四脚・尾の先端を拘束して3段階の三角形メッシュを生成する。色は同じボクセルの露出した色番号を参照する。`pack.py` は全姿勢の位置・インデックスを共有GPUバッファへ、原本由来の色を1つのテクスチャ配列へ格納する。`exact.py` は別の比較方式として存在するボクセルを小さいブロックにまとめ、レイが最初に当たるセルをWebGL2で描けるようにする。

## ブラウザ検証と録画

Node、Chromium、Playwright、FFmpeg（libx264）、NumPy、Pillow を使う。比較図の日本語には Noto Sans CJK を使用した。上のローカルサーバーを起動した状態で、別の端末から実行する。

```sh
npm install
export CHROMIUM_PATH=/usr/bin/chromium
node scripts/s-pixel/v3/measure.mjs v2
node scripts/s-pixel/v3/measure.mjs v3
node scripts/s-pixel/v3/race-table.mjs
node scripts/s-pixel/v3/diagnostics.mjs
node scripts/s-pixel/v3/check-facing.mjs
node scripts/s-pixel/v3/inspect.mjs
node scripts/s-pixel/v3/ui.mjs
node scripts/s-pixel/v3/media.mjs
node scripts/s-pixel/v3/exact-check.mjs
python3 scripts/s-pixel/v3/check-regeneration.py
python3 scripts/s-pixel/v3/report.py
```

[計測条件・メモリの定義](MEASUREMENT.md) ／ [実測CSV](../../../public/s-pixel-lab/v3/evidence/race-performance.csv) ／ [既存v2の記録](../v2/README.md)
