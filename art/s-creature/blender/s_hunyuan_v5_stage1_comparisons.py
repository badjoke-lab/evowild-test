"""Contact sheets of genuine live-Blender renders and locked reference pixels."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/review-v5'
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


V4=OUT.parent/'review-v4'
tags=['SIDE','FRONT','FRONT34','REAR34','BACK']
sheet('V4_V5_STAGE1_FIVE_VIEW.jpg', [[('V4 '+t,V4/('V4_'+t+'.png')) for t in tags],[('V5 STAGE1 '+t,OUT/('V5_STAGE1_'+t+'.png')) for t in tags]],(440,352),'Actual V4 / V5 Stage 1 | matched Cycles, 24 samples | transition repair only')
tags=['SIDE','FRONT','FRONT34']
sheet('V4_V5_STAGE1_SHOULDER_DETAIL.jpg',[[('V4 DETAIL '+t,V4/('V4_DETAIL_'+t+'.png')) for t in tags],[('V5 STAGE1 DETAIL '+t,OUT/('V5_STAGE1_DETAIL_'+t+'.png')) for t in tags]],(600,480),'V4 / V5 Stage 1 | real matched shoulder detail renders | final art REVISE')
ref=Image.open(REF)
boxes={'SIDE':(233,210,424,384),'FRONT':(803,238,916,375),'FRONT34':(1192,225,1313,384)}
sheet('CANONICAL_V4_V5_STAGE1_DETAIL.jpg',[[('LOCKED CANONICAL '+t,ref.crop(boxes[t])) for t in tags],[('V4 DETAIL '+t,V4/('V4_DETAIL_'+t+'.png')) for t in tags],[('V5 STAGE1 DETAIL '+t,OUT/('V5_STAGE1_DETAIL_'+t+'.png')) for t in tags]],(600,480),'Reference pixels / V4 / V5 Stage 1 | pose and perspective differences retained | REVISE')
print('Three comparison sheets saved')
