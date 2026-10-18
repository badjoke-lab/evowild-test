# S ZERO R2 実造形・品質評価 — 2026-10-18

**全身判定: REVISE。局所改善は継続用R2として採用。production KEEP / 本番昇格ではない。**

[S_ZERO_CANDIDATE_REVISED_R2.blend](S_ZERO_CANDIDATE_REVISED_R2.blend)は、保存済みR1のバイト一致コピーから作業した。
Blender MCPの `execute_blender_code` でライブBlender 4.3.2の既存メッシュを編集。
生成器、元の全身生成スクリプト、外部形状ドナーは使用していない。

## 原画と保存点

- 最上位: [00_s_type_modeling_image_v1.png](../references/00_s_type_modeling_image_v1.png)。
- 共通原画、creature reference index、S modeling handoff / correction lockを確認。
- R1の[評価全文](QUALITY_REVIEW.md)と5方向実画像を確認してから造形。
- 原本3件とR1は保存前後のSHA256一致。R2の再読込時点で既存69ファイルを照合（更新対象の品質評価文書を除く）。
- R1 SHA256: `f8e8a80360ee5886d485a17610cf62a9387d10cdb09e4801a055be99bf8d8a4f`。
- R2 SHA256: `3406e12f54670ca397eb31825721aa08e36fbc46a0bc68e2dcfbcbaae0c09662`、1,259,118 bytes。

## R1から実際に変更した形状

| 箇所 | R1 | R2 |
| --- | --- | --- |
| 肩・肩甲部・上腕と胸 | DELTOID / SCAPULA / BRACHIALの左右6メッシュが暗い本体に重なり、肩下と腕上端が別部品として読める | 既存頂点で外側の膨らみを抑制し、上腕を本体側へ寄せた。その6メッシュを本体へEXACT Boolean UNIONし、交線から65 mm以内の局所平滑化を実施。胸から肩・腕まで1つの接続した表面になった |
| 肩の色境界 | 独立白色部品の縁と交差が段差に見える | 接合後の2044面だけに既存色の頂点/コーナー補間を使用。別部品の交差を画像処理で隠したものではない。境界は原画より柔らかく、今後の整理対象 |
| 二本の冠 | 正面では細い平行線に近い | MAIN / BLUE / IVORY_RIDGEの左右6メッシュのY座標のみを調整。中腹をレンズ状に広げ、根元と先端を絞る。側面の全X/Z座標・頂点数・面接続を保持 |

冠MAINのZ=2.64断面の左右幅は各0.04937 → 0.07606（モデル単位）。
Z=2.40では0.04163 → 0.04738、Z=2.84では0.04365 → 0.05307。
中腹を主に広げたため、均一な太線への置換ではない。

変更対象は本体の肩領域、肩由来6メッシュ、冠6メッシュだけ。
残る137メッシュの頂点・面・材質番号・平滑化フラグ・配置ハッシュはR1と一致。
頭・眼・Cue Band・腰・足先・尾は形状不変。肩領域外の本体21,497頂点は座標完全一致。
カメラ、照明、背景、色管理もR1と一致。

## 試作の取り消し・再評価

1. 試作Aは接合により肩の連続性を改善したが、白黒境界がギザつき、正面冠を広げすぎたため**REVISE**。
2. 試作Bでは冠をR1の元座標から小さい変位で調整し直し、過剰な広がりを撤回。
   接合面の白黒境界のみ局所補間した。試作Aの本体の接続形状は保持。
3. SIDE / FRONT / FRONT34の実画像とR1拡大比較で改善を確認してから、R2へ別名保存。

[判断記録](evidence/SCULPT_R2_REVIEW.json) / [試作A拡大](comparisons/R2_TRIAL_A_DETAILS.png) /
[試作B拡大](comparisons/R2_TRIAL_B_DETAILS.png)。
試作Aを最終成果としてKEEP扱いしていない。

## 方向別の実画像評価

