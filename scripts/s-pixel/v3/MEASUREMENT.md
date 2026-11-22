# レース条件の再計測

`public/s-pixel-lab/v3/scenarios.js` が観察室・動画・計測で使えるカメラと走行状態を返す。各条件は同じ3秒のカーブを走る。走行時間、画面寸法、コースの中心軌道からカメラ方位・俯角・倍率を求める。遅い描画でも同じ48時点を順に表示するため、両版で同じ足運びとカメラを比較できる。撮影軌道の再生速度と、実時間で測ったフレームレートは別々に記録する。

`near1` は1体を追走し、`near10` はカーブの接線に追従しながら10体の隊列を手前から見る。`mixed50` と `mixed100` はカーブの奥行きに沿って近景・中景・遠景を同時に映す。`overview100` は100体を倍率約1倍で見渡す。同じ個体数でも、カメラによって各方式が処理する個体数は異なる。生データには毎フレームの描画内訳と、保守的な個体境界が画面に交差する数、中心が入る数、境界全体が入る数を収録する。個体同士の遮蔽は境界テストの対象外。

リポジトリの `public` を HTTP で配信して実行する。`LAB_BASE_URL` で観察室のルートを指定できる。既定値は `http://127.0.0.1:4173/s-pixel-lab/`。Linux・Chromium・SwiftShader・Playwrightを使用する。

```sh
node scripts/s-pixel/v3/measure.mjs v2
node scripts/s-pixel/v3/measure.mjs v3
node scripts/s-pixel/v3/race-table.mjs
```

- PC幅は1280×900、描画877×414、CPU制限なし。スマホ幅は390×844、描画352×335、CPU 4倍減速、タッチ・モバイル設定。同じChromiumのソフトウェアGPUを使用する。物理スマートフォンの実測は別途必要。
- 全条件で24走行ポーズを使用する。3フレーム予熱し、各フレームはRAFで開始、WebGLコマンド発行後に中央1画素の同期 `readPixels` を呼ぶ。平均fpsは実時間の合計から算出し、p95は48個のフレーム間隔を昇順に並べた46番目を採用。GPU時間は `EXT_disjoint_timer_query_webgl2` の有効な描画区間を集計する。フレーム落ちに伴う走行時刻の飛びを防ぐため、同一時点の列を両版で固定している。
- 測定対象の俯角に必要なスプライトは予熱前にロードする。数値は素材ロード後の定常走行である。GPU描画時間、JSの発行時間、同期読出し完了までの時間を分けて保存する。三角形数・描画呼び出しは床・影・個体を含み、インスタンス数も掛け合わせる。Framebuffer転送は別列に記録する。
- GLメモリはWebGL描画コンテキストの生存バッファ、色・深度テクスチャ（配列とミップを含む）、レンダーバッファの論理割当量。ブラウザ管理の既定Framebufferとドライバ内部領域は含めない。JSはCDPの使用ヒープ。RSSはLinuxでChromiumプロセスごとの `VmRSS` を合算するので共有ページが重複しうる。
- `MEASURE_PROFILE=desktop|mobile`、`MEASURE_RACE=near1|near10|mixed50|mixed100|overview100`、`MEASURE_METHOD=lod|surface|exact|stack`、`MEASURE_FRAMES`、`MEASURE_OUT` で部分検査もできる。部分検査では `MEASURE_OUT` を別ファイルに指定する。標準比較は両版で `lod` と48フレームを使用する。

各条件の生データは `public/s-pixel-lab/v3/evidence/v2-race.json` と `v3-race.json`、同条件の一覧は `race-performance.csv` にある。
