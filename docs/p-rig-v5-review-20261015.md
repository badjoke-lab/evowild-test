# P layered v5 — REVISE / experimental only

総合判定は **REVISE**。正規P型に近い角張った頭・冠、高い肩、短い胸腰配置へ変更し、胸郭と骨盤の相対運動を実装した。支持アンカーと固定骨長は保持できたが、前脚回収時の密集、上腕の丸い輪郭、部品境界が残る。足底ラスタの水平移動も一部悪化しており、接地品質を全面的に改善したとは判定しない。標準採用、mainへのmerge、製品標準素材への切替は行わない。

## 開始状態と範囲

- fetch済み開始remote: `fix/2p5d-p-canonical-20261011` = `6c0c79868b14023bba58db6d2fcd5a15cc678f1f`。指定commitとの差分なし。
- 作業branch: `exp/2p5d-p-v5-silhouette-spine-20261015`。
- 造形基準: `public/concept/P.webp`。v3/v4レビュー、比較画像、12フェーズ、実動画を開いて確認した。
- v4コードは [snapshot](evidence/p-rig-v5-20261015/v4-snapshot/p_layered.js)、素材・既存証拠のSHA256は [baseline](evidence/p-rig-v5-20261015/v4-baseline.json) に保存。既存素材の検証は [protected-assets-validation.json](evidence/p-rig-v5-20261015/protected-assets-validation.json)。
- `pRig=1` のみ。正規画像、v2/v3/v4素材、S/E/A、3Dコード、main、開始branchは変更しない。

## 実制作

`public/concept/p-layered-v5/` に新しい胸郭・肩・首・頭・冠の一体部品、腰部、骨盤・尾、上腕、前腕を制作した。透明な原画とcrop定義を保存。平坦な断面パッチを使わず、丸い筋肉の連続面を持つ部品を重ねる。後脚部品はv4、足の描画リソースと物理校正はv3の承認済みデータを再利用する。全身の縦拡大、フレーム画像補間、メッシュワープは使用しない。

`src/p_layered.js` は胸郭・腰部・骨盤を独立した剛体画像として描画する。肩と骨盤のYは周期の中で逆位相に最大±3px、Xは±2px、回転は胸±0.045rad、骨盤±0.055rad。従来の荷重上下動・飛行区間にこの相対運動を追加した。腰部は両者を結ぶ方向を向き、固定倍率の重なりで接続する。これにより全身上下動だけの構造から変更したが、背骨全体の生物的なしなりとしては控えめで、まだ硬さが残る。

| 中立構造 / rig px | v4 | v5 |
| --- | ---: | ---: |
| 肩座標 | (262.828,155.843) | (250,146) |
| 腰座標 | (167.831,162.608) | (179,164) |
| 地面からの肩高 | 140.157 | 150 |
| 地面からの腰高 | 133.392 | 132 |
| 肩–腰間距離 | 95.238 | 73.246 |
| 前脚 / 後脚の各骨長 | 70 + 68 | 70 + 68 |
| 静止外接寸法 | 316 × 236 | 305 × 234 |
| 高さ／幅 | 0.746835 | 0.767213 |

正規は205×163、比率0.795122。比率差は縮んだが一致していない。幅を揃えた比較画像は縦横比を保持している。構造値は中立・補正前、実支持姿勢の値は [structure-comparison.json](evidence/p-rig-v5-20261015/structure-comparison.json) と [phase CSV](evidence/p-rig-v5-20261015/spine-phase-measurements.csv) を参照。画像の見た目と骨格の数値を混同しない。

## 接地と着地準備

4脚ID、支持率0.30、位相差、独立contactId、支持中のworldX/worldLane固定、70/68の骨長を維持した。旧配置は足底を肩の前後に中心配置していたため、足首が足底より約24px後方にある分、足首の可動域が後ろに偏っていた。v5は**着地する前**に足首の可動域を中心化する。支持中のアンカーを修正する処理ではない。

新しい肩高では、回収の最終区間から支持へ直接切り替えると6→7に約8.14pxの跳びが出た。回収末尾20%で着地荷重へ滑らかに移行し、胴の到達補正を準備するよう修正した。荷重後の自由足のみ、固定骨長の到達円へ持ち上げる。支持足にはこの調整を適用しない。修正後の同境界は0.096568px（±0.0001周期の比較）。0と1の端点は関節差0、異なる画像チャンネル0。

