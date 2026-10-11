"""S Type only user-approved source: pixel-coordinate anatomical silhouette traces.

Unlike all previous approaches, this reads the real canonical design PNG
directly, extracts FOUR *actually depicted* views via CV2 segmentation, and
stores exact pixel contours and side-by-side overlay. No donor mesh, no
new "reference" image, no heuristic invented creature modeling geometry.
This data will be used to constrain sculpt—not pass a model as approved.
"""
from pathlib import Path
import hashlib,json
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
IMAGE=ROOT/"references/00_s_type_modeling_image_v1.png"
OUT=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/canonical-4view-pixel-trace-v1"
OUT.mkdir(parents=True,exist_ok=True)
SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(IMAGE.read_bytes()).hexdigest()==SHA
src=cv2.imread(str(IMAGE),cv2.IMREAD_COLOR)
assert src is not None and src.shape[:2]==(1086,1448),src.shape

# Genuine four complete character art panels, not artificial additional
# views. Includes all visible crest spikes and feet, but excludes title/
# silhouette/thumbnail area. ROI frames are auditable original-PNG coords.
regions={
    "SIDE":(28,73,760,507),
    "FRONT":(764,90,946,507),
    "BACK":(948,90,1129,507),
    "FRONT34":(1131,80,1433,507),
}

def trace(region, name, sat_gate=.085, val_gate=.66):
    x0,y0,x1,y1=region
    roi=src[y0:y1,x0:x1].copy()
    hsv=cv2.cvtColor(roi,cv2.COLOR_BGR2HSV)
    sat=hsv[:,:,1]/255.
    val=hsv[:,:,2]/255.
    # Dark true blues/violet and saturated feathers, NOT gray paper.
    core=( ((sat>sat_gate)&(val<.94)) | (val<val_gate) ).astype(np.uint8)
    core[:4,:]=0; core[-3:,:]=0
    core[:,:3]=0; core[:,-3:]=0
    # Only join 1-3 px broken stroke from exported concept PNG.
    core=cv2.morphologyEx(core,cv2.MORPH_CLOSE,
               cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
    stats_n, labels, stats, centroids=cv2.connectedComponentsWithStats(core,8)
    comps=[]
    for idx in range(1,stats_n):
        xx,yy,w,h,area=map(int,stats[idx])
        if area>25:
            comps.append({"id":idx,"box_local":[xx,yy,w,h],"pixel_count":area})
    comps.sort(key=lambda c:c["pixel_count"],reverse=True)
    # Main illustrated animal is largest dark connected component. Any
    # detached crest/tail/toe ink is logged rather than silently invented.
    assert comps, (name,"no color foreground found")
    main=comps[0]
    mask=(labels==main["id"]).astype(np.uint8)*255
    # Fill white plates that are entirely surrounded by animal ink.
    contours,hierarchy=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    c=max(contours,key=cv2.contourArea)
    fill=np.zeros_like(mask);cv2.drawContours(fill,[c],-1,255,cv2.FILLED)
    # Contour is a source-derived silhouette (NOT an original 3D model).
    epsilon=1.55
    approx=cv2.approxPolyDP(c,epsilon,True).reshape(-1,2)
    abs_points=(approx+np.array([x0,y0])).astype(int).tolist()
    extracted={
      "view":name,"original_crop_pixels":[x0,y0,x1,y1],
      "source_pixel_coordinates_are_authority_not_A0_geometry":True,
      "dark_core_connected_components":comps[:12],
      "main_component_native_box":[int(x0+v) if i==0 else int(y0+v) if i==1 else int(v) for i,v in enumerate(main["box_local"])],
      "main_component_pixels":int(main["pixel_count"]),
      "filled_silhouette_pixels":int(np.count_nonzero(fill)),
      "contour_n_vertices":len(abs_points),
      "contour_native_pixels_XY":abs_points,
      "contour_approx_pixel_epsilon":epsilon,
      "EXTRA_detached_illustration_pieces_or_letter_labels":comps[1:12],
      "not_authorized_as_new_master_reference":True,
      "requires_visual_manual_verification":True
    }
    # Overlay original paper with unmodified image beneath transparent colors.
    rgb=cv2.cvtColor(roi,cv2.COLOR_BGR2RGB)
    overlay=rgb.copy()
    contours2=[(c+np.array([[[0,0]]],dtype=c.dtype))]
    cv2.drawContours(overlay,[c],-1,(250,50,32),2)
    aa=cv2.addWeighted(rgb,.66,overlay,.34,0)
    for p in approx[::max(1,len(approx)//50)]:
        cv2.circle(aa,(int(p[0]),int(p[1])),2,(255,26,24),-1)
    Image.fromarray(aa).save(OUT/(name+"_TRUE_SOURCE_CONTOUR_OVERLAY.png"))
    Image.fromarray(fill).save(OUT/(name+"_CORE_COMPONENT_MASK.png"))
    return extracted,Image.fromarray(aa)

all_data={}
tiles={}
for name,box in regions.items():
    all_data[name],tiles[name]=trace(box,name)
    print("S_ACTUAL_CANONICAL",name,
          "connected_ink",all_data[name]["main_component_pixels"],
          "contour_vertices",all_data[name]["contour_n_vertices"],
          "bbox",all_data[name]["main_component_native_box"],
          "components",[(x["pixel_count"],x["box_local"]) for x in
                        all_data[name]["dark_core_connected_components"][:4]])

master={
 "S_reference_exact_path":"art/s-creature/references/00_s_type_modeling_image_v1.png",
 "S_reference_sha256":SHA,"S_reference_original_dimensions":[1448,1086],
 "method":"color/dark-pixel component segmentation from original saved PNG, no generative concept",
 "source_views_real_not_inferred":["SIDE","FRONT","BACK","FRONT34"],
 "source_panels":all_data,
 "not_approved_for_modeling_until_overlay_review":True,
 "not_a_3D_creature":True,
 "original_source_png_untouched":True,
 "main_updated":False
}
(OUT/"ACTUAL_CANONICAL_S_PIXEL_CONTOURS.json").write_text(
   json.dumps(master,ensure_ascii=False,indent=2)+"\n")
# Side by side original exact source panels with contour; no black background,
# no generative content. This shows mistakes honestly.
W=780;H=460
sheet=Image.new("RGB",(2*W,4*H),(242,243,244))
draw=ImageDraw.Draw(sheet)
original=Image.open(IMAGE).convert("RGB")
for i,name in enumerate(regions):
    x0,y0,x1,y1=regions[name]
    for col,(label,im) in enumerate([
         ("EXACT SOURCE / "+name, original.crop((x0,y0,x1,y1))),
         ("ORIGINAL+CV CONTOUR / "+name, tiles[name])]):
        im.thumbnail((W-22,H-42))
        sheet.paste(im,(col*W+(W-im.width)//2,i*H+36+(H-36-im.height)//2))
        draw.text((col*W+8,i*H+8),label,fill=(20,23,27))
sheet.save(OUT/"SOURCE_VS_ACTUAL_PIXEL_TRACE_FOUR_VIEWS.jpg",quality=91,optimize=True)
print("ACTUAL_CANONICAL_VIEWS_TRACED",list(regions))
