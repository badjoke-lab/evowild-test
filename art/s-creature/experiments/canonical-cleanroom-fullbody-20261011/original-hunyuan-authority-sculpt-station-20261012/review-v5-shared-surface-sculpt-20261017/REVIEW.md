# 共有曲面の初回実造形 — REVISE、取り消し済み

Blender MCPでV5_STAGE1の別名コピーから実メッシュを一度作成した。中断後は接続、ファイルパス、対象オブジェクト、頂点・面数を確認し、生成処理を二重実行していない。

対象: `S_RIGHT_SHARED_CHEST_SHOULDER_ARM`。新規120頂点・100四角面。胸郭から肩への制御面と、その面の8頂点の開口境界を共有して伸ばす曲がった上腕を作成した。独立3ロフトではない。表示用Subdivisionは1段、元の38,802頂点・77,684面の座標・面構成は変更0。既存メッシュとの最終接続は未実施。

開始コピー: `S_SHARED_SURFACE_START_COPY.blend`。ディスク上はV5_STAGE1と同一の未編集コピー。開始時の無関係な未保存Grease Pencilシーンは `SESSION_BEFORE_SCULPT.blend` に退避済み。

| 方向 | 変更前 | 初回実造形 |
| --- | --- | --- |
| SIDE | [変更前](00_BASELINE_SIDE.png) | [実造形](01_SHARED_CORE_SIDE.png) |
| FRONT | [変更前](00_BASELINE_FRONT.png) | [実造形](01_SHARED_CORE_FRONT.png) |
| FRONT34 | [変更前](00_BASELINE_FRONT34.png) | [実造形](01_SHARED_CORE_FRONT34.png) |

3方向とも同じ正投影・target=(0,-0.345,-0.055)・distance=0.66・Studio Solid・cavityなしの実画面。基準PNGと形状対応図は造形前に直接確認した。

判定はREVISE。SIDEでは胸下に長い膜状の面が垂れ、原画の胸郭輪郭から大きく外れた。FRONTでは胸から腕への長い柱状の連続面になり、胸・肩・腕それぞれの適切な量感が読めない。FRONT34では湾曲した腕が管状に見え、胸側の膜との間に深いV字の谷が生じている。原画より悪化しており、肩上部の斜めの重なりの追加へは進めない。

原因は初期制御面の境界配置にある。胸郭へ合わせるray_castを局所領域・距離で制限せず、全身メッシュの遠い部位に当たる位置も採用した。境界がz=-0.66929〜+0.40647まで拡大し、本来の胸・肩領域から外れた。低い頂点の実座標を `REJECTED_SHARED_SURFACE_CHECK.json` に残した。共有する胸郭面自体を壊した実装上の失敗であり、膜状の外観を単なる未接続境界として扱わない。上腕の曲がった軸と変化する断面は作成できたが、この胸郭との組合せは不合格。

棄却メッシュの全座標・面を `REJECTED_SHARED_SURFACE_GEOMETRY.json` に保存後、新規制御メッシュと表示用Mask/頂点グループを削除した。元メッシュfingerprint `f8370cea4a46f69251b658505454dacb91712c647828acc07494dcd99c6675ff` の一致を確認。`ROLLBACK_VERIFIED.json` と `02_ROLLED_BACK_SIDE.png` を保存した。

編集済みモデルはない。初回の実造形と3方向確認で終了。追加造形、反対側制作、長時間レンダリング、編集済みblend保存、commit/pushは実施していない。生成スクリプト・棄却形状JSON・実画像・判定はローカルに残す。既存モデル・基準PNG・過去の失敗記録・Git参照の終了時照合は `PROTECTION_FINAL.json`。
