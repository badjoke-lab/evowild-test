# Game Studio — 既存3Dレース単独評価

実施日: 2026-10-09 UTC。作業ブランチ: `exp/gamestudio-3d-20261010`。基点: `610d42800180ed31f174a097fc2eb96c27ecd0ab`。対象は `public/preview-motion-first-race/` と共有実装 `public/preview-motion-first/main.js`。

**実証できた改善は、外部CDNに依存しない起動、Androidでのレース可視領域、入力操作、固定色バッファの更新削減、再現可能な検証工程である。造形・歩様・接地の改善、およびFPSの一貫した向上は実証していない。2.5Dとの優劣は判定しない。**

Game Studio は導入済みスキルとして利用可能だった。以下の `SKILL.md` を読み、その手順を実際のコード・検証に適用した。専用生成APIを実行したという意味ではない。

| 実際に使用したGame Studioスキル | 実行内容 |
|---|---|
| `game-studio:three-webgl-game` | 既存の固定60Hzシミュレーションと描画の分離を維持。Three.jsのインスタンス属性更新を確認し、変更された色スロットだけを更新。FPS表示に実時間を使用。 |
| `game-studio:web-3d-asset-pipeline` | 正規参照・モデル・リグ・アニメーションのハッシュとGLB構造を監査。モデル採用状態、依存ファイル、骨数、クリップ、境界・三角形数を記録。Three.js 0.181.0をライセンス・SHA-256付きで同梱。 |
| `game-studio:game-playtest` | Playwrightで18体、4カメラ、Android/desktop、手動フォーカス、入力、停止・再開、レース完走、画面被覆、動画、描画性能、実際の足位置を検証。 |
| `game-studio:game-ui-frontend` | 管理情報と設定を開閉式に変更。モバイルのカメラボタンを44px高にし、フォーカス表示と画面サイズ変更時の設定アクセスを確認。 |

Sprite Pipeline、Phaser、React Three Fiber、Tripo、画像/モデル生成、Blender編集、glTF Transform、SpectorJS、Rapier、新規リグ作成は使用していない。

承認済み参照は [正規参照シート](../../references/evowild-creature-reference-sheet-20260921.jpg)、[参照索引](../../creature-reference-index-v0.1.md)、既存 `public/concept/S.webp / P.webp / E.webp / A.webp`。Sは細身・長脚、Pは厚い胴と重い四肢、Eは長く細い胴、Aは低く柔軟な体という基準を確認した。

対象ページは従来から**18体の簡略プロキシ**を使い、関節・脚IK・4モルフの既存ソルバーで動く。通常走行では正規Hunyuan GLBを読み込まない。Sの正規形状系列は `source-lod2.glb`、現行候補は `focus-rigged-v5.glb` / `race-lod4-rigged-v5.glb`。v5は19骨、`EvoWild_S_Run_V5`（58チャンネル）を持つが、最終アート承認済みではない。今回のGLB実データではfocus 12,939 / race 3,233三角形であり、一部の既存文書の概数と異なる。監査対象GLBに外部URIはなかった。

`v31` はREJECT済みとして棚卸ししただけで、採用・読み込みしていない。旧プリミティブSを正規造形として再承認していない。対象ページが以前から使うプロキシを維持した評価であり、新しいレーンや代替クリーチャーの制作・昇格は行っていない。既存の簡略レーンの承認記録と、正規S造形の承認条件を混同しない。

| 検証項目 | Before | After | 判断 |
|---|---|---|---|
| この環境での通常起動 | unpkgへの接続失敗で起動不可 | 同梱の同一Three.js 0.181.0で起動 | 改善 |
| AndroidのUI被覆面積 | 73.2% | 25.5% | 改善。初期状態の矩形和集合を4 CSS px刻みで計測 |
| DesktopのUI被覆面積 | 24.3% | 22.0% | 小幅改善 |
| 所有者入力欄で `PLAYER` + Space + `2` | `PLAYER2`、レース停止、CHASEへ切替 | `PLAYER 2`、走行とFRONTを維持 | 修正 |
| 15個の色属性version増分（動画測定区間） | Desktop各503 / Android各574 | すべて0 | 静的色の不要な更新を削減。色変更時の再更新もテスト |
| 描画負荷 | 29 draw calls / 36,940 triangles | 同一 | 形状・画質を削っていない |
| FPS表示 | 120msで上限処理した時間を使用 | 実際の経過時間を使用 | 長い停止を隠さない表示に修正。シミュレーションの上限は維持 |

