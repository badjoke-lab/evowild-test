# S Hunyuan shoulder / chest sculpt V1

Blender 4.3.2で元Hunyuanの既存メッシュ `geometry_0` を実編集した比較用候補。元モデルの置換なし。

## 実変更

- 肩：上方から上腕へ斜めに流れる局所的な厚みを追加。
- 胸：前面を前方へ、胸下面を下方へ動かし、胸郭の深さを追加。
- 上腕：肩とは別の局所的な量感を追加し、前肢への接続を強調。
- 脇・腹側移行：肩後方の面を少し内側へ戻し、胸から腰へ上がる下面の変化を強調。
- 正面で肩が過剰に張り出した初期値は減量。公開ファイルは減量後の候補。

## 実行検証

- Blender: 4.3.2 (Codex Cloud上の実バイナリ)
- 元commit: `f8c10657e75bde0105bffff932bb1976f3ff71c5`
- 38,802頂点 / 77,684面を保持。
- 変更頂点: 8,674
- 最大移動: 0.028257284313 Blender単位
- 変更頂点の平均移動: 0.012443486601 Blender単位
- 保存後の再読込座標: 全頂点で期待値と完全一致。
- 編集領域外の頂点および面の接続: 不変。
- 元.blend SHA256: `1f26bbd4485721a69d74c0c4c4da917dacf9341c15932785e42ba478c3f71c37`
- 基準PNG SHA256: `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`
- 修正版 SHA256: `13d911bbefed39ec602df35b812ce04d27815ac3a7afe3ec0205d77aa65fd212`
- 元.blend、基準画像、mainは変更していない。

## 成果物

- `S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1.blend`：実編集済み、約2.7MB。
- `AFTER_SIDE/FRONT/FRONT34/REAR34/BACK.png`：5方向実レンダリング。
- `AFTER_DETAIL_SIDE/FRONT/FRONT34.png`：肩・胸・上腕の拡大レンダリング。
- `BEFORE_*.png`：同一カメラ・照明・クレイ材質による修正前比較。
- `FIVE_VIEW_BEFORE_AFTER.jpg`、`SHOULDER_CHEST_BEFORE_AFTER.jpg`：実レンダーの比較配置。
- `SCULPT_VERIFICATION.json`、`vertex_delta.npz`：検証数値と変更全頂点の前後座標。
- `execution.log`：実行ログ。

## 再実行

リポジトリrootからBlender 4.3.2で実行する。

```sh
blender -b -t 4 --python-exit-code 1 --python art/s-creature/blender/s_hunyuan_sculpt_before_v1.py
blender -b -t 4 --python-exit-code 1 --python art/s-creature/blender/s_hunyuan_shoulder_chest_sculpt_v1.py
python3 art/s-creature/blender/s_hunyuan_sculpt_contact_sheets.py
```

比較シートにはPillowが必要。Blenderスクリプトは毎回保護された元モデルから開始し、同名V1候補のみを再作成する。元モデルは上書きしない。
GitHub Actions: `.github/workflows/s-hunyuan-shoulder-chest-sculpt-v1.yml`。
ワークフローは修正前後の実レンダー・修正版blend・検証をartifactに保存し、自動commitはしない。

クレイ材質、カメラ、照明はレンダー時だけ設定する。保存blendの元材質と画像ガイドは保持。比較は正投影の共通フレームであり、基準画像への画素単位の位置合わせではない。REAR34は基準画に存在しないため、立体の連続性だけを確認する。

## 判定: REVISE

肩の外側の量感、胸前面の深さ、胸から腹側へ上がる輪郭は修正前より読み取りやすい。上腕の局所的なふくらみと脇の凹みも実際の頂点変更で追加した。

ただし、正規画像の肩・胸にある斜めの面の重なりと、胸筋から上腕への明確な面の切り替えには届いていない。現在の肩はまだ丸い量感が中心で、正面の幅も引き続き要調整。上腕の独立性は増したが、肘へ向かう方向性と胸からの分離は不十分。従って完成形としてKEEPしない。V1は実編集済みの比較候補として保存する。

元メッシュ由来の三角面の粗さ、頭冠・尾の薄片や欠損、前後肢・足部の正規画像との差も残る。このパスでは領域外の形を変更していない。正規画像への一致、ゲーム投入、リギング承認はしていない。

面品質確認：有効な三角面の法線反転0。退化面は修正前後とも2で、新規退化なし。これは全自己交差の検査ではない。
