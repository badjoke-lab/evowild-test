"""Encode the complete one-sample LOD sweep, in both directions."""
import json,sys,subprocess
from pathlib import Path
from PIL import Image,ImageDraw

here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'v3'))
import plates as p
out=p.ROOT/'public/s-pixel-lab/v4.1/evidence'
recipes=[r for r in json.loads((p.CACHE/'recipes.json').read_text()) if r['group']=='switch']
v4='v4-lod-race';candidate='v4.1-lod-race'
draws=json.loads((p.CACHE/candidate/'draws.json').read_text())
ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1024x392','-r','24','-i','-',
                     '-an','-c:v','libx264','-threads','2','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'lod-switch.mp4')],stdin=subprocess.PIPE)
for r in recipes+recipes[-2::-1]:
    im=Image.new('RGB',(1024,392),p.INK);d=ImageDraw.Draw(im)
    for x,k,label in [(0,v4,'v4'),(512,candidate,'v4.1')]:
        im.paste(Image.fromarray(p.pixels(k,r['id'])),(x,36))
        p.text(d,(x+12,3),label+'　単一サンプル',17,'white',True)
    m=draws[r['id']]['mix']
    stage='スプライト' if m['sprite'] else '移行' if m['transition'] else '中距離メッシュ' if m['mid'] else '近景メッシュ'
    p.text(d,(12,360),f"{r['span']:.1f} px　 {stage}　 ／　 同じ走行位相・視点、24 fps 固定時刻再生",16,'white')
    ff.stdin.write(im.tobytes())
ff.stdin.close()
if ff.wait():raise RuntimeError('Video encoding failed')
