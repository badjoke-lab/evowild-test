# S–01 ボクセル原本

静止1姿勢と四足走行24姿勢の正式な原本を [`assets/voxels/`](../../../public/s-pixel-lab/v3/assets/voxels/) に保存している。各姿勢は17色＋透明のボクセル配列1個で表現する。横断面、近景のサーフェスメッシュ、遠景の色・深度スプライトはこの原本から生成する。

## 配列の読み方

[`index.json`](../../../public/s-pixel-lab/v3/assets/voxels/index.json) に25姿勢の順序、足の支持フラグ、周期、パレット、グリッドからワールドへの変換、姿勢ごとのチェックサムがある。`.u8.gz` はヘッダーのないC順序の `uint8` 配列をgzip圧縮したファイルで、SHA256の対象は展開後のバイト列。配列の添字は `[y,z,x]`、サイズは `128 × 60 × 283`。`y=0` が床、`x` は鼻から尾へ増える。色番号0は空で、1～17は目録のRGB値を指す。全原本を合わせた圧縮サイズは約601 KiB。

```python
from pathlib import Path
import gzip, hashlib, json
import numpy as np

root = Path('public/s-pixel-lab/v3/assets/voxels')
index = json.loads((root / 'index.json').read_text())
pose = index['poses'][1]  # run-00
raw = gzip.decompress((root / pose['file']).read_bytes())
assert hashlib.sha256(raw).hexdigest() == pose['sha256']
volume = np.frombuffer(raw, dtype=np.uint8).reshape(index['shape'])
```

セル `(x,y,z)` の外側角は `originXYZ + [x,y,z] * stepXYZ`、中心は各軸に半セル足した位置。値はそれぞれ `[-420,0,-118.8]`、`[3,3.625,3.96]`。足先の `toe` はv2から継承した側面作画上の座標で、ワールド座標への変換は `worldX = toeX - 385`、`worldY = 502 - toeY`。

## 原本と断面の再生成

リポジトリルートで実行する。Python 3、NumPy、Pillow、SciPyを使う。

```sh
python3 scripts/s-pixel/v3/volume.py source
python3 scripts/s-pixel/v3/volume.py stacks
python3 scripts/s-pixel/v3/volume.py verify
python3 scripts/s-pixel/v3/directions.py
```

`source` はSHA256を照合した基準画像のもと、4方向の既存部位画、ポーズ変換、v2で確定した頭冠・脚軌道補正を適用する。`stacks` は原本を読み直し、全128段をそのまま断面化する。64段では各2層の中央サンプルを優先し、透明部分を同じ帯のもう一層で補って細い部位を保つ。`verify` は出力PNGを登録座標に展開し、各セルの色番号をv2と照合する。今回の25姿勢では64段・128段とも差分0セル、128段から原本への復元も差分0セル。[検証結果](../../../public/s-pixel-lab/v3/evidence/voxel-roundtrip.json)

原本を直接修正して試す場合は `voxels/` 一式を作業用の `assets/` にコピーする。対象の配列、目録の展開後SHA256と占有セル数を更新して `volume.py stacks --assets /path/to/assets` を実行する。`directions.py --assets /path/to/assets` で同じ修正を遠景に適用できる。作画から修正する場合は最初の `source` 工程から再生成する。

## 遠景スプライト

[`directions.py`](directions.py) は128段のPNG全25枚、各層の登録座標、原点・寸法、パレット、生成シェーダーとメッシュ化・色変換コードのSHA256を確認する。今回の入力はv2と一致するため、既存アトラス20ページと目録のSHA256を検証して、同一の色・深度ページを共有する。実際に使う目録のURLは [`assets/directions.json`](../../../public/s-pixel-lab/v3/assets/directions.json) の `index`。相対URLの基点はこの記述ファイルのURLで、各PNGのURLはスプライト目録を基点に解決する。

入力や生成コードが変わると、一時ビルドディレクトリにv2のベイク用プログラムを展開し、v3の断面を入力として再実行する。48方位、俯角0～90°を10°刻み、25姿勢の12,000画像。4点被覆と表面深度も同じ投影から取得する。異なる出力はv3の `assets/angles-<hash>/` に保存し、`directions.json` を更新する。全生成にはNode、Playwright、ChromiumとローカルHTTPサーバーが必要。`CHROMIUM_PATH` でChromiumのパスを指定できる。

```sh
python3 scripts/s-pixel/v3/directions.py --force
python3 scripts/s-pixel/v3/check-regeneration.py
```

2つ目のコマンドは一時コピーの静止姿勢に含まれる色番号9と10を交換し、色差がどのポーズ・角度に伝わるかを12,000画像で検査する。公開する原本・スプライトへの書き込みは行わない。