FPSは同じ機器条件、録画と読み取り用プローブを有効にした各5秒の実測。最良値の選別はしていない。プローブを除いた製品性能や実機Androidの性能を表すものではない。

| カメラ | Desktop Before → After FPS | Androidエミュレーション Before → After FPS |
|---|---:|---:|
| SIDE | 17.3 → 18.6 | 21.3 → 23.4 |
| LOW | 18.9 → 18.5 | 23.8 → 21.9 |
| CHASE | 19.7 → 17.4 | 22.1 → 22.2 |
| FRONT | 18.5 → 20.3 | 21.5 → 23.1 |

フレームp95は約50–67ms。FPSの全体的改善とは判定しない。詳細な生データ、環境、区間、描画数は [comparison.json](comparison.json) と各ディレクトリの `raw.json.gz` にある。

造形は正規参照に対して依然として粗い代理表現であり、頭部・角・胴体表面の同一性を最終アート基準で合格とはできない。既存の個体識別色も正規コンセプトの配色再現ではない。4モルフの体格差はあるが、18体が重なる場面、LOWの近距離遮蔽、縦長画面のSIDEで画面外に切れる身体は識別しにくい。UIを減らして観察できる面積は増えたが、カメラ配置や造形は変更していない。

歩様には関節運動、胴体の上下動、尾の追従がある。一方、既存 `maxStanceSlip` はソルバー目標点の指標で、描画後の足先の接地保証ではなかった。このため追加で、18体の実際の足/つま先変換を毎描画フレーム・6秒間読み取り、トラック面Y=0との距離を測った。

| モルフ | After desktop 接地期間の足底クリアランス中央値 / 最小値 (m) | 接地期間の足中心移動の観測最大 Before → After (m) |
|---|---:|---:|
| S | +0.012 / -0.412 | 0.398 → 0.385 |
| P | -0.161 / -0.470 | 0.348 → 0.349 |
| E | -0.109 / -0.408 | 0.160 → 0.160 |
| A | -0.127 / -0.453 | 0.233 → 0.238 |

元の標本は草地Y=-0.12を基準にした値だったため、最終比較ではその基準面を明記して実際のトラック面Y=0へ再計算した。標本自体は変更していない。正値は浮き、負値は地面への貫通を示す境界箱ベースの診断値。足中心移動には回転・体の傾きも含まれ、厳密な接触点の摩擦滑りではない。描画間の最大移動を捉えきらないため下限値でもある。Androidでも同種の問題が残る。前後の標本位相は完全には一致せず、小さな数値差を改善とは扱わない。**接地・足滑りの品質合格、モーション改善は主張しない。** 初回の動画用10Hz標本では同一接地中の連続標本が不足したため、別途毎フレーム測定を追加した。

保護対象20ファイルと、形状・プロファイル・関節構造・レース状態・ソルバー・カメラ/自動ディレクターのソース領域は基点とハッシュ一致。[preservation.json](preservation.json)、[Before監査](before/asset-audit.json)、[After監査](after/asset-audit.json)を参照。S/P/E/Aのデザイン、正規参照、モデル、骨、アニメーションクリップ、18体のレース構造、距離・コース・エージェント/交通処理を維持した。mainの変更・マージはしていない。

証拠は以下に保存した。通常走行動画は各環境でSIDE → LOW → CHASE → FRONTを連続収録し、各カメラで実際の中位の個体を選択している。カメラ変更後にフォーカスを指定し、AUTOによる選択上書きを避けている。

| 環境 | Before | After |
|---|---|---|
| Desktop | [連続動画](before/desktop/side-low-chase-front.webm) / [SIDE画像](before/desktop/side.png) | [連続動画](after/desktop/side-low-chase-front.webm) / [SIDE画像](after/desktop/side.png) |
| Android | [連続動画](before/android/side-low-chase-front.webm) / [SIDE画像](before/android/side.png) | [連続動画](after/android/side-low-chase-front.webm) / [SIDE画像](after/android/side.png) |

