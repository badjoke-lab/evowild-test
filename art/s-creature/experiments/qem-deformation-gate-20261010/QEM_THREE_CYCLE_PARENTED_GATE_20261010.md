# S型QEM — 実メッシュを前進させる3周期IK検証（2026-10-10）

## 結論

**PASS_LIMITED_THREE_CYCLE_IK / S型完成承認ではない。**
Blender 4.3.2の実アーマチュア（13変形ボーン）とTRELLIS2 QEM実メッシュを使い、描画メッシュ自体のワールド座標前進を証明したうえで、対角脚の接地固定・遊脚と短い3周期の継ぎ目を検証した。

- Authority: `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Original donor: `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`, SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`.
- Source: 29,948 vertices, 59,932 triangles, 13 deform bones. Source mesh and original GLB **unchanged**. R0/R1 proxy not substituted.
- branch `exp/s-qem-threecycle-parented-20261010`, Actions run [38029838137](https://github.com/badjoke-lab/evowild-test/actions/runs/38029838137).

## 重要な修正：アーマチュアを動かすだけでは不十分だった

先行 `rootmotion-contact-v2c` の限定PASSは、描画用weighted meshがarmature objectの子ではない状態だった。アーマチュアオブジェクトの位置パラメータが変わることだけで、全身メッシュが正しく移動したと証明してはいけない。

`threecycle-ik-gait-v1` で従来のまま3周期を試すと、全候補で面積条件違反と周期シーム不一致を観測した。接地パッチのみの合格から全身前進・継ぎ目成功と主張できない。

そのため、このV2実験では**元QEMを保持しつつweighted copyを実アーマチュアの子にする**親子関係を明示した。親子関係変更による静止姿勢の頂点位置誤差 = **0**。IKを一時的に無効にした状態でarmature rootを0.024動かし、描画用メッシュ全頂点の剛体平行移動との差 = **最大7.06e-8**。これにより、ボーンの位置パラメータだけでなく**表示される身体メッシュ自体が前進する**ことを確認した。これは独立した実モデル検査である。

## 実際の3周期PASS

| 検査 | 結果 |
| --- | --- |
| 16フレーム/周期 × 3周期 + 最終キー | 49 integer frames |
| 全中間フレーム | 48 half-frames |
| 元頂点/面/13ボーン/GLB SHA | 維持・PASS |
| 接地中の各foot patch XY誤差 | 最大 4.86e-7 (上限 0.01) |
| 地面min-Z接地 | 全integer/half-frame PASS (許容 -0.002〜+0.006) |
| 面反転・潰れ・面積半減以下/倍増以上 | 全97サンプルで0 |
| 最大triangle area ratio | 1.6743 (上限 2.0) |
| 検査したcycle境界F17/F33/F49の相対形状ズレ | 最大 7.86e-7 (許容 0.0015) |
| 胴体の前進距離 | 1周期0.024、3周期合計0.072 モデル単位 |
| 高さ2.55に対する3周期の距離 | 約2.82% |
| 速度・加速度・着地衝撃・実レース性能 | **未検証** |
| 完成S型承認 | **未承認、0体** |

数値は `threecycle-ik-gait-v2-parented/REAL_THREE_CYCLE_IK_QA.json` から取得した。**GitHub Actions自体のSUCCESSと、メッシュの限定PASSは別。** すべてのgate criteriaがtrueであることを確認した。

### 確認リンク

- [V2 JSON 97時点実測](https://github.com/badjoke-lab/evowild-test/blob/exp/s-qem-threecycle-parented-20261010/art/s-creature/experiments/qem-deformation-gate-20261010/threecycle-ik-gait-v2-parented/REAL_THREE_CYCLE_IK_QA.json)
- [V2 real .blend](https://github.com/badjoke-lab/evowild-test/blob/exp/s-qem-threecycle-parented-20261010/art/s-creature/experiments/qem-deformation-gate-20261010/threecycle-ik-gait-v2-parented/S-QEM-13bone-threecycle-parented-v2.blend)
- [実Blender 17 frame GIF](https://github.com/badjoke-lab/evowild-test/blob/exp/s-qem-threecycle-parented-20261010/art/s-creature/experiments/qem-deformation-gate-20261010/threecycle-ik-gait-v2-parented/review/S_QEM_13BONE_REAL_IK_ONE_OF_THREE_CYCLES.gif)
- 追加F25/F33/F41/F49の実レンダリングも同reviewディレクトリに保存。
- 失敗例は `threecycle-ik-gait-v1/REAL_THREE_CYCLE_IK_QA.json` に保持。

## まだ達成していないこと・次のGate

1. **全身走行リグの本格化**：現在は対角二脚を交互に動かす短い運動学試験であり、ギャロップ、推進力、重心上下動、着地衝撃、速度変化を再現したわけではない。
2. **関節の解剖学的承認と長い歩幅**：12 joint landmarksはメッシュから抽出した候補。肩・肘・手首・股関節・膝・飛節は最終承認されていない。0.024/周期の短い移動だけで妥当性を主張しない。次はウェイト/リグの差分を独立実験し、歩幅の拡大を同条件で比較する。
3. **最上位S形状への五方向レビュー**：SIDE / FRONT / FRONT34 / REAR34 / BACKの実モデル画像をauthoritative S referenceと直接比較。現時点で造形の一致・冠・首・肩・後肢等の承認は行っていない。
4. **ゲーム実装**：18体描画・FPS・接地をゲーム内で実測するまでmain / Motion First等へのmergeは禁止。

**原則**：外観QEMを低品質R1/R0へ差し替えない。未実証をPASSに数えない。完成S型=0。
