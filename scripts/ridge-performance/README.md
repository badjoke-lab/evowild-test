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
