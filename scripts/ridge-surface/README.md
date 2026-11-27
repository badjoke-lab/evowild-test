# 統合表面の限定試験を再現する

基準は `2606922a521ae9d9d8a4563824c22b13f2d12815`。Three.js本体、ゲームのシミュレーション、既存デモの配布物から同一の条件を構築する。Chromium、Node、既存のnode_modules、Python 3、NumPy、Pillow、ffmpegを使用する。

```sh
export SURFACE_WORK="$(mktemp -d)"
mkdir -p "$SURFACE_WORK/site"
unzip -q public/ridge-performance/ridge-optimized.zip -d "$SURFACE_WORK/site"
node scripts/ridge-performance/build-probe.mjs "$SURFACE_WORK/site/evowild-test" 2606922a521ae9d9d8a4563824c22b13f2d12815
node scripts/ridge-surface/prepare.mjs "$SURFACE_WORK/site/evowild-test" "$SURFACE_WORK/variants"
python3 -m http.server 4210 --bind 127.0.0.1 --directory "$SURFACE_WORK/site"
```

別シェルでも同じ `SURFACE_WORK` を指定し、次を順次実行する。試作はブラウザのモジュール読込を置き換えて実際のゲームに適用する。計測ページの負荷プローブは採用FPS測定から分離している。

```sh
for mode in base group color both; do
  if test "$mode" = base; then
    unset RIDGE_ACTORS
  else
    export RIDGE_ACTORS="$SURFACE_WORK/variants/$mode-probe.js"
  fi
  node scripts/ridge-surface/profile.mjs http://127.0.0.1:4210/evowild-test/ "$SURFACE_WORK/profile-$mode"
done
export RIDGE_CASE=pc-18-pixel-race,pc-18-pixel-follow,pc-50-pixel-race,pc-50-pixel-follow,pc-100-pixel-race,pc-100-pixel-follow,phone-18-pixel-race,phone-18-pixel-follow,phone-50-pixel-race,phone-50-pixel-follow,phone-100-pixel-race,phone-100-pixel-follow
for mode in base group color both; do
  if test "$mode" = base; then
    unset RIDGE_ACTORS
  else
    export RIDGE_ACTORS="$SURFACE_WORK/variants/$mode.js"
  fi
  node scripts/ridge-performance/accept.mjs http://127.0.0.1:4210/evowild-test/ "$SURFACE_WORK/accept-$mode"
done
unset RIDGE_ACTORS RIDGE_CASE
python3 scripts/ridge-surface/report.py "$SURFACE_WORK" public/ridge-surface/evidence
bash scripts/ridge-surface/verify.sh "$SURFACE_WORK"
```

基準、群、単色、併用で各24条件×7時点を検証し、実RAFは各12ピクセル条件×96区間を測る。通常18体、S型50・100体、Race／Follow、PC幅／スマホ幅。7時点は元の25・41・57・73・89・105・120フレーム。24予熱＋96測定、描画サイズ、タッチ判定、DPRは前の試験と同じ。

GPUはEXT_disjoint_timer_query_webgl2で元の提出順を区間計時、CPUはperformance.now。完了待ちは描画後に1画素を同期読み出しする時間。これらを合算して実RAF時間とはしない。`profile.mjs` は前のドライバーを再利用し、群数・単色該当数の取得だけを追加している。

手元のPCまたは同じWi-Fiのスマホから操作するには、リポジトリで `python3 scripts/ridge-surface/serve.py` を起動してポート8000を開く。基準ZIPを検算して読み込み、4つのURLで同じレースを配信する。各試作の色・群処理は明示的に選択したURLに適用される。基準ZIPはリポジトリに同梱済み。候補を再生成した場合、`$SURFACE_WORK/variants/{group,color,both}.js` を `public/ridge-surface/variants/` にコピーする。

実機のJSONには配信サーバーが候補を示す統合ビルド名を付ける。画面の向きと実描画サイズを固定し、基準と各候補を交互に各3回測る。

`gpu.csv` の三角形削減率はWebGLへ実際に提出したインスタンス込みの三角形数を基準版と比較する。`raw.zip` の `surface.trianglesBefore` は個別裏面除去も行う前の原始メッシュ数で、採用表の比較分母には使わない。GPU負荷表にはCPUの姿勢・LOD、メッシュ提出、完了待ちも含む。

各方式の回帰は、Sのみ1・10・50・100体と通常18体混走の7チェックポイント、さらにSTARTからFINALまでのブロック・追越し・順位変動を検証する。基準と併用の動画はそれぞれ独立の実時間収録で、同時刻の画質判定には固定時点のPNGを使用する。

非同期読込の追加回帰は、試験サーバー起動後に `node scripts/ridge-surface/async-load.mjs http://localhost:8000 public/ridge-surface/evidence/async-load.json` で実行する。paint.gzの読込を500 ms遅延させ、その間も元のレースを進める。候補読込の前後で既存の頂点配列の索引・属性バッファ・有効化・型・オフセットを検算する。

集計後に `python3 scripts/ridge-surface/finalize.py` と `python3 scripts/ridge-surface/view.py` で報告書と比較ページを生成する。ビルドは `node_modules/.bin/vite build --outDir "$SURFACE_WORK/build"`。既存モデルの生成スクリプトを経由せず、保存済みのモデルを使用する。
