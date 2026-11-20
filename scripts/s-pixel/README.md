# S–01 · ピクセル作画と水平断面の走行実験

**採用判定は REVISE。** 横と斜めでは頭冠・肩・尾と四足の走行を識別できる。正面での重なり、頭冠先端の離断、大群の描画コストが残る。[ブラウザ用判定書](../../public/s-pixel-lab/evidence/review.html) に5方向・旧版との比較、走行動画、接地と性能の実測を収録した。

## デモを開く

[ホスト版の観察室](https://evowild-s01-sprite-stacking-lab.bracedllama8.chatgpt.site) は所有者アカウントで開ける。共有用・オフライン起動用には以下のZIPを使う。

配布用の [デモZIP](../../public/s-pixel-lab-demo.zip) を展開し、Python 3で `start-demo.py` を実行する。WebGL 2対応ブラウザで開く。ビルド・npm・外部CDNは起動に不要。リポジトリでは次のコマンドを使う。

```sh
git switch exp/s-pixel-stacking-zero-20261121
python3 -m http.server 4173 --bind 127.0.0.1 --directory public
```

[ローカル観察室](http://127.0.0.1:4173/s-pixel-lab/) を開く。スマートフォンから同じLANのPCに接続する場合は `--bind 0.0.0.0` で起動し、URLのホストをPCのLANアドレスに置き換える。

- ▶ で走行の再生・停止、タイムラインでコマ送り、↺ で作画の静止姿勢を確認できる。
- ドラッグ・タッチまたは方位と俯角のスライダーでカメラを変更する。自動回転は走行と併用できる。キーボードは空白で再生、矢印でカメラ調整。
- 「走行コース」で、直線からカーブへ進む個体をカメラが追う。標本ビューでは指定した体数を整列させる。1・10・50・100体の各個体が選択中の層数で描画される。

## 原本・作画・ランタイム

- 作業ブランチの起点は main の `cde1bd7`。指定原本は造形ブランチ `48b39d8` の [00_s_type_modeling_image_v1.png](../../art/s-creature/references/00_s_type_modeling_image_v1.png)。SHA256は `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`。
- 参照した旧実験は `e002736b22f91b9a020109e0a251b6042544915d`。旧側面の比較画像のみ、比較用の原本として同梱した。実験コード・GLB・旧断面・モーションは動作入力に使っていない。
- [artwork.py](artwork.py) の手描きポリゴンと幅の指定を、17色＋透明の[4方向・部位別作画](../../public/s-pixel-lab/assets/drawings)にラスタライズする。全身上面は推定。原画の3/4図は独立した造形チェックに用いた。
- [bake.py](bake.py) はその4枚のPNGを読み戻し、部位の登録位置、断面曲率、関節を使って再構成する。近側と遠側の脚・頭冠・尾羽は別部位。側面の同一部位で隠れる幅は、上面と前後の輪郭を拘束にして推定する。
- まず12ポーズを作り、中間12ポーズを同じ軌道で追加する。各走行ポーズと静止姿勢に16/32/64/128層を生成した。各PNGは1姿勢の水平断面アトラス。manifestの各行は下から順に `[元x, 元z, 幅, 奥行, atlas内u, atlas内v]`。透明度0は空間。最大高さ464、長手テクセル幅3。
- WebGLの描画入力はその都度選んだ層数のアトラス。対応する高さ帯を埋め、外面の同色矩形をWorkerで結合して、ポーズごとにインスタンシングする。奥行き判定は全個体共通。画面の5方向画像はカメラプリセットのサムネイル。
- [比較画像](../../public/s-pixel-lab/evidence/comparison.png) / [層数比較](../../public/s-pixel-lab/evidence/layer-study.png) / [走行24コマ](../../public/s-pixel-lab/evidence/gait-cycle.png) / [実測CSV](../../public/s-pixel-lab/evidence/performance.csv)。

## 再生成

検証環境はLinux、Python 3.12、NumPy、Pillow、SciPy、Chromium、Node.js、Playwright、FFmpeg（H.264）。文字組版はNoto Sans CJKを使う。リポジトリのルートで実行する。

```sh
python3 -m pip install numpy pillow scipy
npm install
python3 scripts/s-pixel/bake.py
# 既存のindexed PNGを直接編集した場合は上のコマンドの代わりにこちら
# python3 scripts/s-pixel/bake.py --from-drawings
python3 scripts/s-pixel/quality.py
python3 -m http.server 4173 --bind 127.0.0.1 --directory public
```

別端末で続ける。Chromiumのパスは使用環境のものを指定する。

```sh
export CHROMIUM_PATH=/usr/bin/chromium
node scripts/s-pixel/capture.mjs
python3 scripts/s-pixel/plates.py
node scripts/s-pixel/layer-study.mjs
node scripts/s-pixel/qa.mjs
node scripts/s-pixel/benchmark.mjs
python3 scripts/s-pixel/report.py
python3 scripts/s-pixel/package.py
```

ベンチマークは動画収録やQAと同時に走らせない。画面フレームを24 fpsに時刻指定して撮った動画と、GPUの同期読出しを含む性能計測は別に記録する。CSVの平均・p95とサンプル数、JSONの生間隔を併記した。回転の単発画素反転はカメラに対する細い形状の移動を含み、ちらつきの主観評価と同一ではない。
