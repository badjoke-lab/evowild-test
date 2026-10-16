# 構造再設計・初期制御メッシュ — REVISE / STOP

2026-10-16。branch: `exp/s-anatomy-structural-redesign-20261016`。

Revision A・BはREVISEとして固定。開始時の未追跡ファイルとbranch情報をSTART_GIT_STATUS.txt、Git参照をSTART_REFS.txtに記録。既存モデル・基準画像・A/B記録など101ファイルをSHA256で保護し、A/Bの証拠とスクリプトをREVISION_A_B_FAILURE_EVIDENCE.zipへ退避した。既存証拠の書換えはしていない。

V5_STAGE1からS_ANATOMY_REDESIGN_CONTROL_WORKING.blendへバイトコピーして開始。読込オブジェクト名にはV4が残っているが、入力ファイルはV5_STAGE1でありPILOTではない。ディスクの新blendは未編集の開始コピーのまま。

右肩・胸上部・上腕付け根を一つの設計領域とし、合計170頂点・144面の3つの低密度制御体を一度だけ作成。既存メッシュは削除・張替えをせず、非破壊の表示用Maskを使用。制御体は未接続。接続トポロジーは作っていない。再現スクリプトはart/s-creature/blender/s_anatomy_redesign_control.py、棄却形状はREJECTED_CONTROL_GEOMETRY.json。

## 原画と3方向の実画面による判定

最上位基準: art/s-creature/references/00_s_type_modeling_image_v1.png。
実画面: 01_CONTROL_SIDE.png、01_CONTROL_FRONT.png、01_CONTROL_FRONT34.png。正投影、target=(0,-0.345,-0.055)、distance=0.63、Studio Solid、cavityなし。原画のポーズ・透視差はあり、画像一致の数値は主張しない。

- SIDE: 肩上部には斜めの長軸があるが、原画の幅広く短い重なりに対して、長い葉状の単一体になった。上腕は先細りの棒状で、肩下から出る厚みと屈曲の関係が不十分。
- FRONT: 胸の制御体が縦長の独立部品として見える。原画の胸郭へ回り込む曲面にならず、肩と胸の間に長い溝が生じる。肩幅・胸幅の関係も未成立。
- FRONT34: 胸と肩が並列の二つの塊に見える。原画の斜めの被さりと面方向の切替えを再現できていない。肩下端と上腕の継ぎ目も突合せに見える。

初期設計の失敗原因は、水平断面ロフトを別々の閉じた量塊として構成したことで、胸郭の横方向の曲率と肩の被さりを共通の面の流れとして設計できなかった点。表示Maskの境界にも開口が見えるため、完成接続の外観評価はできない。ただし棄却理由は開口だけでなく、制御体自体の比率・面方向・重なりの不成立である。

視覚ゲートはREVISE。技術的PASSを採用理由にしていない。同形状への微修正を繰り返さず停止。接続・細部・反対側への展開、5方向レンダー、編集済みblendの保存・再読込、最終メッシュ検証、commit/pushは実施していない。ライブBlenderには未保存の棄却プレビューが残る。

終了時の保護照合はPROTECTION_VERIFIED.jsonを参照。既存101ファイルとmainを変更していない。
