# S型 肩の接続面構造の造形 — 2026-10-15

**肩の局所改善としてKEEP。全身最終V5の承認ではありません。** 作業者自身による画面・実レンダリング比較です。独立した第三者レビューとは扱いません。

保存モデルは `S_HUNYUAN_SHOULDER_LAYER_PILOT.blend`。片側が完成した時点は `S_HUNYUAN_SHOULDER_LAYER_RIGHT_FINAL.blend`。元のV5_STAGE1から開始し、REVISEのStage2候補は使用していません。最初に `review-v5-stage2-candidate/INDEPENDENT_ART_REVIEW.md` をgitのHEADから読みました（この作業ツリーでは同ディレクトリがsparse checkout対象外）。

## 目で確認する成果

- [原画 / Stage1 / 両側造形のSIDE・FRONT・FRONT34比較](CANONICAL_STAGE1_LAYER_PILOT.jpg)
- [原画 / Stage1 / 片側完成時点の比較](CANONICAL_STAGE1_RIGHT_FINAL.jpg)
- [原画と全身5方向比較](CANONICAL_STAGE1_LAYER_FIVE_VIEWS.jpg)
- [反対側の実レンダリング](LAYER_PILOT_DETAIL_LEFT_FRONT34.png)
- [SIDEの実メッシュlandmark](STAGE1_LANDMARKS_SIDE.jpg)、[FRONT34](STAGE1_LANDMARKS_FRONT34.jpg)

Stage1の大きな平坦な肩外側を、斜めに流れる肩板として組み直しました。肩板の前側は胸の量感へ戻り、後縁・下縁には薄い接続面があります。下端付近の谷と近位上腕の膨らみを分け、正面の肩周りを絞っています。SIDEとFRONT34では板の縁と上腕への切り替わりが以前より明確です。FRONTでは横に広い上部の塊を抑えています。

原画の滑らかな面の流れに比べると、上端・後縁の角と面分割には硬さが残ります。今回は「以前の平坦な塊から、目で分かる肩の面構造へ進めた」という局所判断です。頭・冠・尾・脚などの原画との差は今回の編集範囲に含めません。

## 実際の編集

Blender **4.3.2** のユーザーのライブGUIを **Blender MCP** で操作しました。右肩だけを先に造形し、SIDE・FRONT・FRONT34を操作ごとに `look` で確認しました。片側の実Cycles比較と背面側確認を終え、`ONE_SIDE_ART_GATE.json` を書いてから反対側に同じ局所構造を展開しました。全身の置換や別球体の貼り付けはしていません。

採用した編集は、既存三角面を板の輪郭で切り、内部の面・頂点を局所的に置き換え、既存の境界ループにつながる戻り面と板の面を作るトポロジー変更です。肩板、胸との谷、上腕の量感を作り、最後に肩の奥行き全体に連続する横方向の絞りを加えました。反対側には元メッシュの非対称を保ったまま同じ手順を適用し、先に造形した側が変わっていないことも検査しています。

不採用案は取り消しました。最初の面置換はギザつく外周、Inset案は面交差、小さな肩板と多項式面の案は貼り付けた印象や上端の形、上端を下げる案は根元の折れが理由です。`*_REJECTED.json` と画面記録に残しています。採用案は小さい頂点差分の候補検索ではありません。

## 比較と検証

実Cyclesレンダリングは1000×800、24 samples、同じクレイ材質・照明です。Stage1との肩の比較3方向はカメラ位置・向き・ortho scale・照明も一致させています。最終モデルには全身5方向と肩3方向、反対側FRONT34があります。各最終レンダリングの設定は `*_RENDER.json` に記録しました。比較画像は実画像の切り出しと配置のみで、造形の描き直しやAI画像生成はしていません。REAR34には直接の原画がないため、3Dの整合確認として表示しています。

`FINAL_GEOMETRY_VERIFICATION.json`、`SAVE_RELOAD_VERIFIED.json` に実測結果を保存しています。

| 検査 | Stage1 | 保存したモデル |
|---|---:|---:|
| 頂点 | 38,802 | 40,957 |
| 三角化後の面 | 77,684 | 81,994 |
| 連結成分 | 7 | 7 |
| 非多様体エッジ | 0 | 0 |
| 面積1e-12未満の三角面 | 2 | 2 |
| 非隣接三角面のBVH交差候補 | 7 | 7（同一の既存箇所） |

新規のBVH交差候補、連結成分、縮退面は増えていません。BVH検査は頂点を共有する三角面同士を除外する表面検査で、あらゆる接触の不存在の数学的証明ではありません。元の7成分・2つの極小面・7つの交差候補を修理したとは主張しません。新しい肩板と戻り面は、それぞれ元の肩の成分に接続されています。

肩ROI外の頂点座標は完全一致。反対側への展開で完成済みの側も完全一致。Blenderのnative mesh validationはStage1・候補のコピーの両方で変更なしでした。最終保存データは1メッシュオブジェクト・1メッシュデータブロックに整理し、ロールバック用の未使用データを除去しました。再読込で座標と面ループのSHA256 fingerprintが完全一致し、基準画像5枚もblend内にpackされています。

元Hunyuan、v3、v4、V5_STAGE1、既存WORKING、基準画像の、ローカルに存在する保護対象6件は作業前後のSHA256が一致しています（`PROTECTED_BEFORE.json`）。sparse checkout未展開のv1・v2にも操作を加えていません。既存の追跡ファイルには変更を加えず、mainは操作していません。開始時からあった未追跡の失敗記録も保持しています。

## 確認画面と再現用スクリプト

`viewport-evidence/` はBlenderウィンドウ全体の実スクリーンショットの縮小JPEGです。原寸PNGはローカルの同ディレクトリ直下に保持し、原寸とJPEGのhashは `VIEWPORT_CAPTURE_MANIFEST.json` に記録しました。landmark画像はStage1の実画面に、実頂点位置から投影した診断ラベルを重ねたものです。macOSのlogical window寸法とframebuffer寸法を区別しています。

再現用スクリプトは `art/s-creature/blender/s_hunyuan_shoulder_*pilot*.py`。採用した順序は preparation (`s_hunyuan_shoulder_structure_pilot.py`) → connected_sheet → chest_arm → taper。右側で確認した後に `SIDE=-1` で反対側へ適用します。各操作後の実画面確認を省かず、スクリプトを現在の完成モデルへ重ねて実行しないでください。`retopology.py` と `sheet.py` は不採用手法の記録です。保存・再読込・レンダリング・比較作成スクリプトも同じ場所にあります。
