#!/usr/bin/env python3
"""Create a reproducible crop/difference audit from actual R0 / R1 renders.

Source files: real Blender PNGs from locked same cameras. Difference images
are diagnostic only, not fake rendered geometry nor visual acceptance.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps,ImageEnhance

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"art/s-creature/output/review"
R0=BASE/"authority-r0-a6"
R1=BASE/"authority-r1-a1-trial"
VIEWS=("front34","rear34","side")
PANEL_W=440
PANEL_H=465
SHEET=Image.new("RGB",(PANEL_W*3,PANEL_H*len(VIEWS)),(246,247,248))
DRAW=ImageDraw.Draw(SHEET)
results={}

for row,view in enumerate(VIEWS):
    pa=R0/("S_authority_r0_a6_"+view+".png")
    pb=R1/("S_authority_r1_a1_"+view+".png")
    a=Image.open(pa).convert("RGB")
    b=Image.open(pb).convert("RGB")
    if a.size!=b.size:raise RuntimeError(f"{view} size or camera mismatch")
    ar=np.asarray(a).astype(np.int16)
    br=np.asarray(b).astype(np.int16)
    delta=np.max(np.abs(ar-br),axis=2)
    moved=delta>=14
    N=int(moved.sum())
    if N<50:raise RuntimeError(f"{view}: insufficient visible pixel delta: {N}")
    ys,xs=np.where(moved)
    h,w=delta.shape
    # Crop centered at actual changed pixels, with enough context around limbs.
    l=int(np.percentile(xs,1));r=int(np.percentile(xs,99))+1
    t=int(np.percentile(ys,1));bot=int(np.percentile(ys,99))+1
    edge=int(max(30,.14*max(r-l,bot-t)))
    l=max(0,l-edge);r=min(w,r+edge)
    t=max(0,t-edge);bot=min(h,bot+edge)
    if r-l<180:
        extra=(180-(r-l))//2;l=max(0,l-extra);r=min(w,r+extra)
    if bot-t<180:
        extra=(180-(bot-t))//2;t=max(0,t-extra);bot=min(h,bot+extra)
    roi=(l,t,r,bot)
    aroi=a.crop(roi)
    broi=b.crop(roi)
    # Colorize the absolute pixel deltas. This is not visual morphology.
    d=np.clip(delta[t:bot,l:r].astype(np.float32)*4,0,255).astype(np.uint8)
    heat=np.stack([d,(d*.24).astype(np.uint8),np.zeros_like(d)],axis=2)
    heatpic=Image.fromarray(heat,"RGB")
    for col,(name,im) in enumerate([("R0 ACTUAL",aroi),("R1 ACTUAL",broi),("PIXEL CHANGE x4",heatpic)]):
        thumb=ImageOps.contain(im,(PANEL_W-18,PANEL_H-45),method=Image.Resampling.LANCZOS)
        xx=col*PANEL_W+(PANEL_W-thumb.width)//2
        yy=row*PANEL_H+35+(PANEL_H-42-thumb.height)//2
        SHEET.paste(thumb,(xx,yy))
        DRAW.text((col*PANEL_W+12,row*PANEL_H+9),f"{name} / {view.upper()}",fill=(12,16,20))
    results[view]={
       "pixel_dimensions":[w,h],"crop":list(roi),
       "changed_pixels_threshold_14":N,
       "changed_fraction":float(N/(w*h)),
       "max_pixel_difference":int(delta.max()),
       "mean_pixel_difference":float(delta.mean())
    }
p=R1/"R1_A1_three_region_actual_zoom_comparison.jpg"
SHEET.save(p,quality=92,optimize=True)
(R1/"R1_A1_image_delta_QA.json").write_text(json.dumps({
  "source":"existing real R0 and R1 unchanged-camera Blender five-view PNGs",
  "meaning":"pixel differences only; do not interpret as improvement without visual review",
  "diagnostics":results
},indent=2)+"\n")
print(json.dumps(results,indent=2))
