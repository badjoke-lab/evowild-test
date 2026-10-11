# EvoWild Run — S 型 最上位基準固定、S/T/U 実メッシュ判定 (2026-10-11)

## 唯一の最上位基準とImmutableドナー

- 造形基準: `art/s-creature/references/00_s_type_modeling_image_v1.png`、SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`。ユーザー承認済み、勝手に差し替え禁止。
- ドナーは真のTRELLIS2 repaired QEM：`art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`、SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`、**29,948 頂点 / 59,932 三角面**。
- 三候補の原型：M の一体型尾（31,948 頂点 / 63,932 三角面）から、一枚の皮膚パッチを実際に切除して対応する立体羽根を接合した各 Q 単独モデル。
- Q の各単独メッシュは1連結・境界辺0・非多様体辺0・退化面0。修正 S/U は形状キーによる頂点編集のみで、Q メッシュトポロジーは変更しない。
- Source QEM、M、元Qは実 Blender 4.3.2 で再評価し、非改変検証を実施。

## S：中央の一枚の自己交差ゼロを実現

基準 Q `MID_LEFT` は、実際の非共有三角面BVH交差 **5組**。事前フォレンジックで5組の頂点座標、ポリゴン番号・法線を取得：`exp/s-qem-midleaf-rootrepair-s-20261011` の `midleaf-forensic-s-v1/ACTUAL_QEM_MIDLEAF_FIVE_FACE_FORENSIC.json`。

異常箇所はいずれも **最初の接続リング Y≈2.30–2.32**。原型Qの固定6桁頂点SHA-256 `b5e0cdc2d15a79e3f15d6dcfff686fd053651e2d5844cae2e2479aeb96055130` をチェックし、元M頂点には一切触らず新しいリングの **51頂点を局所加重**。X の外側へ最大 **0.006** の微小移動で一度目の候補が PASS。

| 検証 | S 判定 |
| --- | --- |
| 自己交差（定義済み尾ROI内 BVHTree） | **5→0** |
| 新しい三角面反転 / 退化 / 面積0.5倍未満 / 2倍超 | **0 / 0 / 0 / 0** |
| 最小・最大三角面面積比（Q原型比） | **0.550804 / 1.481281** |
| 立体メッシュ接続 / 共有辺の有向整合 | 元Q同一トポロジー、**PASS** |
| 編集対象 | 新しい中央羽根接続リングの近傍のみ |
| 最上位S型基準の形状一致 / 13ボーン / 三周期走行 | **未合格・未再検証** |

実 Blender：`exp/s-qem-midleaf-rootrepair-s-20261011` の `midleaf-rootclearance-s-v1/S-QEM-MIDLEFT-first-ring-root-repair-S-TRIAL.blend`。
証拠：同フォルダの `REAL_QEM_MIDLEAF_ROOT_S_QA.json`、`review/ACTUAL_QEM_MIDLEAF_S_FIVE_VIEW.jpg`、`review/ACTUAL_QEM_MIDLEAF_S_ROOT_DETAIL.jpg`。
GitHub Actions [38113768624](https://github.com/badjoke-lab/evowild-test/actions/runs/38113768624) は Blender+証拠保存 SUCCESS。**一枚だけの技術PASSであり、S型造形承認ではない。**

## T：残り二枚の原因の実座標特定

Q 単独モデルをそのまま使用し、同じBVH定義で交差を再測定。

- **根元側 PROXIMAL_RIGHT：34組**
- **先端側 DISTAL_RIGHT：152組**
- 二枚とも **全交差がそれぞれの最初のリング付近（根元からY方向0.17未満）**に集中。
- 各実ポリゴンID・3D頂点座標・関与新リング頂点の頻度・原型の最近接Mメッシュとの距離を保存。

現物：`exp/s-qem-remaining-tail-root-audit-t-20261011` の `tail-remaining-forensic-t-proximal_right/` と `tail-remaining-forensic-t-distal_right/`、各 `REAL_QEM_T_REMAINING_LEAF_COLLISION_MAP.json`。Actions [38114011018](https://github.com/badjoke-lab/evowild-test/actions/runs/38114011018) SUCCESS。

## U：Sと同じ手法を残り2枚に適用（各45候補）

同じ最上位基準と元QEMドナーを毎実行SHAチェック。元のQ単独実Blenderファイルをそれぞれ直接読み、接続リングの新しい頂点だけを外側/上下方向へ加重移動。**根元側と先端側は技術FAIL**。

| 装甲 | Q時点の交差 | Uの最良交差 | 新規面反転・退化・0.5倍未満・2倍超 | 技術判定 |
| --- | ---: | ---: | --- | --- |
| 中央 | 5 | **S：0** | 0・0・0・0 | **S の1枚のみPASS** |
| 根元側 | 34 | **24** | 0・0・0・0 | FAIL |
| 先端側 | 152 | **119** | 0・0・0・0 | FAIL |

U各45候補、計90候補を Blender 4.3.2 で実行。詳細 `tail-otherleaf-clearance-u-proximal_right/REAL_QEM_OTHERLEAF_U_QA.json`、`tail-otherleaf-clearance-u-distal_right/REAL_QEM_OTHERLEAF_U_QA.json`。保存した実Blenderはそれぞれ `S-QEM-PROXIMAL_RIGHT-first-ring-clearance-U-TRIAL.blend`、`S-QEM-DISTAL_RIGHT-first-ring-clearance-U-TRIAL.blend`。比較 `tail-otherleaf-clearance-u-summary/REAL_QEM_PROXIMAL_DISTAL_U_SIDE.jpg`。
Actions [38114173295](https://github.com/badjoke-lab/evowild-test/actions/runs/38114173295) SUCCESS（ワークフローの成功は**形状合格ではない**）。

## 次の必須工程（単純な押し出し量の変更を繰り返さない）

1. 残りの接続リングの曲がり・交差構造を**局所的に再トポロジー化**。対象は原Qの皮膚パッチ境界と最初の2支持リング。単一の穴から自然につながる、隣接面の巻き込みがないサーフェスを作る。ソースメッシュは上書きしない。
2. 根元側、先端側を**個別にBVH交差ゼロ**・一体マニフォールド・退化0・面反転0で確認。**いずれか不合格のまま3枚を結合しない。**
3. 3枚を初めて統合した後は、各装甲の単独テストを流用せず、**装甲同士も含む全尾自己交差を再検証**。
4. 技術的接続ができても、**基準の頭冠、胸・肩、腰、四肢、蹄、長く重なる装甲尾を5方向で直接比較して造形REJECTなら完成扱い禁止**。まだ全身デザインは不一致。
5. 新規メッシュに対するスキンウェイト・13ボーン・複数周期走行・接地検証が必要。旧QEMのアニメーションPASSは新メッシュへ継承されない。

**全S型完成数：0。main、本線ゲーム資産、別レーン未変更。**
