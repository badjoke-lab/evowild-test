# S型立体スタディの再現

開始HEADは `a93fa4b65ea398d4e8ec0560c600f0d50abe1e72`。Node、既存npm依存、Python 3 + NumPy/Pillow、Blender 4.3、Chromium、ffmpegを使用する。過去のモデル生成スクリプトは起動しない。

```sh
npm ci
blender -b --threads 2 --python-exit-code 1 --python scripts/s-form/build.py
python3 scripts/s-form/anatomy-check.py
npx vite build --outDir /tmp/s-form-build
npx vite preview --outDir /tmp/s-form-build --host 0.0.0.0 --port 4186
```

別のターミナルで以下を順番に実行する。録画中に開発サーバーの自動再読込が起きないよう、検証はビルド済みファイルを使う。

```sh
export FORM_ORIGIN=http://localhost:4186/evowild-test/
export FORM_WORK=/tmp/evowild-s-form
node scripts/s-form/ui-check.mjs
node scripts/s-form/compare.mjs
node scripts/s-form/studio-capture.mjs
python3 scripts/s-form/plates.py "$FORM_WORK"
node scripts/s-form/record.mjs
node scripts/s-form/regression.mjs
python3 scripts/s-form/package.py /tmp/s-form-build
```

`compare.mjs` は旧レンダラーをそのまま読み込み、静止姿勢の128層原本とv4.1表面を描画する。旧アプリのソースファイルは書き換えない。新旧のカメラと切出し倍率をJSONに保存する。上面の原画は尾の部分図として掲載する。

`regression.mjs` は既存ゲームへ固定フレーム入力を渡し、1・18・50体の旧v4.1と修正版を同じ7地点で照合する。実時間動画は `record.mjs` で別に収録し、FPSの採用試験には流用しない。`ui-check.mjs` は24位相の実GLB変形頂点、位相選択、静止／走行、視点、無彩色表示を確認する。

形状は `build.py` の断面列、白い面の境界、`REST` の関節位置、尾の枝から生成される。既存データから使うのは参照画像のSHA、17色パレット、位相・接地・足先軌道の記録。旧ボクセル、旧メッシュから頂点を転用しない。足先軌道の前後幅は0.75倍、前後脚の関節解法は新規。ゲーム側の速度・進路には書き戻さない。

Blenderファイルは部位ごとの頂点グループと24形状キーを持つ。生成後にBlenderで編集した場合は、そのファイルを保存し、GLBを再出力する。コードからの再生成は手編集を上書きするため、手編集版を別名に保存してから行う。
