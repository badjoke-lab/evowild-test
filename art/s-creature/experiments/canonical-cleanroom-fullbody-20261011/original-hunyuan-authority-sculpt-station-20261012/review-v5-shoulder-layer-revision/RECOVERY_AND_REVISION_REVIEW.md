# クラッシュ復旧とRevision Aの判定 — 2026-10-16

**復旧成功。再開後のRevision A試案はREVISEで棄却。採用モデルの更新・commit/pushは未実施です。**

## 復旧した地点

作業ブランチは `exp/s-hunyuan-shoulder-sculpt-20261013`。GitHubの最新 `375dab9` とローカルHEADは一致しています。追跡済みファイルに変更はありません。既存の未追跡PILOT画面・過去の失敗記録は削除していません。

直前に成功した操作は、保存済みPILOTの読込、SHA確認、オブジェクト一覧の取得です。クラッシュした操作は `s_hunyuan_shoulder_revision_a_setup.py` の当時の19行目、現在読込中のPILOTから同じメッシュを `bpy.data.libraries.load` で取得する検査でした。Blender自身のcrash.txtに同じPython行と `bpy_lib_exit` のスタックがあります。この検査を、保存時fingerprintとの直接照合へ置き換えました。

Blender一時領域・設定・作業フォルダを調査しました。該当する `.blend1` はありません。00:13:10の `960_autosave.blend` は別名で保全して実際に開き、標準Cube・Light・Cameraだけで造形データがないことを確認しました。最新の正常な造形は保護済みPILOTです。

`S_HUNYUAN_SHOULDER_LAYER_REVISION_A_RECOVERED_BASE.blend` はPILOTを上書きせずに作ったバイト完全一致の復旧コピーです。再読込後も、座標と面ループのfingerprintが保存時PILOTと一致しました。

- ファイルSHA256: `4342cede67662bb28066bcd5e00c7ac1a2527e25d0b4c7a01fb96ca1567d4627`
- メッシュfingerprint: `bd1a73404f0885af9f5fd831f87e88792726fe5894e09cd000e46408e997d4e4`
- 40,957頂点、三角化後81,994面、非多様体0、既存極小面2、既存BVH接触候補7。
- 新しいRevision Aのメッシュ複製・造形前にクラッシュしたため、確認できる造形作業の損失は0です。失われたのは一時的な表示・セッション状態です。

## 中断地点から再開した作業

PILOT生成スクリプトは再実行していません。復旧したメッシュの作業コピーに対し、右肩のみ、斜めの支持線5本と2つの面方向の切替え、下端の戻りと小さい胸側の凹みの充填を実施しました。実画面で硬い二本の帯になることを確認し、既存支持線の高さを下げて曲線的な変形を加えました。切断処理の再実行や両側への展開はしていません。各編集には二重実行を防ぐガードがあります。

試案は41,075頂点、三角化後82,230面。右肩ROI外と反対側の座標は完全一致、新規BVH交差候補0、非多様体0、巻き方向不整合0、極小面は既存の2面のまま、native mesh validationによる修正0です。保護対象10ファイルのSHAも一致しました。BVH検査はあらゆる接触の不存在の証明ではありません。

SIDE・FRONT・FRONT34の実画面確認に加え、ライブBlender 4.3.2で全身5方向と肩詳細3方向のCyclesレンダーを完了しました。`RENDER_PROGRESS.json` と各 `*_RENDER.json` に記録しています。

## 視覚判定: REVISE

`CANONICAL_PILOT_REVISION_A_DETAIL.jpg` は基準画のピクセル切出し、保護PILOTの既存実レンダー、新試案の実レンダーの比較です。`PILOT_REVISION_A_FIVE_VIEW.jpg` は全身5方向比較です。ポーズ差を補正したピクセル類似度は主張しません。

SIDEとFRONT34では、面の中に帯状の折れが増えましたが、基準画の複合的な肩の重なりには達していません。下縁の黒いV字と硬い直線的な戻りが残り、上腕へ連続する形も不自然です。FRONTでも下端に角張った段差が残ります。PILOTより良い肩になったとは判断できません。

試案は保存せず破棄し、復旧コピーを再読込してPILOTとの完全一致を再確認しました。現在のBlenderはこの正常な復旧コピーを開いています。`S_HUNYUAN_SHOULDER_LAYER_REVISION_A.blend` は作っていません。「改善した場合だけ保存・commit/push」の条件を満たさないため、試案・復旧記録ともローカルに保持し、今回のcommit/pushは行っていません。

元Hunyuan、v1〜v4、V5_STAGE1、PILOT、基準PNG、mainは変更していません。`git clean`、`git reset --hard`、強制pushは実行していません。
