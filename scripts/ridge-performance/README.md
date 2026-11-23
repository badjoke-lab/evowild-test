# Ridge Oval 統合レースの再測定

基準コミットは `b13743d5a473660f2b7979b504fcb32cda43ce11`。リポジトリの Node / Vite、Chromium、Playwright、Python 3、NumPy、Pillow、ffmpeg を使用する。試験は同じブラウザで順番に実行する。モデルが未展開の場合、次の手順で過去の配布物にある Morph 標本を読み出せる。

```sh
export RIDGE_WORK="$(mktemp -d)"
export BEFORE_URL=http://127.0.0.1:4201/evowild-test/
export AFTER_URL=http://127.0.0.1:4202/evowild-test/
export REPORT="$PWD/public/ridge-performance/evidence"
mkdir -p "$RIDGE_WORK/before" "$RIDGE_WORK/after/evowild-test" "$REPORT"
unzip -q public/race-integration/ridge-race-demo.zip -d "$RIDGE_WORK/before"
cp -n "$RIDGE_WORK/before/evowild-test/models/"evowild-s.{obj,mtl} public/models/
node_modules/.bin/vite build --outDir "$RIDGE_WORK/after/evowild-test"
node scripts/ridge-performance/build-probe.mjs "$RIDGE_WORK/before/evowild-test" b13743d5a473660f2b7979b504fcb32cda43ce11
node scripts/ridge-performance/build-probe.mjs "$RIDGE_WORK/after/evowild-test"
```

各フォルダーを別々の端末から配信する。

```sh
python3 -m http.server 4201 --bind 127.0.0.1 --directory "$RIDGE_WORK/before"
python3 -m http.server 4202 --bind 127.0.0.1 --directory "$RIDGE_WORK/after"
```

通常のゲーム画面で計測ボタンとJSONダウンロードを操作する `accept.mjs` と、同じゲームを専用ページで再生して描画区間を計時する `profile.mjs` を分けて実行する。PC幅は 1100×745 / DPR 1、スマホ幅は 390×844 / DPR 2.625・タッチ。両方とも Chromium の ANGLE SwiftShader。

```sh
node scripts/ridge-performance/accept.mjs "$BEFORE_URL" "$RIDGE_WORK/accept-before"
node scripts/ridge-performance/accept.mjs "$AFTER_URL" "$RIDGE_WORK/accept-after"
node scripts/ridge-performance/profile.mjs "$BEFORE_URL" "$RIDGE_WORK/measured-before"
node scripts/ridge-performance/profile.mjs "$AFTER_URL" "$RIDGE_WORK/measured-after"
python3 scripts/ridge-performance/evidence.py "$RIDGE_WORK" "$REPORT"
python3 scripts/ridge-performance/tail.py "$RIDGE_WORK" "$REPORT"
node scripts/ridge-performance/profile.mjs "$BEFORE_URL" "$RIDGE_WORK/tail-before" "$RIDGE_WORK/tail-frames.json"
node scripts/ridge-performance/profile.mjs "$AFTER_URL" "$RIDGE_WORK/tail-after" "$RIDGE_WORK/tail-frames.json"
python3 scripts/ridge-performance/tail.py "$RIDGE_WORK" "$REPORT" summarize
TRIAL_URL="$AFTER_URL" TRIAL_EVIDENCE="$REPORT" node scripts/race-integration/regression.mjs
TRIAL_URL="$AFTER_URL" TRIAL_EVIDENCE="$REPORT" node scripts/race-integration/record.mjs
```

`performance.csv` は1行が予熱24・採用96実RAFの1試行。列 `mean_ms` は区間の算術平均、`fps` はその逆数×1000、`p95_ms` は昇順92番目。カメラとシミュレーションの1更新は30Hz固定。アニメーションの再生速度から実時間FPSを推定していない。

