# EvoWild Run　S型ピクセル版 v4

**採用判定は REVISE。** 混在50・100体で平均30 fpsに届かなかった。PC幅での48時点の再計測は以下のとおり。p95 は RAF 間隔で、単位はミリ秒。

| PC幅・SwiftShader | v3 平均fps | v4 平均fps | v3 p95 | v4 p95 |
|---|---:|---:|---:|---:|
| 近景1体 | 37.03 | 38.66 | 51.5 | 51.6 |
| 近景10体 | 31.86 | 33.55 | 55.6 | 55.3 |
| 混在50体 | 21.71 | 25.17 | 76.0 | 62.2 |
| 混在100体 | 16.52 | 19.35 | 87.5 | 76.6 |
| 全景100体 | 35.00 | 35.05 | 56.4 | 54.1 |

## 操作デモ

[オフライン版ZIPをダウンロード](https://raw.githubusercontent.com/badjoke-lab/evowild-test/refs/heads/exp/s-pixel-stacking-zero-20261121/public/s-pixel-lab/v4/evowild-v4-demo.zip)。展開後、WebGL 2 対応の Chromium で `index.html` を開く。レース条件を選ぶとそのカメラで走行する。ドラッグで旋回、タイムラインで24姿勢を確認できる。「積層と並列比較」は同じ視点と位相の原本を表示する。レポート、画像、動画も同梱。配布HTMLの初期ロード後にネットワークを切り、4方式の描画と100体への切替を確認した。管理環境の Chromium は file:// の直接起動を制限するため、その起動経路だけは未検証。

チェックアウトからは `python3 -m http.server 4173 --directory public` を実行し、[操作デモ](http://localhost:4173/s-pixel-lab/v4/) または [採用試験](http://localhost:4173/s-pixel-lab/v4/evidence/review.html) を開く。v1・v2・v3 はそれぞれ元のURLで操作できる。

[PC幅・スマホ幅の性能CSV](../../../public/s-pixel-lab/v4/evidence/race-performance.csv) ／ [原画比較](../../../public/s-pixel-lab/v4/evidence/original.png) ／ [脚先](../../../public/s-pixel-lab/v4/evidence/legs.png) ／ [LOD移行](../../../public/s-pixel-lab/v4/evidence/transition.png) ／ [混在100体の実走行](../../../public/s-pixel-lab/v4/evidence/mixed100.mp4)

## 負荷と形状

初回の v3 区間計測では、混在100体のメッシュが28.12 ms、床が8.60 ms。LOD分類CPUは0.19 msだった。v4 はメッシュの局所形状を最適化し、陰影と足の接地補正の重みを事前計算した。完全不透明なバッチではフラグメントの破棄判定を省き、コースの補助グリッドを既存の床テクスチャへ焼き込んだ。v4 の同条件ではメッシュ24.67 ms、床10.57 msが残った。個体数・隊列・カメラ・LOD距離を両版の全480組で照合した。総合タイマーとパス別タイマーは独立したリプレイ。

走行時24姿勢と静止1姿勢は v3 の原本ボクセルから構築し、各ポーズのSHA-256をビルド時に照合する。精細メッシュは頭冠と足先の両側を部分固定し、レース用メッシュは格子の段差を平滑化してからフィットする。色は v3 の17色と同じボクセル塗りを参照する。遠景の奥行きスプライトと移行帯の中距離メッシュは v3 のものを使う。

頭冠の一時的な点滅率は標本旋回で0.832%から0.664%に低下した。正面・背面で原本上の分離した脚先186か所のうち、標本表示で別々に識別できた数は169から176、群走と同じ単一サンプルでは169から169。単一サンプルの遠近スイープ全体では頭冠IoU中央値が0.763から0.724に下がった。この残存する画質退行とフレーム時間の両方を採用判定に含めた。

より強い頂点削減は輪郭が崩れたため棄却。100体のインデックスを結合して全体を5 drawまで減らした試作も、GPU時間が39.72 msから47.27 msへ増えたため棄却した。[試作の数値](../../../public/s-pixel-lab/v4/evidence/trials.csv)

## 再現

開始コミット `f9b0b2380d31a2f9197c050569c5b4c7e068f8c6`。リポジトリ直下で実行する。ビルド済み資産を使う場合、メッシュの再生成は不要。再生成には Python の NumPy・SciPy・VTK、v3で固定した meshoptimizer が必要。計測と動画生成には Chromium、Playwright、Pillow、FFmpeg を使用する。物理GPU、スマートフォン実機は未測定。スマホ幅の値は同じ SwiftShader にCPU 4倍減速を設定したもの。

```sh
npm ci --prefix scripts/s-pixel/v3
python scripts/s-pixel/v4/mesh.py
npm run build
python3 -m http.server 4173 --directory public
```

別端末で以下を実行。GPU測定は同時実行せず、両版で同じ48時点を使う。

```sh
MEASURE_OUT=public/s-pixel-lab/v4/evidence/v3-race.json node scripts/s-pixel/v3/measure.mjs v3
node scripts/s-pixel/v3/measure.mjs v4
node scripts/s-pixel/v3/race-table.mjs v4
for v in v3 v4; do
  node scripts/s-pixel/v4/profile.mjs "$v"
  node scripts/s-pixel/v4/profile.mjs "$v" --transition
done
V3_QA_CACHE=/tmp/s4-qa V3_QA_ALL=1 V3_QA_VERSIONS=v3 V3_QA_METHODS=stack,lod,lod-race node scripts/s-pixel/v3/inspect.mjs
V3_QA_CACHE=/tmp/s4-qa V3_QA_ALL=1 V3_QA_VERSIONS=v4 V3_QA_METHODS=lod,lod-race node scripts/s-pixel/v3/inspect.mjs
python scripts/s-pixel/v4/appearance.py /tmp/s4-qa
node scripts/s-pixel/v4/courses.mjs
FILM_VERSION=v4 node scripts/s-pixel/v3/media.mjs
node scripts/s-pixel/v3/ui.mjs v4
python scripts/s-pixel/v4/report.py
node scripts/s-pixel/v4/portable.mjs /tmp/s4-offline
```
