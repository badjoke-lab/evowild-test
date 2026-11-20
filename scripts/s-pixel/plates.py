"""Assemble human-readable plates from original reference crops and actual browser readbacks."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from bake import ROOT,OUT
E=OUT.parent/'evidence'
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
BOLD='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def ft(n,bold=False):
    try:return ImageFont.truetype(BOLD if bold else FONT,n,index=0)
    except OSError:return ImageFont.load_default(size=n)
def box(im,src,rect,bg='#dce3df',pixel=False,trim=True):
    a=Image.open(src) if isinstance(src,(str,Path)) else src.copy()
    if trim and 'A' in a.mode and a.getbbox():a=a.crop(a.getbbox())
    x,y,w,h=rect
    ImageDraw.Draw(im).rectangle((x,y,x+w-1,y+h-1),fill=bg)
    scale=min((w-18)/a.width,(h-16)/a.height)
    a=a.resize((max(1,round(a.width*scale)),max(1,round(a.height*scale))),Image.Resampling.NEAREST if pixel else Image.Resampling.LANCZOS)
    im.paste(a,(x+(w-a.width)//2,y+(h-a.height)//2),a.getchannel('A') if 'A' in a.mode else None)
def heading(im,subtitle):
    d=ImageDraw.Draw(im);d.rectangle((0,0,im.width,77),fill='#26332d')
    d.rectangle((24,21,30,56),fill='#f48650');d.text((43,9),'EvoWild Run   /   S–01',font=ft(28,True),fill='#f9f8ee')
    d.text((43,47),subtitle,font=ft(14),fill='#c8d1c7')
def label(im,xy,txt):ImageDraw.Draw(im).text(xy,txt,font=ft(18,True),fill='#26332d')
def main():
    ref=Image.open(ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png').convert('RGB')
    im=Image.new('RGB',(1500,917),'#f7f7ee')
    heading(im,'MODEL SHEET  /  造形基準と128層のブラウザ描画')
    columns=[('side','側面',(62,69,753,505),437),('front','正面',(789,106,928,507),193),('rear','背面',(978,106,1110,507),193),('top','上面',(1110,778,1430,846),258),('quarter','斜め45°',(1138,87,1430,505),316)]
    x=24
    for name,title,crop,w in columns:
        label(im,(x,88),title);box(im,ref.crop(crop),(x,123,w,233),'#e3e8ed')
        if name=='top':ImageDraw.Draw(im).text((x+8,325),'原画は尾のみ',font=ft(14),fill='#34443a')
        box(im,OUT/'views'/(name+'.png'),(x,371,w,233),pixel=True)
        x+=w+12
    label(im,(24,617),'旧実験と今回の側面')
    old=Image.open(E/'previous-side.png')
    # Lower-right cell in the archived six-panel capture is its 128-slice view.
    tile=old.crop((2*old.width//3,old.height//2,old.width,old.height))
    box(im,tile,(24,651,698,207),bg='#e0e3d7')
    box(im,OUT/'views/side.png',(739,651,737,207),pixel=True)
    ImageDraw.Draw(im).text((24,865),'11/18   D3-C v2 ・ 128層 ・ 走行中 ・ 俯角35°',font=ft(16),fill='#475549')
    ImageDraw.Draw(im).text((739,865),'今回   新規ピクセル作画 ・ 128層 ・ 静止姿勢 ・ 俯角0°',font=ft(16),fill='#475549')
    im.save(E/'comparison.png',optimize=True)
    p=Image.new('RGB',(1224,1007),'#f6f6ee');heading(p,'GALLOP  /  24ポーズ・同一カメラ・同一縮尺')
    for f in range(24):
        x=16+(f%4)*300;y=91+(f//4)*151
        a=Image.open(E/f'pose-{f:02}.png')
        box(p,a,(x,y,292,134),pixel=True,trim=False)
        ImageDraw.Draw(p).text((x+5,y+1),f'{f+1:02}',font=ft(13),fill='#49554a')
    p.save(E/'gait-cycle.png',optimize=True)
if __name__=='__main__':main()
