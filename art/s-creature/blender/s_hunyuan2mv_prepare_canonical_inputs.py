"""EvoWild S: faithful canonical multi-view INPUTS, not a new concept image.
Exact original PNG + approved-source ink-based transparent masks only.
NO generated other-angle views; the source truly has LEFT SIDE, FRONT, BACK.
Outputs are evaluation inputs for free multi-view Hunyuan3D-2mv; unapproved.
"""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageChops,ImageOps,ImageDraw
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(ref.read_bytes()).hexdigest()==SHA
src=Image.open(ref).convert("RGB")
assert src.size==(1448,1086)
base=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/multiview-visual-hull-v1"
out=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/hunyuan2mv-original-source-20261012"
out.mkdir(parents=True,exist_ok=True)
# Model inputs are ONLY actual illustrated canonical views, not generated
# views or old incorrect QEM proxies.
sections={
  "front":{"region":"FRONT","crop":(764,90,946,507)},
  "back":{"region":"BACK","crop":(948,90,1129,507)},
  "left":{"region":"SIDE","crop":(28,73,760,507)}
}
rows={}
previews=[]
for slot,data in sections.items():
    r=data["region"]
    box=data["crop"]
    pixels=src.crop(box).convert("RGBA")
    mp=base/(r+"_TRUE_V1_NEGATIVE_SPACE_MASK.png")
    m=Image.open(mp).convert("L")
    assert pixels.size==m.size,(r,pixels.size,m.size)
    m=m.point(lambda a:255 if a>=128 else 0)
    bounds=m.getbbox()
    assert bounds is not None
    x0,y0,x1,y1=bounds
    # Exclude painted original ground line and detached component noise by
    # using only this source-derived 3D negative-space segmentation mask.
    rgb_crop=pixels.crop(bounds)
    crop_alpha=m.crop(bounds)
    rgb_crop.putalpha(crop_alpha)
    bbox_size=rgb_crop.size
    # Consistent humanoid/creature zoom across front and back (height
    # normalized), while side still fits its much wider original body.
    limit=466
    scale=min(limit/rgb_crop.width,limit/rgb_crop.height)
    newsize=(max(2,round(rgb_crop.width*scale)),max(2,round(rgb_crop.height*scale)))
    smooth=rgb_crop.resize(newsize,Image.Resampling.LANCZOS)
    canvas=Image.new("RGBA",(512,512),(255,255,255,0))
    # Ground alignment at 490px, top empty space reserved. No artwork edits.
    x=(512-newsize[0])//2
    y=490-newsize[1]
    canvas.alpha_composite(smooth,(x,y))
    target=out/("SOURCE_REAL_"+slot.upper()+"_ORTHO_RGBA.png")
    canvas.save(target)
    background=Image.new("RGBA",(512,512),(232,234,237,255))
    background.alpha_composite(canvas)
    previews.append(background.convert("RGB"))
    rows[slot]={
       "authoritative_png_sha256":SHA,
       "original_view":r,"original_full_png_crop":box,
       "source_alpha_mask":str(mp.relative_to(ROOT)),
       "original_foreground_bbox_in_crop":bounds,
       "original_subject_dims":bbox_size,
       "normalized_output":target.name,
       "normalized_size":newsize,
       "transparent_background":True,
       "source_3D_geometry_generated":False,
       "new_other_angle_synthesized":False,
       "readable_foot_contact_still_review_required":True,
       "output_sha256":hashlib.sha256(target.read_bytes()).hexdigest()
    }
sheet=Image.new("RGB",(1536,545),(243,244,245))
draw=ImageDraw.Draw(sheet)
for i,(name,img) in enumerate(zip(sections,previews)):
    sheet.paste(img,(i*512,33))
    draw.text((i*512+8,8),name.upper()+" — ORIGINAL S IMAGE MASKED",fill=(11,20,29))
sheet.save(out/"SOURCE_ORIGINAL_3_REAL_VIEWS_INPUT_AUDIT.jpg",quality=93,optimize=True)
report={"highest_authority_original_png":"art/s-creature/references/00_s_type_modeling_image_v1.png",
  "original_png_SHA256":SHA,
  "method":"CROP + ALPHA (actual source ink) + RESCALE, no generated art",
  "space":"tencent/Hunyuan3D-2mv",
  "public_ZeroGPU_only":True,
  "no_paid_GPU_no_subscription":True,
  "no_user_token_embedded":True,
  "source_public_GitHub":True,
  "license_not_yet_cleared_for_commercial_game":True,
  "front_back_left":rows,
  "right_view":None,
  "model_design_acceptance":"UNTESTED",
  "game_asset":False}
(out/"SOURCE_MULTIVIEW_INPUTS_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
print("REAL_MULTIVIEW_S_INPUTS_PREPARED",json.dumps({k:[v["normalized_size"],v["original_subject_dims"]] for k,v in rows.items()}))
