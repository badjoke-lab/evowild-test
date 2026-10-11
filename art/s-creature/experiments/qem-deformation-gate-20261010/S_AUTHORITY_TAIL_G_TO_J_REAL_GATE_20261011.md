# EvoWild Run S型 — 正式基準画像からの尾G–J実メッシュ検証 / 2026-10-11

## 最優先・絶対変更禁止の基準

**ユーザー指定の唯一の最上位基準画像**：
`art/s-creature/references/00_s_type_modeling_image_v1.png`
SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`。
GitHub blob SHA `34e92e5f56e12f611b59c62381f7bc1f1ff015bc`。
この画像は「EvoWild Run / S TYPE / SPRINT MORPH」デザインシート。**生成した別画像を基準にしない**。各GH Actionsは画像SHAを直接照合した。

元TRELLIS2 QEM donor GLBは `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`、SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`、29,948 vertices / 59,932 triangles。本体は一切上書きしていない。

## 元画像・現物を横に並べた比較

`tail-authority-lamina-g-v1/review/REFERENCE_VS_REAL_QEM_TAIL_G.jpg`
`tail-authority-blades-h-v1/review/REFERENCE_VS_REAL_QEM_TAIL_H.jpg`

上記の左列が *SHA検証済み上位基準の実画像クロップ*、中央が元のTRELLIS2 QEM-A、右列がBlender実モデル試作。基準のTailは**長い複数の流線形装甲羽根が重なり、臀部から後方へ自然に流れる形**。現行QEMにはその構造がない。

## 実験結果は不合格として保存

| 試験 | 実際の派生QEMメッシュ | manifold | BVH非共有三角面同士の自己交差 | 造形・結果 |
| --- | --- | --- | --- | --- |
| A / 元の短い尾を延長 | 29,948 / 59,932 | 既存評価 | **0（このH監査と同一ROI）** | 原画の尾装甲と異なる |
| G / 6本のskin-connected swept loft | **31,145頂点 / 62,326面** | 連結1、境界0、退化0 | **2,473** | 細枝状、REJECT |
| H / 3本の幅広の羽根 | **30,540頂点 / 61,116面** | 連結1、境界0、退化0 | **824** | 鉤状・不自然、REJECT |
| I / H自己交差の詳細分類 | H据え置き | 非改変 | **573：新羽根→元の尾、238：新羽根同士、13：その他（近似分類）** | 失敗原因明確化 |
| J / 新羽根を元の表面から離す20候補 | Hと同一トポロジー + shape key | 元Hを非改変 | **最良の三角面品質PASS候補でも841** | 改善せず、REJECT |

**注意**：Jの形状面積・反転テストがPASSでも、自己交差は824→841と増えた。GH Actions runのSUCCESSはproduction approvalと無関係。交差があるため使用不可。

実QAファイル：
- G `tail-authority-lamina-g-v1/QEM_G_REAL_TAIL_LOFT_QA.json`
- H `tail-authority-blades-h-v1/QEM_H_REAL_TAIL_BLADES_QA.json`
- I `tail-intersection-audit-i-v1/QEM_H_TAIL_COLLISION_LOCATION_QA.json`
- J `tail-surface-clearance-j-v1/QEM_J_SURFACE_CLEARANCE_QA.json`

修正可能な実Blender：
- G `tail-authority-lamina-g-v1/S-QEM-real-connected-tail-lamina-loft-G-TRIAL.blend`
- H `tail-authority-blades-h-v1/S-QEM-real-connected-tail-blades-H-TRIAL.blend`
- J `tail-surface-clearance-j-v1/S-QEM-real-surface-clearance-J-TRIAL.blend`

## 結論と次の作業条件

**G/H/Jは幾何学的・視覚的に不合格。完成S=0。main未変更。**

「Aの尾から適当なface islandsを選びロフト／押し出し／局所移動」というG–J方式はこれ以上連続試行しない。尾の体積・装甲羽根の分岐・羽根同士の上下/前後配置・根元の接続を**最上位基準側面/背面/3/4図から同時に設計**し、新たな一体型尾トポロジーとして構築し直す必要がある。前提として実メッシュのBVH自己交差0、連結成分1、非多様体0、造形5方向一致を別々に評価。**ただし基準画像が示さない左右厚みなどは3/4/back viewから検証**。その後にのみskin weights・tail bones・13-bone gait compatibilityを確認する。

現行 QEM 13ボーン・3周期IKのlimited PASSは**変更前の別メッシュだけ**に適用される。形状を変更したG/H/Jへ合格結果を流用禁止。無承認production merge不可。
