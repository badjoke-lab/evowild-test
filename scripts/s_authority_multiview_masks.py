#!/usr/bin/env python3
"""Reference-locked EvoWild S orthographic silhouette extraction.

Produces VISUAL EVIDENCE only. This is not a creature model or an approved
segmentation. All original reference pixels preserved; masks generated from
fixed labeled panels with OpenCV GrabCut and explicit QA.
"""
import json,hashlib,urllib.request
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"art/s-creature/experiments/authority-visualhull"
OUT.mkdir(parents=True,exist_ok=True)
REF=OUT/"s-authority-unaltered.png"
URL="https://raw.githubusercontent.com/badjoke-lab/evowild-test/48b39d8b64aa5146dc2028876b448c3e884295e6/art/s-creature/references/00_s_type_modeling_image_v1.png"
SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
if not REF.exists() or hashlib.sha256(REF.read_bytes()).hexdigest()!=SHA:
    data=urllib.request.urlopen(URL,timeout=30).read()
    if hashlib.sha256(data).hexdigest()!=SHA:raise RuntimeError("SOURCE IMAGE HASH INVALID")
    REF.write_bytes(data)
if hashlib.sha256(REF.read_bytes()).hexdigest()!=SHA:
    raise RuntimeError("SOURCE IMAGE HAS CHANGED")
full=np.asarray(Image.open(REF).convert("RGB"))
assert full.shape==(1086,1448,3),full.shape
# Panel region boundaries deliberately preserve sharp black blade and foot tips.
panels={
 "side":(15,74,763,510),
 "front":(766,74,949,510),
 "back":(952,74,1126,510),
 "front34":(1128,74,1445,510)
}
report={"authority_sha256":SHA,"method":"GrabCut with foreground seed from luminance / nonneutral chroma","results":{},"validated":False}
thumbs=[]
for tag,(x0,y0,x1,y1) in panels.items():
    rgb=np.ascontiguousarray(full[y0:y1,x0:x1].copy())
    H,W=rgb.shape[:2]
    # Narrow outer band definitely outside the intended animal.
    seed=np.full((H,W),cv2.GC_PR_BGD,np.uint8)
    seed[:5,:]=cv2.GC_BGD
    seed[-4:,:]=cv2.GC_BGD
    seed[:,:4]=cv2.GC_BGD
    seed[:,-4:]=cv2.GC_BGD
    lum=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    # Visual creature has dark pigment with blue crest and pale sculpted plates.
    # Text/labels also are dark but disconnected and removed by CC selection.
    strong=(lum<152)&(hsv[:,:,2]<225)
    probable=(lum<228)|(hsv[:,:,1]>28)
    margin=np.zeros((H,W),dtype=np.uint8)
    margin[12:H-5,9:W-7]=1
    seed[(probable)&(margin>0)]=cv2.GC_PR_FGD
    seed[(strong)&(margin>0)]=cv2.GC_FGD
    bg=np.zeros((1,65),np.float64)
    fg=np.zeros((1,65),np.float64)
    # Exactly one deterministic segmentation, no artistic hallucinated mask.
    cv2.setRNGSeed(73021)
    cv2.grabCut(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),seed,None,bg,fg,7,cv2.GC_INIT_WITH_MASK)
    raw=np.where((seed==cv2.GC_FGD)|(seed==cv2.GC_PR_FGD),1,0).astype(np.uint8)
    raw=cv2.morphologyEx(raw,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8),iterations=1)
    comps,labels,stats,centroids=cv2.connectedComponentsWithStats(raw,8)
    candidates=[]
    for i in range(1,comps):
        x,y,w,h,area=stats[i].tolist()
        if area>80:
            candidates.append((int(area),i,(x,y,w,h)))
    candidates.sort(reverse=True)
    if not candidates:raise RuntimeError(tag+" segmentation no components")
    # Retain largest creature component; exclude panel labels / text / borders.
    main_id=candidates[0][1]
    animal=np.where(labels==main_id,255,0).astype(np.uint8)
    # Keep small detached sculpt blades only if close to primary silhouette
    near=cv2.dilate(animal,np.ones((11,11),np.uint8),iterations=1)
    for area,i,bounds in candidates[1:]:
        if area>=150 and np.count_nonzero((labels==i)&(near>0))>8:
            animal[labels==i]=255
    # preserve slender parts; fill isolated pinholes but no large smoothing.
    animal=cv2.morphologyEx(animal,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    ys,xs=np.where(animal>0)
    if not len(xs): raise RuntimeError(tag+" segmentation zero foreground")
    bb=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
    # Ground and crest positions must remain in silhouette's correct window.
    coverage=float(len(xs)/(W*H))
    if coverage<.022 or coverage>.72:raise RuntimeError(f"{tag} implausible mask coverage={coverage:.3f}")
    col=Image.fromarray(rgb)
    col.save(OUT/(tag+"_crop.png"))
    Image.fromarray(animal).save(OUT/(tag+"_mask.png"))
    rgba=np.concatenate([rgb,animal[:,:,None]],axis=2)
    Image.fromarray(rgba,"RGBA").save(OUT/(tag+"_masked.png"))
    overlay=rgb.copy().astype(np.float32)
    tint=np.zeros_like(overlay);tint[:,:,0]=216;tint[:,:,1]=75;tint[:,:,2]=52
    overlay[animal>0]=.77*overlay[animal>0]+.23*tint[animal>0]
    cv2.rectangle(overlay,(bb[0],bb[1]),(bb[2]-1,bb[3]-1),(40,210,160),2)
    tile=Image.fromarray(overlay.astype(np.uint8))
    tile.thumbnail((560,375))
    card=Image.new("RGB",(580,425),(236,239,242))
    card.paste(tile,((580-tile.width)//2,31))
    d=ImageDraw.Draw(card)
    d.text((12,9),f"{tag.upper()}  bounding={bb} coverage={coverage:.3f}",(0,0,0))
    thumbs.append(card)
    report["results"][tag]={"crop":[x0,y0,x1,y1],"crop_size":[W,H],"bbox_local":bb,
                            "coverage":coverage,"candidate_components":candidates[:10],
                            "biggest_component_area":candidates[0][0],
                            "mask_pixels":int(len(xs))}
sheet=Image.new("RGB",(1160,850),(238,241,244))
for i,t in enumerate(thumbs):sheet.paste(t,((i%2)*580,(i//2)*425))
sheet.save(OUT/"authority_four_view_segmentation_QA.jpg",quality=92,optimize=True)
report["validated"]=False
report["review_status"]="REVIEW_PENDING_MANUAL; not yet suitable for 3D hull"
(OUT/"SEGMENTATION_QA.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:{"coverage":v["coverage"],"bbox":v["bbox_local"],"components":len(v["candidate_components"])} for k,v in report["results"].items()},indent=2))
