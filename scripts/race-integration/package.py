"""Package the built game and its existing graphics for a local/LAN browser."""
import re
import sys
import zipfile
from pathlib import Path

root=Path(__file__).resolve().parents[2]
built=Path(sys.argv[1]).resolve()
destination=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else root/'public/race-integration/ridge-race-demo.zip'
# Never sweep another demo ZIP, node_modules or unrelated public experiments.
files={built/'index.html',built/'race-2_5d.html'}
for html in list(files):
    for asset in re.findall(r'["\']/evowild-test/(assets/[^"\']+)["\']',html.read_text()):
        files.add(built/asset)
for name in ('concept','race-integration'):
    files.update(p for p in (built/name).rglob('*') if p.is_file() and p.suffix not in {'.zip'} and p.name!='probe-actors.js')
if len(sys.argv)>2:
    report=built/'ridge-performance'
    files.update(p for p in report.rglob('*') if p.is_file() and (p.suffix!='.zip' or p.name=='raw.zip'))
for name in ('evowild-s.mtl','evowild-s.obj'):files.add(built/'models'/name)
lab=built/'s-pixel-lab'
for folder in (lab,lab/'v2',lab/'v3',lab/'v4',lab/'v4.1'):
    files.update(folder.glob('*.js'))
files.update([lab/'v3/assets/manifest.json',lab/'v3/assets/runtime/paint.gz',lab/'v4.1/index.html',lab/'v4.1/meter.css'])
for name in ('v2/assets/angles','v4/assets','v4.1/assets','v4.1/evidence'):
    files.update(p for p in (lab/name).rglob('*') if p.is_file())
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as archive:
    for file in sorted(files):
        relative=file.relative_to(built).as_posix()
        name='evowild-test/'+relative
        if relative=='race-integration/README.md':
            # Inside the archive, point directly to the unpacked game.
            archive.writestr(name,file.read_text().replace('[ビルド済み操作デモ ZIP](ridge-race-demo.zip)','[同梱の操作デモを開く](../?raceTrial=1)'))
        elif relative=='ridge-performance/README.md':
            body=file.read_text().replace('[ビルド済み操作デモ ZIP](ridge-optimized.zip)','[同梱の操作デモ](../?raceTrial=1)')
            body=body.replace('../../scripts/ridge-performance/', '../scripts/ridge-performance/')
            body=body.replace('../race-integration/ridge-race-demo.zip','https://raw.githubusercontent.com/badjoke-lab/evowild-test/b13743d5a473660f2b7979b504fcb32cda43ce11/public/race-integration/ridge-race-demo.zip')
            archive.writestr(name,body)
        else:
            archive.write(file,name)
    archive.write(root/'scripts/race-integration/README.md','evowild-test/scripts/race-integration/README.md')
    if len(sys.argv)>2:
        archive.write(root/'scripts/ridge-performance/README.md','evowild-test/scripts/ridge-performance/README.md')
    archive.writestr('index.html','<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/evowild-test/?raceTrial=1"><a href="/evowild-test/?raceTrial=1">EvoWild Run</a>')
    archive.writestr('README.txt','''EvoWild Run / Ridge Oval — S型v4.1 仮統合
ZIPを展開し、このREADMEと同じフォルダーで次を実行してください。
python3 -m http.server 8000 --bind 0.0.0.0
PC: http://localhost:8000/
Android: PCと同じWi-Fiに接続し、Chromeで http://PCのLANアドレス:8000/ を開く。
初期編成は通常の18体です。「出走設定」で頭数・編成を選んだら「新しいレース」。
「S型表示」は走行中に変更できます。実機計測と比較の手順は
evowild-test/race-integration/README.md にあります。
'''+('統合レースの改修前後の比較・負荷表・動画は http://localhost:8000/evowild-test/ridge-performance/ にあります。\n' if len(sys.argv)>2 else ''))
print(destination,destination.stat().st_size)
