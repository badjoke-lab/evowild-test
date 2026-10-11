# 正規P型 v5 — 造形審査用の実モデル

最上位基準は変更していない `public/concept/P.webp`。v4の審査コミット
`c771ad323d0ad8bbcad7bebf222bfe642b130106` の次候補。
造形判定は [REVIEW.md](REVIEW.md) を参照。技術検証の成功だけではKEEPにしない。

- [実モデル GLB](../../../public/models/evowild-p/p-canonical-v5.glb)
- [正規P型・v4・v5比較](comparison-canonical-v4-v5.png)
- [5方向一覧](five-views.png)
- [SIDE](SIDE.png) / [FRONT](FRONT.png) / [FRONT34](FRONT34.png) / [REAR34](REAR34.png) / [BACK](BACK.png)
- [走行動画：6.4秒、SIDE/FRONT34各4周期](running-review.mp4)
- [MP4を実際にデコードした確認画像](video-decoded-contact-sheet.png)
- [走行位相と周期境界](running-contact-sheet.png)
- [GLB検証](gltf-validation.json) / [ブラウザー検証](browser-validation.json)
- [連続面の検査](topology-check.json) / [実GLBのスキニング・接地測定](skin-motion-validation.json)

## 制作方法

Blender 4.3.2。v4の外形ガイドと同じP型の頭部・足・尾の制作コードを継承。
独立した胸・肩・上腕の筋肉シェルは取り除き、胸郭、首、肩から前腕、腹、後脚を
0.026 mボクセルで一体化。面を平滑化し、同じ連続面に肩の扇状の隆起、上腕への流れ、
腋窩と胸の浅い溝を加えた。色はこの面の頂点色として付け、別メッシュの筋肉板にはしていない。
三角形削減はDecimateであり、手作業の四角形リトポロジーを完了したという意味ではない。

主要な連続面は1成分、境界辺0、非多様体辺0。頭、Cue Band、足先、尾などの
二次パーツまで全モデルが単一の閉曲面であるという主張ではない。
走行時は部品ごとの剛体追従を置き換え、胸・肩・上腕の共有面へ連続するボーン重みを配分した。

## 再現

リポジトリルートで以下を実行する。通常のHTTPサーバーとChromiumが起動できる環境が必要。

```sh
blender -b -t 4 --python scripts/modeling/build-canonical-p-v5.py -- --no-render
node scripts/modeling/finalize-p-v5.mjs
node scripts/modeling/validate-p-v5.mjs
npm run build
npm run dev -- --host 127.0.0.1 --port 4173
# 別ターミナル
node scripts/modeling/capture-p-review-v5.mjs
python3 scripts/modeling/package-p-evidence-v5.py
node scripts/modeling/check-p-skinning.mjs
```

`gltf-validator@2.0.0-dev.3.10`、Pillow、FFmpeg、Chromiumを使用。
GLBのdedup/pruneには `@gltf-transform/cli@4.3.0` を使用。
完全な手順は `.github/workflows/p-canonical-v5.yml`。
`--local` のfinalizeはネットワーク無しの予備表示用であり、提出GLBは通常の最適化を実行したもの。

静止画・動画はGLBの実描画。比較画像は既存の正規画像と実描画のレイアウトのみ。
新たな基準画像の生成、v1〜v4の上書き、mainへの変更・マージ、本番18体レースへの導入はしていない。