`cpu-gpu.csv` は各条件でフレーム25・41・57・73・89・105・120の7時点の平均。CPU時間はperformance.now、GPU時間は元の発行順を保った非重複のEXT_disjoint_timer_query_webgl2。各個体のメッシュの分類は元の所有者で決める。GPUの `sceneOther` は選択リング等、`course` は地面以外のコース・背景、`pixelMesh` と `sprite` は共有コンテキスト上のS型の生WebGL描画。タイマー解像度付近のCPU内訳は丸め誤差を含む。シミュレーション内のSリグ更新は別列、カメラとHUD内で参照する順位はそれぞれの呼出元に計上する。独立したシャドウマップ・深度プリパス・ポストプロセスは0回。通常の深度テスト・MSAAは各描画のGPU時間に含む。ブラウザのDOM合成時間はWebGLタイマーの対象外。CPUの `wait` は描画後に1画素を同期読み出しした時間であり、GPU時間と重なる。これらを足してRAF間隔にしない。

`quality.csv` 比較は同じ投影・走行状態で全画面RGBと、背景を一時的に隠した個体画像の差を算出する。後者には選択表示を含む。提出個体ID・LOD・姿勢、全個体の状態、カメラが改修前後で一致しなければ集計を停止する。`raw.zip` に全計時JSONと7時点の個票を格納した。実機では配布版の「実機計測」を使う。

`slow-replay.csv` は50・100体の各カメラ・画面幅で、実RAFの遅い3区間の直前フレームを同じ状態で再描画したもの。同期再生からブラウザのキュー待ちや合成の時間までは一意に復元できない。

比較ページと配布物は次で作成する。測定とテストの完了後に実行する。`frameplot.py` はMatplotlibを使用する。

```sh
python3 scripts/ridge-performance/frameplot.py "$RIDGE_WORK" "$REPORT"
python3 scripts/ridge-performance/review.py public/ridge-performance
node_modules/.bin/vite build --outDir "$RIDGE_WORK/package/evowild-test"
python3 scripts/race-integration/package.py "$RIDGE_WORK/package/evowild-test" public/ridge-performance/ridge-optimized.zip
unzip -q public/ridge-performance/ridge-optimized.zip -d "$RIDGE_WORK/unpacked"
python3 -m http.server 4203 --bind 127.0.0.1 --directory "$RIDGE_WORK/unpacked"
```

別シェルで `node scripts/ridge-performance/package-check.mjs http://127.0.0.1:4203/evowild-test/ "$RIDGE_WORK" "$REPORT/package-check.json"` を実行すると、展開したZIPでレース表示を切り替え、両動画、全比較画像、改修前後のJSONの読込を検証する。`RIDGE_ORIGIN=http://127.0.0.1:4202 node_modules/.bin/playwright test --config scripts/ridge-performance/race-test.config.mjs --workers 1` は通常ゲームの既存回帰を実行する。

100体のGPU原因を絞る対照試験は次の順に実行する。前者は地面だけを新版にして元のS表面を再生する。後者は全三角形・ディザ・深度を保ちSの表面色だけを定数にする診断で、採用FPSや画質の集計には入れない。

```sh
export RIDGE_CASE=pc-100-pixel-race,pc-100-pixel-follow,phone-100-pixel-race,phone-100-pixel-follow
RIDGE_ACTORS="$RIDGE_WORK/before/evowild-test/race-integration/probe-actors.js" node scripts/ridge-performance/profile.mjs "$AFTER_URL" "$RIDGE_WORK/ground-only"
RIDGE_FLAT_COLOR=1 node scripts/ridge-performance/profile.mjs "$AFTER_URL" "$RIDGE_WORK/flat-color"
unset RIDGE_CASE
python3 scripts/ridge-performance/diagnostics.py "$RIDGE_WORK" "$REPORT"
```

低速区間の追加試行は `node scripts/ridge-performance/trace.mjs "$AFTER_URL" "$RIDGE_WORK/chrome-trace.json"`、続いて `python3 scripts/ridge-performance/trace.py "$RIDGE_WORK/chrome-trace.json" "$REPORT/chrome-follow-100.csv"`。PC・100体Followで、24フレーム予熱後のコールバック間隔に重なるChromeイベントの和集合を各列で計算する。GPUプロセスのスケジューラタスク区間は実行中の待機を含む。診断完了後、`evidence.py` をもう一度実行すると対照試験の個票も `raw.zip` に加わる。
