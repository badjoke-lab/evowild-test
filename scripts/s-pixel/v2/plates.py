"""Comparison contact sheet. Both browser renders share the same crop and scale."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
D=ROOT/'public/s-pixel-lab/v2/evidence'
def font(n,bold=False):
    f=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc')
    return ImageFont.truetype(str(f),n) if f.exists() else ImageFont.load_default(size=n)
def put(im,a,r,bg='#d8e1db'):
    x,y,w,h=r;ImageDraw.Draw(im).rectangle((x,y,x+w-1,y+h-1),fill=bg)
    factor=min((w-12)/a.width,(h-10)/a.height)
    a=a.resize((max(1,round(a.width*factor)),max(1,round(a.height*factor))),Image.Resampling.NEAREST)
    im.paste(a,(round(x+(w-a.width)/2),round(y+(h-a.height)/2)),a.getchannel('A') if a.mode=='RGBA' else None)
def main():
    ref=Image.open(ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png')
    paper=Image.new('RGB',(1550,958),'#f6f6ef');d=ImageDraw.Draw(paper);d.rectangle((0,0,1550,83),fill='#233129')
    d.text((20,9),'EvoWild Run   /   Sprint Morph',font=font(32,True),fill='#faf9f1')
    d.text((22,55),'S–01    /    128 LAYERS    /    v1 → v2',font=font(15),fill='#e9bf9e')
    cols=[('side','側面',415,(62,69,753,505)),('front','正面',193,(789,106,928,507)),('rear','背面',193,(978,106,1110,507)),('top','上面',270,(1110,778,1430,846)),('quarter','斜め45°',301,(1138,87,1430,505))]
    scores={};x=102
    for k,title,w,rect in cols:
        d.text((x,94),title,font=font(21,True),fill='#293b2f')
        put(paper,ref.crop(rect),(x,132,w,216),'#e5ebee')
        if k=='top':d.text((x+9,318),'基準画は尾のみ',font=font(16),fill='#455546')
        a,b=[Image.open(D/(v+'-'+k+'.png')).convert('RGBA') for v in ('v1','v2')]
        ma,mb=[np.maximum.reduce(np.array(i)[:,:,:3],axis=2)>12 for i in (a,b)]
        scores[k]=round(float((ma&mb).sum()/(ma|mb).sum()),5)
        merged=Image.fromarray((ma|mb).astype('uint8'));bounds=merged.getbbox()
        for j,img in enumerate((a,b)):put(paper,img.crop(bounds),(x,363+j*271,w,255))
        d.text((x,907),f'輪郭 IoU  {scores[k]:.3f}',font=font(16),fill='#344939')
        x+=w+12
    for title,y in [('基準画',220),('v1',470),('v2',745)]:d.text((19,y),title,font=font(25,True),fill='#2c3c30')
    paper.save(D/'comparison.png',optimize=True)
    (D/'five-view-iou.json').write_text(json.dumps(scores,indent=2))
if __name__=='__main__':main()
