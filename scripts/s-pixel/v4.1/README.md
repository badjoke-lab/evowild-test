# 再現手順

リポジトリのルートで実行する。描画資産は同梱済み。Python 3（NumPy、SciPy、Pillow）、Node.js、Playwright、Chromium、ffmpeg が必要。表面の再構築だけは事前に `scripts/s-pixel/v3` の meshoptimizer を依存定義・ロックファイルに従ってインストールする。Chromiumのパスは `CHROMIUM_PATH` で指定できる。PNGの日本語ラベルには旧版と同じCJKフォントを使用する。

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory public
```

別シェルで実行する。計測中は他のブラウザ試験やエンコードを並列に実行しない。

```sh
node scripts/s-pixel/v4.1/adoption.mjs
node scripts/s-pixel/v4.1/ablation.mjs
node scripts/s-pixel/v4.1/race-check.mjs
node scripts/s-pixel/v4.1/ui-check.mjs
python3 scripts/s-pixel/v4.1/report.py
```

基準画像、動画と配布ZIPの再生成には次を実行する。`surface.py` の入力はv3の保存済みボクセルで、各姿勢のSHA-256を照合する。生成先はv4.1専用の表面メッシュ。遠景スプライト・ボクセルの再生成は不要。

```sh
python3 scripts/s-pixel/v4.1/surface.py
export V3_QA_CACHE="$(mktemp -d)" V3_QA_GROUPS=views,switch,gait V3_QA_ALL=1
V3_QA_VERSIONS=v3 V3_QA_METHODS=stack node scripts/s-pixel/v3/inspect.mjs
V3_QA_VERSIONS=v4,v4.1 V3_QA_METHODS=lod-race node scripts/s-pixel/v3/inspect.mjs
python3 scripts/s-pixel/v4.1/quality.py "$V3_QA_CACHE"
python3 scripts/s-pixel/v4.1/film.py "$V3_QA_CACHE"
node scripts/s-pixel/v4.1/race-film.mjs
export S_DEMO_PATH="$(mktemp -d)"
node scripts/s-pixel/v4.1/package.mjs "$S_DEMO_PATH"
python3 -m http.server 4175 --bind 127.0.0.1 --directory "$S_DEMO_PATH"
```

別シェルで `QA_URL=http://127.0.0.1:4175/index.html QA_OFFLINE=1 node scripts/s-pixel/v4.1/ui-check.mjs` を実行すると、配布HTMLが初期読込後にネットワークを遮断しても両サイズの測定・保存を完了できるか検証する。配布ZIPに最新の検証記録を含めるにはパッケージ生成を再度実行する。