同じ各フォルダに `low.png`、`chase.png`、`front.png`、`raw.json.gz`、`contact-frames.json.gz` がある。[動画一覧フレーム](after/desktop/video-review-contact-sheet.jpg)は2秒間隔の抜き出し。`after/desktop/isolated-{S,P,E,A}-{SIDE,LOW}.png` は既存 `proxyReviewRunner` モードの補足画像で、18体通常表示の証拠とは区別する。

Beforeの無改変起動失敗は [画像](before/stock-boot-failure.png) と [エラー](before/stock-boot-failure.json) に保存。走行Beforeは、テスト側でunpkgリクエストを公式npmの同一バージョンのファイルに置換して撮影した。Afterはこの置換なしでローカルファイルを使用。補足接地比較は基点の `main.js` と変更後の `main.js` を、同一の現在UI・ローカルThree.js上で別々に実行した。ゲーム状態やポーズを外部から書き換える測定ではない。

実行環境: Linux x64、Node 24.19.0、npm 11.9.0、Playwright 1.64.0、Vite 7.3.7、Chromium 151.0.7922.173、ANGLE Vulkan SwiftShader。Desktop 1280×720 / DPR1、Pixel 7エミュレーション 412×839 / DPR2.625・touch。Three.jsは対象ページでは0.181.0、ルートnpm依存は0.181.2。レンダリング解像度倍率0.75は既存値のまま。AndroidのUAはPlaywrightの端末プリセットであり、実際のブラウザ版は151。実機GPU・実機Android・長時間の熱/電池/メモリ検証は未実施。

After録画はコミット前の変更済み作業ツリーで撮影したため、生データの `sourceCommit` は撮影時HEAD（基点）を記録している。変更実装はこの証拠を含むコミットの差分を参照する。録画後の追加修正はfavicon 404と、モバイルで閉じたSETUPを広い画面へ変更した後も開けるようにする処理で、レース描画・ポーズは変わらない。

検証結果の最終一覧は [validation.json](validation.json)。初回の追加テスト8件は [tests.log](tests.log) / [tests.json](tests.json)。既存の対象8件は [existing-tests.log](existing-tests.log) / [existing-tests.json](existing-tests.json)。最初の既存テストは `/favicon.ico` の404で失敗し、対象ページに空のfavicon指定を加えて修正した。失敗を消さず [trace](favicon-failure-trace.zip) を保存し、修正後の結果は [existing-recheck.log](existing-recheck.log)。既存テストのFPS計測には既存の再測定処理があるため、上の前後比較表には使用していない。

再実行はリポジトリルートで以下を使用する。ブラウザとffmpegは環境にインストール済みのものを使用した。Playwright標準ブラウザを用意する環境では `CHROMIUM_PATH` を適切に設定する。ポート4173はこのリポジトリのサーバーに限定して使用する。

```sh
npm install
npm run dev -- --host 127.0.0.1 --port 4173 --strictPort
# 別のシェルで実行
PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright node scripts/gamestudio-3d/capture.mjs after
node scripts/gamestudio-3d/contact-review.mjs
node scripts/gamestudio-3d/summarize.mjs > docs/evidence/gamestudio-3d-20261010/comparison.json
node scripts/gamestudio-3d/audit-assets.mjs
node scripts/gamestudio-3d/check-preservation.mjs
npx playwright test --config=playwright.gamestudio-3d.config.js tests/gamestudio-3d.spec.js
npm run build
```

Beforeの再撮影は、別ディレクトリへ `npm install --prefix /tmp/evowild-three-baseline --save-exact three@0.181.0` で取得し、`THREE_BASELINE_DIR=/tmp/evowild-three-baseline/node_modules/three` を指定して `capture.mjs before` を実行する。基点コミットのHTML/JSを読み出すので、作業ツリーを切り替える必要はない。再撮影は既存証拠を上書きするため、保存先を分ける場合は `EVIDENCE_DIR` を指定する。同梱ファイルの再生成は `vendor-three.mjs /path/to/three@0.181.0`。`vendor/three/manifest.json` とMITライセンスを同梱している。
