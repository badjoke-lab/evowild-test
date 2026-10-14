"""Contact sheets of genuine live-Blender renders and locked reference pixels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/review-v4'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
def sheet(name, rows, cell, title):
    width,height=cell
    im=Image.new('RGB',(width*len(rows[0]),(height+28)*len(rows)+48),(232,237,241))
    draw=ImageDraw.Draw(im)
    draw.text((12,15),title,fill='black')
    for r,row in enumerate(rows):
        for c,(label,src) in enumerate(row):
            pic=Image.open(src).convert('RGB') if isinstance(src,Path) else src.convert('RGB')
            pic=ImageOps.contain(pic,(width-12,height-12))
            x=c*width+(width-pic.width)//2;y=48+r*(height+28)
            draw.text((c*width+10,y+5),label,fill='black')
            im.paste(pic,(x,y+28+(height-pic.height)//2))
    im.save(OUT/name)

tags=['SIDE','FRONT','FRONT34','REAR34','BACK']
sheet('V3_V4_FIVE_VIEW.jpg', [[(v+' '+t,OUT/(v+'_'+t+'.png')) for t in tags] for v in ['V3','V4']],(440,352),'V3 / V4 | same Cycles lighting and orthographic framing | real geometry')
tags=['SIDE','FRONT','FRONT34']
sheet('V3_V4_SHOULDER_CHEST_UPPERARM.jpg',[[(v+' DETAIL '+t,OUT/(v+'_DETAIL_'+t+'.png')) for t in tags] for v in ['V3','V4']],(600,480),'Shoulder / chest / upper arm | V3 above, V4 below | real Cycles renders')
sheet('CANONICAL_V3_V4.jpg', [[('LOCKED CANONICAL '+t,OUT/('CANONICAL_CROP_'+t+'.png')) for t in tags]]+[[(v+' '+t,OUT/(v+'_'+t+'.png')) for t in tags] for v in ['V3','V4']],(600,450),'Locked reference / V3 / V4 | source pose and illustrated perspective differences retained')
ref=Image.open(REF)
boxes={'SIDE':(233,210,424,384),'FRONT':(803,238,916,375),'FRONT34':(1192,225,1313,384)}
sheet('CANONICAL_V3_V4_SHOULDER_DETAIL.jpg',[[('CANONICAL DETAIL '+t,ref.crop(boxes[t])) for t in tags]]+[[(v+' DETAIL '+t,OUT/(v+'_DETAIL_'+t+'.png')) for t in tags] for v in ['V3','V4']],(600,480),'Canonical shoulder planes / V3 / V4 | pixel crops and actual 3D renders, no retouching')
print('Four comparison sheets saved')
