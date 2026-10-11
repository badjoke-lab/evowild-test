"""Source-constrained TRUE volume geometry: SIDE plus FRONT & BACK S art.

Use only exact original repository S-Type modeling image. NOT a game creature:
multi-view visual hull is a source-shape proxy for disproving/reviewing source
silhouette proportions, not surface armor details, correct rig, or a completed
design. It does not import ANY historic false S/trellis/QEM meshes.

Unlike A0's hand-guessed tube primitives, EVERY Y,Z silhouette occupancy here
comes directly from the SOURCE SIDE pixel mask and EVERY X,Z width profile
comes from SOURCE front/back images. Keep true holes between all visible legs.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
from scipy.ndimage import gaussian_filter, label
from skimage.measure import marching_cubes

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/"references/00_s_type_modeling_image_v1.png"
SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(REF.read_bytes()).hexdigest()==SHA
SOURCE=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/canonical-4view-pixel-trace-v1"
OUT=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/multiview-visual-hull-v1"
OUT.mkdir(parents=True,exist_ok=True)

source_bgr=cv2.imread(str(REF),cv2.IMREAD_COLOR)
source_panels={
    "SIDE":(28,73,760,507),
    "FRONT":(764,90,946,507),
    "BACK":(948,90,1129,507)}
assert source_bgr is not None and source_bgr.shape[:2]==(1086,1448)
def mask(name,rm_floor):
    # V0 consumed a filled EXTERNAL contour of the animal. It falsely
    # included entire vacant space between legs from the painted ground line.
    # V1 uses actual source PIXELS, not V0's erroneous filled silhouette.
    x0,y0,x1,y1=source_panels[name]
    rgb=source_bgr[y0:y1,x0:x1]
    hsv=cv2.cvtColor(rgb,cv2.COLOR_BGR2HSV)
    satur=hsv[:,:,1]/255.
    value=hsv[:,:,2]/255.
    dark=((satur>.085)&(value<.94))|(value<.66)
    dark=dark.astype(np.uint8)
    dark[:3,:]=0;dark[:,-3:]=0;dark[:,:3]=0
    if rm_floor:dark[-rm_floor:,:]=0
    dark=cv2.morphologyEx(dark,cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
    n,lab,stats,_=cv2.connectedComponentsWithStats(dark,8)
    assert n>=2,(name,"zero creature pixels")
    indices=sorted(range(1,n),key=lambda j:int(stats[j,cv2.CC_STAT_AREA]),reverse=True)
    main=indices[0]
    raw=(lab==main)
    # Enclosed white armor patches: preserve only small fully enclosed
    # regions within the actual body, NEVER interior underbody ground gaps.
    complement=(~raw).astype(np.uint8)
    count,hlab,hstats,_=cv2.connectedComponentsWithStats(complement,8)
    filled=raw.copy();holes=[]
    for k in range(1,count):
        xx,yy,w,h,area=map(int,hstats[k])
        enclosed=xx>1 and yy>1 and xx+w<raw.shape[1]-1 and yy+h<raw.shape[0]-1
        if enclosed and area<3800 and (name!="SIDE" or yy<245):
            filled[hlab==k]=True
            holes.append(area)
    if name=="SIDE":
        # This location is genuinely open air between the front/hind limbs
        # under the belly in the APPROVED original SIDE design.
        gap=filled[(355-y0):(466-y0),(404-x0):(480-x0)]
        open_space=float(np.count_nonzero(~gap))/gap.size
        assert open_space>.60,("reject solid slab/filled negative space",open_space)
    else:open_space=None
    Image.fromarray((filled*255).astype(np.uint8)).save(OUT/(name+"_TRUE_V1_NEGATIVE_SPACE_MASK.png"))
    return filled,{"mask_size_xy":[filled.shape[1],filled.shape[0]],
       "original_connected_nonfill_foreground_pixels":int(np.count_nonzero(raw)),
       "source_ink_main_component_pixels":int(stats[main,cv2.CC_STAT_AREA]),
       "final_mask_foreground_pixels":int(np.count_nonzero(filled)),
       "white_enclosed_holes_filled_only":holes,
       "ground_baseline_removed_pixel_rows":rm_floor,
       "between_legs_air_open_fraction":open_space,
       "V0_external_contour_fill_rejected":True}

side,sm=mask("SIDE",8)
front,fm=mask("FRONT",7)
back,bm=mask("BACK",7)
# Real original image orthographic registration in native-pixel coords:
# Z=0 at ground Y_IMG=504; all source panels share a consistent image
# height, roughly 105 px / normalized 3D unit.
# Y (object fore/aft) from SIDE x; X (object L/R) from FRONT and BACK x.
xs=np.linspace(-.94,.94,105,dtype=np.float32)
ys=np.linspace(-2.62,3.99,272,dtype=np.float32)
zs=np.linspace(-.08,4.06,178,dtype=np.float32)
dx=float(xs[1]-xs[0]);dy=float(ys[1]-ys[0]);dz=float(zs[1]-zs[0])
YPIX=332+110*ys
SIDE_PY=504-110*zs
FRONT_PY=504-(110*zs)*.925
SIDE_X=np.rint(YPIX-28).astype(int)
SIDE_Z=np.rint(SIDE_PY-73).astype(int)
FRONT_Z=np.rint(FRONT_PY-90).astype(int)
BACK_Z=np.rint(FRONT_PY-90).astype(int)
def collect_side():
    ny,nz=len(ys),len(zs)
    good=(SIDE_X[:,None]>=0)&(SIDE_X[:,None]<side.shape[1])&(SIDE_Z[None,:]>=0)&(SIDE_Z[None,:]<side.shape[0])
    x=np.clip(SIDE_X,0,side.shape[1]-1)
    z=np.clip(SIDE_Z,0,side.shape[0]-1)
    out=side[z[None,:],x[:,None]]&good
    return out
S=collect_side()
assert np.count_nonzero(S)>5000

# Width is SOURCE front/back silhouette at each height, NOT a guessed
# constant extrusion. Tail progressively converges, because source frontal
# widths depict shoulder/hips, not the tail spine behind them.
def smoother(arr):
    x=np.clip(arr,0,1)
    return x*x*(3-2*x)
tail_reduce=1-.82*smoother((ys-1.39)/2.18)
head_reduce=1-.22*smoother((-ys-1.58)/.70)
widthfac=np.minimum(tail_reduce,head_reduce)
Ywidth=np.maximum(.13,widthfac)
XQUERY=xs[:,None]/Ywidth[None,:] # X by Y, then Z
iF=np.rint(856+110*XQUERY-764).astype(int)
iB=np.rint(1036+110*XQUERY-948).astype(int)
iF=np.clip(iF,0,front.shape[1]-1)
iB=np.clip(iB,0,back.shape[1]-1)
VF=np.rint(856+110*XQUERY-764).astype(int)
VB=np.rint(1036+110*XQUERY-948).astype(int)
validF=(VF>=0)&(VF<front.shape[1])
validB=(VB>=0)&(VB<back.shape[1])
zF=np.clip(FRONT_Z,0,front.shape[0]-1)
zB=np.clip(BACK_Z,0,back.shape[0]-1)
goodZ=(FRONT_Z>=0)&(FRONT_Z<front.shape[0])&(BACK_Z>=0)&(BACK_Z<back.shape[0])
maskFront=front[zF[None,None,:],iF[:,:,None]] & validF[:,:,None] & goodZ[None,None,:]
maskBack=back[zB[None,None,:],iB[:,:,None]] & validB[:,:,None] & goodZ[None,None,:]
# Source-backed front/back union avoids treating inconsistent painted armor
# overlap from one projection as an actual zero-thickness slit in the other.
WIDTH=(maskFront|maskBack)
# Discrete voxel occupancy has THREE nontrivial dimensional axes, not a
# transparent image or flat plane.
occ=WIDTH & S[None,:,:]
assert 20000<occ.sum()<5000000,occ.sum()
# Smooth jagged segmentation without inventing new anatomy.
f=gaussian_filter(occ.astype(np.float32),sigma=(1.1,1.1,.83))
binary=f>.43
cc,n=label(binary)
size=np.bincount(cc.ravel())
keep=[i for i in range(1,n+1) if size[i]>120]
volume=np.isin(cc,keep)
f=gaussian_filter(volume.astype(np.float32),sigma=(.74,.75,.70))
vertices,faces,normals,values=marching_cubes(f,level=.45,spacing=(dx,dy,dz))
vertices+=np.array([xs[0],ys[0],zs[0]])
assert len(vertices)>2000 and len(faces)>3000
assert np.isfinite(vertices).all()
# Real conventional Blender-OBJ geometry. Axis X-left/right Y-back, Z-up.
path=OUT/"S-SOURCE-SIDE-FRONT-BACK-REAL-VOLUME-V1-NOT-APPROVED.obj"
with path.open("w") as o:
    o.write("# Source-driven actual S-type 3D triangle volume, NOT an approved sculpt\n")
    for v in vertices:o.write("v %.7f %.7f %.7f\n"%tuple(v))
    for i,j,k in faces+1:o.write("f %d %d %d\n"%(i,j,k))
# Numeric source-image projection overlap. Evaluated before rendering, so
# artistic resemblance is NOT inferred from triangles alone.
projS=volume.any(axis=0)
source_count=int(S.sum())
S_inter=int(np.count_nonzero(projS & S))
S_union=int(np.count_nonzero(projS | S))
srcF=(maskFront & S[None,:,:]).any(axis=1)
srcB=(maskBack & S[None,:,:]).any(axis=1)
volFront=volume.any(axis=1)
src2=srcF|srcB
FB_inter=int((src2&volFront).sum())
FB_union=int((src2|volFront).sum())

Image.fromarray((projS.T[::-1,:]*255).astype(np.uint8)).save(OUT/"ACTUAL_3D_VOXEL_SIDE_PROJECTION_V1.png")
Image.fromarray((volFront.T[::-1,:]*255).astype(np.uint8)).save(OUT/"ACTUAL_3D_VOXEL_FRONT_PROJECTION_V1.png")
qa={
 "immutable_source_image_sha256":SHA,
 "image_source":"art/s-creature/references/00_s_type_modeling_image_v1.png",
 "source_extracted_orthogonal_views":["SIDE","FRONT","BACK"],
 "source_FRONT34_constrained_in_geometry":False,
 "old_external_filled_mask_v0_corrected":True,
 "SIDE_open_space_below_belly_fraction":sm["between_legs_air_open_fraction"],
 "all_pixels_original_not_AI_generated":True,
 "original_QEM_TRELLIS_R0_R5_A0_meshes_imported":False,
 "geometry_kind":"TRUE 3D source-ink-derived visual hull preserving between-legs negative space; still technical scaffold",
 "axis_centers_from_exact_original_sheet_native_pixels":{
  "SIDE_Y_world_from_image_X_pixel":"(pixelX-332)/110",
  "Z_world_from_SIDE_pixel_Y":"(504-pixelY)/110",
  "FRONT_X_world_from_image_X":"(pixelX-856)/110",
  "BACK_X_world_from_image_X":"(pixelX-1036)/110",
  "FRONT_BACK_y_registration":"504-110*Z*0.925",
  "posterior_tail_width_taper_explicit_hypothesis":True
 },
 "side_source_foreground_info":sm,
 "front_source_foreground_info":fm,
 "back_source_foreground_info":bm,
 "grid_shape_XYZ":list(occ.shape),
 "real_occupancy_voxels":int(occ.sum()),
 "connected_occupancy_groups_remaining":len(keep),
 "actual_mesh_3d_vertices":len(vertices),
 "actual_mesh_triangles":len(faces),
 "actual_mesh_3d_bbox":[vertices.min(axis=0).tolist(),vertices.max(axis=0).tolist()],
 "numerical_projection_self_consistency_with_segmented_SIDE_mask_not_visual_fidelity":S_inter/S_union,
 "numerical_projection_self_consistency_with_segmented_FRONT_BACK_masks_not_visual_fidelity":FB_inter/FB_union,
 "relative_old_A0_geometry_imported":False,
 "canonical_design_visual_approved":False,
 "actual_3D_armor_parts_approved":False,
 "face_materials_and_eye_detail_approved":False,
 "rigged":False,
 "animated":False,
 "production_asset":False
}
(OUT/"REAL_SOURCE_MULTIVIEW_VOLUME_V1_QA.json").write_text(json.dumps(qa,indent=2)+"\n")
print("REAL_S_CANONICAL_VOLUME",qa["actual_mesh_3d_vertices"],qa["actual_mesh_triangles"],
      "SIDE_SOURCE_IOU",round(qa["numerical_projection_self_consistency_with_segmented_SIDE_mask_not_visual_fidelity"],4),
      "FRONTBACK_SOURCE_IOU",round(qa["numerical_projection_self_consistency_with_segmented_FRONT_BACK_masks_not_visual_fidelity"],4),
      "voxels",int(occ.sum()))