## 胴高上限12の調査

既存 `MAX_COMPRESSION=10` は「前の時点ですでに支持していた脚」が許すレーン移動範囲の計算に使われる。新しく着地した脚はその範囲計算を通らず、後段の実到達補正が10を超え得る。12は骨長から導かれる物理上限ではなく、テストの許容沈み込み上限であり、値のクリップでもない。

v4 Androidの12.326241を再現した。v5は肩・腰配置、足首中心の着地点、着地準備を変更して対応した。閾値12、骨長、サンプリング数を緩めていない。テストは30ms間引きを廃し、PC/Androidとも全rAF（16ms）で採取する。補正値は実際の描画・IKに使用した値で、表示上の切り詰めはない。

| 全rAFの計測 | v4 PC | v5 PC | v4 Android | v5 Android |
| --- | ---: | ---: | ---: | ---: |
| 最大胴高補正 rig px | 10.649232 | 11.918968 | 12.326241 | 11.202784 |
| 最大実沈み込み bob+補正 | 16.844744 | 17.992948 | 17.837328 | 17.777296 |
| 最大要求レーンとの差 | 0.000035942 | 0.006079720 | 0.000021458 | 0.002554225 |
| 全20脚支持アンカー移動 | 0 | 0 | 0 | 0 |

PCの補正・沈み込みとレーン差は増えている。Androidだけの改善を全条件の改善とは扱わない。v5の到達誤差は0、骨長誤差は最大8.53e-14px。動画計測はPC375フレーム/6秒、Android250フレーム/4秒、時間解像度は共通16ms。上表のv4は保存済み独立レース、v5は今回の独立レース。詳細は [run-validation.json](evidence/p-rig-v5-20261015/run-validation.json)。

## 足底画素 — アンカー0とは異なる

全20脚のfoot painterをそれぞれ透明面へ描画し、下2行のalpha>128の水平重心を計測した。カメラ移動を除去し、垂直方向は投影接地Yとの差分を用いる。合成レース画像の輪郭追跡ではなく、遮蔽前の足底ラスタ検査である。

同一のライブ入力をv4/v5へ与えた16msの比較:

| 条件 | v4平均 / 最大 px | v5平均 / 最大 px |
| --- | ---: | ---: |
| 単体・水平足底 | 0.382561 / 4.313371 | 0.520239 / 7.114952 |
| PC全20脚・水平足底 | 0.302857 / 1.838475 | 0.308409 / 2.156971 |
| Android全20脚・水平足底 | 0.209801 / 0.943113 | 0.214269 / 1.022234 |

水平足底指標は悪化。垂直残差の最大は両版とも1px。足全体のalpha重心平均はPC 0.058567→0.056601、Android 0.076481→0.076092と僅かに減るが、足底指標の悪化を打ち消す判定には使わない。足画像・校正を変えていなくても、新しい接地点でサブピクセル位置が変わり、閾値輪郭の揺れは残る。世界支持アンカー0を画素0と呼ばない。

この比較はv5レース入力を両コントローラへ供給するため、v4の独立レース再現と同一ではない。特にレーン差は共有入力と各コントローラの制約の違いを含む。独立動画トレースと区別して保存した。[全フレーム](evidence/p-rig-v5-20261015/all-20-contact-frames.json)、[集計](evidence/p-rig-v5-20261015/all-20-contact-validation.json)、[脚別CSV](evidence/p-rig-v5-20261015/all-20-contact-summary.csv)。

## 実画像と動画

