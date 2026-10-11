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
OUT=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/multiview-visual-hull-v0"
OUT.mkdir(parents=True,exist_ok=True)

def mask(name,rm_floor):
    p=SOURCE/(name+"_CORE_COMPONENT_MASK.png")
    m=np.array(Image.open(p).convert("L"))>0
    # The source sheet ground baseline links otherwise unrelated paws at
    # the panel boundary. Strip only bottom ink rows; retain actual leg gaps.
    if rm_floor:m[-rm_floor:]=False
    mk=(m.astype(np.uint8)*255)
    mk=cv2.morphologyEx(mk,cv2.MORPH_CLOSE,
           cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))>0
    # Fill only truly enclosed SMALL white negative cavities (plated ink).
    inv=(~mk).astype(np.uint8)
    count,labels,stats,cent=cv2.connectedComponentsWithStats(inv,8)
    enclosed=[]
    height,width=mk.shape
    for i in range(1,count):
        x,y,w,h,area=map(int,stats[i])
        if x>1 and y>1 and x+w<width-1 and y+h<height-1 and area<=5500:
            mk[labels==i]=True
            enclosed.append(area)
    Image.fromarray((mk*255).astype(np.uint8)).save(OUT/(name+"_VOLUME_ART_MASK.png"))
    return mk,{"mask_size_xy":[mk.shape[1],mk.shape[0]],
               "source_foreground_pixels":int(np.count_nonzero(m)),
               "post_surgical_hole_fill_pixels":int(np.count_nonzero(mk)),
               "source_hole_fill_regions":enclosed,
               "ground_pixel_crop_rows":rm_floor}

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
path=OUT/"S-SOURCE-SIDE-FRONT-BACK-REAL-VOLUME-V0-NOT-APPROVED.obj"
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

Image.fromarray((projS.T[::-1,:]*255).astype(np.uint8)).save(OUT/"ACTUAL_3D_VOXEL_SIDE_PROJECTION.png")
Image.fromarray((volFront.T[::-1,:]*255).astype(np.uint8)).save(OUT/"ACTUAL_3D_VOXEL_FRONT_PROJECTION.png")
qa={
 "immutable_source_image_sha256":SHA,
 "image_source":"art/s-creature/references/00_s_type_modeling_image_v1.png",
 "source_extracted_orthogonal_views":["SIDE","FRONT","BACK"],
 "source_FRONT34_constrained_in_geometry":False,
 "all_pixels_original_not_AI_generated":True,
 "original_QEM_TRELLIS_R0_R5_A0_meshes_imported":False,
 "geometry_kind":"TRUE 3D source-constrained multiview visual hull; prototype silhouette scaffold",
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
 "numeric_source_side_silhouette_IoU":S_inter/S_union,
 "numeric_source_front_back_union_silhouette_IoU":FB_inter/FB_union,
 "relative_old_A0_geometry_imported":False,
 "canonical_design_visual_approved":False,
 "actual_3D_armor_parts_approved":False,
 "face_materials_and_eye_detail_approved":False,
 "rigged":False,
 "animated":False,
 "production_asset":False
}
(OUT/"REAL_SOURCE_MULTIVIEW_VOLUME_V0_QA.json").write_text(json.dumps(qa,indent=2)+"\n")
print("REAL_S_CANONICAL_VOLUME",qa["actual_mesh_3d_vertices"],qa["actual_mesh_triangles"],
      "SIDE_SOURCE_IOU",round(qa["numeric_source_side_silhouette_IoU"],4),
      "FRONTBACK_SOURCE_IOU",round(qa["numeric_source_front_back_union_silhouette_IoU"],4),
      "voxels",int(occ.sum()))
