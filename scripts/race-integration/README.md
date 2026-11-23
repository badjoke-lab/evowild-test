# 統合試験の再現

リポジトリのルートから実行する。Node、Three.js、Vite、Playwright、WebGL 2対応Chromium、Python 3、NumPy、Pillow、ffmpegが必要。テストは `CHROMIUM_PATH` と `TRIAL_URL` でブラウザとベースURLを指定できる。性能計測・動画収録は順番に実行する。

```sh
export TRIAL_WORK="$(mktemp -d)"
mkdir -p "$TRIAL_WORK/site/evowild-test"
node_modules/.bin/vite build --outDir "$TRIAL_WORK/site/evowild-test"
python3 -m http.server 4180 --bind 127.0.0.1 --directory "$TRIAL_WORK/site"
```

別シェルでも同じ `TRIAL_WORK` を指定する。既存の専用Morph標本用のOBJ／MTLがないチェックアウトは、配布ZIPの `evowild-test/models/evowild-s.{obj,mtl}` を `public/models/` にコピーしてからビルドする。新規のモデル生成は不要。通常のエントリは `/evowild-test/`、仮統合は `/evowild-test/?raceTrial=1`。

```sh
TRIAL_SHOTS="$TRIAL_WORK/shots" node scripts/race-integration/regression.mjs
node scripts/race-integration/quality.mjs "$TRIAL_WORK/quality"
python3 scripts/race-integration/plates.py "$TRIAL_WORK/quality" "$TRIAL_WORK/shots"
node scripts/race-integration/record.mjs
node scripts/race-integration/device-check.mjs
python3 scripts/race-integration/report.py
node_modules/.bin/vite build --outDir "$TRIAL_WORK/site/evowild-test"
python3 scripts/race-integration/package.py "$TRIAL_WORK/site/evowild-test"
```

`regression.mjs` はゲームの通常のRAFコールバックをテストブラウザから駆動し、既存の選択・一時停止・リセット・カメラの入口を使う。検証用の `verify=1` は読み取り専用の状態スナップショットを有効にする。`record.mjs` は実時間収録、`device-check.mjs` は検証スナップショットを無効にした実際の計測・ダウンロード操作を使う。

配布ZIPを別フォルダーに展開し、そのルートから `python3 -m http.server 4181 --bind 127.0.0.1` を起動して `node scripts/race-integration/package-check.mjs` を実行する。初回の表面ファイル読込を失敗させ、従来表示で継続してから再選択で復旧すること、動画・画像・JSON比較が配布物だけで開くことを検証する。