- [正規／v4／v5](evidence/p-rig-v5-20261015/canonical-old-new.png)、[拡大](evidence/p-rig-v5-20261015/fullbody-enlarged-comparison.png)
- [12フェーズ比較](evidence/p-rig-v5-20261015/12-phase-before-after.png)、[v5シート](evidence/p-rig-v5-20261015/layered-contact-sheet.png)
- [前脚重なり](evidence/p-rig-v5-20261015/forelimb-overlap-comparison.png)、[関節拡大](evidence/p-rig-v5-20261015/joint-comparison.png)
- [体幹位相と実描画](evidence/p-rig-v5-20261015/spine-phase-comparison.png)、[新部品](evidence/p-rig-v5-20261015/runtime-parts.png)
- [v4／v5走行比較MP4](evidence/p-rig-v5-20261015/before-after-motion.mp4)、[v5単体MP4](evidence/p-rig-v5-20261015/isolated-continuous.mp4)、[半速](evidence/p-rig-v5-20261015/layered-half-speed.mp4)
- [18体PC MP4](evidence/p-rig-v5-20261015/race-18-desktop.mp4)、[18体Android MP4](evidence/p-rig-v5-20261015/race-18-mobile.mp4)
- [動画から抽出した比較](evidence/p-rig-v5-20261015/video-comparison-filmstrip.png)、[実動画フレーム](evidence/p-rig-v5-20261015/actual-motion-filmstrip.png)

実ブラウザの60fpsスクリーンショットからMP4を作成。補間フレームなし。単体5.555周期、PC19.565周期、Android12.748周期。18体動画は全フレーム18体描画、P型5体。v4単体動画は今回同条件で再撮影した。動画をデコードした時系列画像と12フェーズを実際に開いて比較した。v5は角張った冠と前傾した肩が近づいた一方、回収時に上腕が円盤状に見え、胸下の近遠脚が一体化する瞬間が残る。体幹の相対運動は見えるが、重い四足獣の滑らかな荷重移動として完成していない。

## 検査とCI

本番build: PASS (`npm --ignore-scripts run build`; S素材生成のprebuildはローカルで起動しない)。ループ検査PASS。ローカルPC/Android **24 PASS / 0 FAIL**（3.1分）。[JSON](evidence/p-rig-v5-20261015/2p5d-test-results.json)、[log](evidence/p-rig-v5-20261015/local-tests.log)。

v4 Actions [38503464926](https://github.com/badjoke-lab/evowild-test/actions/runs/38503464926) のログを取得。`Run E2E suite` は成功、`Capture Motion First visuals` で `tests/motion-first.spec.js:1735` / assertion1779 のbalanced1600順位分布が失敗（37 PASS / 1 FAIL / 1 SKIP）。これは3D側の既存問題で、P型Android胴高検査と別。対象外ソースは修正していない。

v5 Actions: [38602638790](https://github.com/badjoke-lab/evowild-test/actions/runs/38602638790)、検査対象コードcommit `8baec5ae76580c52625f1c90747883356ca5918c`。今回の実験branchで既存workflowを実行するためpush対象にこのbranch名だけを追加した。既存の全体E2E・3D検査をskipする変更はしていない。実結果は **FAILURE**。全体E2Eは **43 PASS / 81 SKIP / 0 FAIL**。追加の `Capture Motion First visuals` は **36 PASS / 2 FAIL / 1 SKIP**。失敗は (1) v4と同じbalanced1600順位分布、(2) `tests/motion-first.spec.js:2732` / assertion2744 の3Dスタート状態検査（READY待機中にCOUNTDOWN→GO→RUNNINGへ進行）。後者は今回のrunで観測した別のタイミング失敗で、v4でも失敗していたとは主張しない。どちらも2.5D Pリグを読み込まないMotion Firstページの検査であり、対象外を修正しない。ログからの分類であり、タイミング失敗の再現・根治は未実施。[ステップ結果](evidence/p-rig-v5-20261015/ci-jobs.json)、[失敗ログ](evidence/p-rig-v5-20261015/ci-failures.txt)。

最終の証拠・レビュー追記commitは `[skip ci]` を付け、上記で実際に検査済みのコード・素材・テスト・workflowを変更せず保存する。最終commit自体に別のPASS runがあるとは扱わない。

## 判定

- KEEP: 4脚支持アンカー固定、70/68骨長、既存支持相・飛行区間、足画像・校正の保持。
- 局所改善: 全身比率、肩高、角張った頭・冠、胸郭と骨盤の相対運動、Androidの12超過解消。
- REVISE: 正規との体幹・前脚輪郭差、上腕の円盤感、肘付近の境界、前脚密集、足底ラスタ悪化、PC補正とレーン差増加。
- **総合REVISE、標準採用禁止。** テストPASSを造形完成の根拠にしない。
