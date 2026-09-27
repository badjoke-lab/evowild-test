# EvoWild Run — S-type checkpoint

current_stage: S-blockout-v2 — self-reviewed, NOT accepted/final
branch: feat/s-creature-model
current_model_file: output/S-blockout-v2.blend
latest_export: output/S-blockout-v2.glb

done:
- S型1体を添付referenceから新規制作。既存ゲーム用proceduralモデルは未使用。
- S-blockout-v1を.blend/.glbで保存し、指定4方向を確認。
- v2で頭蓋・顎を再構成、冠と首を細く低く修正、肩の稜線と脚の前後差を追加。
- v2も4方向を確認。頭蓋正面は中央で連続。
- 編集用断面メッシュを非表示S_EDITABLE_SOURCEに保持。REVIEWは表示確認用。
- 最新表面は単一の連結メッシュ、non-manifold edge 0。微小な孤立断片24頂点を除去。
- texture / final rig / animationなし。P/E/A未着手。

next_action: Open output/S-blockout-v2.blend, unhide S_EDITABLE_SOURCE, narrow the lower Neck_integrated_keel cross sections by 15% and reshape their chest junction against reference 01; preserve the continuous central skull.

quality_issues:
- 冠は中央一枚の刃として強く見え、主資料の細い後方への流れと稜線構成にまだ差がある。
- 首下部から胸郭が厚く、主資料の軽い首肩の移行にまだ届かない。
- 肩・骨盤の大きな面構成は未完成で、胸郭側面に断面由来の段差が残る。
- 後肢の膝・足首と長い下肢の太さの変化が弱く、関節周囲を再造形する必要がある。
- 足先は三趾のblockout段階。接地、指の分離、前方重心は走行・変形検証をしていない。

blockers:
- 造形を続ける技術的blockerなし。
- 形状は未承認。retopologyと走行変形への適性は未検証。

review_renders:
- output/review/v2/S_blockout_front.png
- output/review/v2/S_blockout_side.png
- output/review/v2/S_blockout_front34.png
- output/review/v2/S_blockout_rear34.png

resume:
- 最新.blendを直接開く。生成scriptの再実行は不要。
- S_organism_blockout_v2が現在の連続表面。S_EDITABLE_SOURCEはその元断面で、同時表示すると重複する。
- 座標: -Yが前、+Zが上。四肢は確認用の静止姿勢。
- 技術チェックはoutput/validation.json。これは造形品質の合格を示すものではない。