| 方向 | 改善・維持 | 残課題 |
| --- | --- | --- |
| [SIDE](renders/revised_r2/SIDE.png) | 肩から腕へ突き出した部品上端と重なりの段差が減少。小頭、細い腰、長脚、後方へ流れる冠を保持 | 肩がまだ丸く滑らかで、原画の複数の面による構成に不足 |
| [FRONT](renders/revised_r2/FRONT.png) | 二冠の中腹に面幅が現れ、根元・先端への絞りが読める。肩外側の膨らみと腕への分離感を軽減 | 原画の角張った断面・額への根元構成はさらに整理が必要。白黒境界が柔らかい |
| [FRONT34](renders/revised_r2/FRONT34.png) | 肩甲部から肩・上腕への連続した量感。別の上腕キャップの段差を軽減。二冠とCue Bandを維持 | 胸との局所の凹凸、肩の面構成、色境界の設計は未完成 |
| [REAR34](renders/revised_r2/REAR34.png) | 肩後方から上腕への表面の連続性を確認。細い腰・後脚・尾のシルエットを保持 | 腰の別部品感、尾の反復板構造は今回の変更対象外 |
| [BACK](renders/revised_r2/BACK.png) | 左右の冠の中腹幅と絞りを背面でも確認。脚・骨盤の配置は保持 | 腰と本体の段差、尾の中央軸と層のつながりは残る |

[原画・R1・R2比較](comparisons/REVISED_R2_REFERENCE_R1_COMPARISON.png) /
[肩・冠の拡大比較](comparisons/REVISED_R2_DETAILS.png) /
[R2 5方向](comparisons/REVISED_R2_FIVE_VIEWS.png) /
[R1/R2 5方向比較](comparisons/REVISED_R2_R1_FIVE_VIEW_COMPARISON.png)。

画像はCycles CPU / 32 samples / seed 17 / 1200×900。
同じカメラ行列・orthographic scale・照明・色管理を使用。
比較画像の加工は原画切抜き・等比縮小・配置・文字だけ。生成画像、形状レタッチ、補間画像は使っていない。
原画イラストとモデルの姿勢・投影は完全一致ではない。

## 保存・再読込・構造検査

[R2再読込検査](evidence/VERIFY_R2_RELOAD.json)は実際にR1とR2を開いて比較した結果。

- R2: 144 meshes、39,691 vertices、40,014 faces。
- 本体は27,567頂点の1連結成分。統合前の6肩部品は本体へ吸収され、隠した別オブジェクトはない。
- 全144メッシュのboundary / nonmanifold / loose vertex / 面積1e-12未満の面は0。
- 本体の非隣接面BVH自己交差候補は0。完全な交差証明ではない。
- 全身remeshは行っていない。肩周辺のBoolean接合にはngonや不規則なエッジがあり、**変形用トポロジーではない**。
- 未変更の腰・肋骨・背中などと本体の交差は残る。全身一体化済みとは評価しない。
- Armature / Actionなし。歩様・race-size motion・PC/mobile runtime未検証。本番モデルは変更していない。

## GitHub保全

開始時local `1c33ebb594e61ee24d9a28af09594ae24c88d19c` とremote `2a273da4e3cc7a9c6318941d64db0c58ba4608cb` は履歴が分岐していたが、内容差は未反映画像16点のみ。
GitHub Contents APIで1ファイルずつ追加し、直後にraw bytesを再取得して全バイトを照合した。
[16画像の保全記録](evidence/REMOTE_missing_images.json)。
通常mergeで両履歴を保持し、以後も同じ保全branchだけに送信。
大きな一括push、reset --hard、clean、force pushは行っていない。
R2と試作証拠も[個別送信・再取得記録](evidence/REMOTE_r2_assets.json)に残す。

## 次の造形課題

1. 肩・胸・上腕の連続面に原画の明確な面の向きと白黒境界を与える。現在の柔らかな境界は最終仕様ではない。
2. 腰・骨盤と本体の交差整理。無関係な部位を同時にまとめて変えない。
3. 足先を楔形とし、方向性・接地面・足首を定義。
4. 尾の薄板反復を有機的な厚みと層の重なりへ整理。
5. 肩・股関節のリトポロジー、基準姿勢、リグ、歩様、PC/mobile runtimeの順で検証。

## 再現

R1を`verification/S_ZERO_R2_WORKING_COPY.blend`へバイトコピーして開き、ライブBlender MCPで
`scripts/11_sculpt_r2.py` → `13_refine_r2_interface.py` を実行する。
3方向を実レンダリングして評価記録を作り、`15_save_reviewed_r2.py` → `14_verify_r2.py`。
各スクリプトは既存の出力モデルの上書きを拒否する。再実行は別の検証用checkoutで行う。
