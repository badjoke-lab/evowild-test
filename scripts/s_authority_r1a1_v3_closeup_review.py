"""Honest, fixed crop actual source R0 vs v3 mesh reconstruction.
Unmodified Blender renders only, not fake or synthetically painted outcomes.
"""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"art/s-creature/output/review"
OLD=BASE/"authority-r0-a6"
NEW=BASE/"authority-r1-a1-v3-topology"
VIEWS=("front34","rear34","side")
ROI={"front34":(332,286,689,492),"rear34":(330,280,717,495),"side":(292,276,708,505)}
W,H=490,355
page=Image.new("RGB",(3*W,3*H),(241,244,247))
draw=ImageDraw.Draw(page)
stats={}
for row,name in enumerate(VIEWS):
    a=Image.open(OLD/f"S_authority_r0_a6_{name}.png").convert("RGB")
    b=Image.open(NEW/f"S_R1_A1_v3_{name}.png").convert("RGB")
    assert a.size==b.size==(1024,768),a.size
    ac=np.asarray(a,dtype=np.int16);bc=np.asarray(b,dtype=np.int16)
    raw=np.abs(ac-bc)
    dmax=raw.max(axis=2)
    x1,y1,x2,y2=ROI[name]
    msk=dmax[y1:y2,x1:x2]
    diag=np.stack([np.clip(msk*5,0,255),np.clip(msk*.8,0,255),np.zeros_like(msk)],axis=2).astype(np.uint8)
    visuals=(("R0 APPROVED BLOCKOUT",a.crop(ROI[name])),
             ("R1-A1 v3 ACTUAL MESH",b.crop(ROI[name])),
             ("ABS PIXEL CHANGE x5",Image.fromarray(diag)))
    for col,(label,im) in enumerate(visuals):
        im=ImageOps.contain(im,(W-16,H-37),Image.Resampling.LANCZOS)
        page.paste(im,(col*W+(W-im.width)//2,row*H+28+(H-30-im.height)//2))
        draw.text((col*W+10,row*H+10),label+" / "+name.upper(),(16,19,22))
    stats[name]={
      "crop_xyxy":list(ROI[name]),
      "pixels_changed_threshold_14":int((msk>=14).sum()),
      "fraction_changed_threshold_14":float((msk>=14).mean()),
      "max_rgb_difference":int(msk.max()),
      "mean_absolute_max_channel_difference":float(msk.mean())
    }
dst=NEW/"S_R0_vs_R1A1v3_shoulder_pelvis_real_closeup.jpg"
page.save(dst,quality=93,optimize=True)
(NEW/"S_R1A1v3_pixels_QA.json").write_text(json.dumps({
 "method":"fixed camera identical-resolution actual Blender render local crops",
 "meaning":"measures visual magnitude only, not artistic approval",
 "stats":stats
},indent=2)+"\n")
print("ACTUAL_LOCAL_DIFFERENCES",json.dumps(stats))
