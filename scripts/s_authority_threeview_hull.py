#!/usr/bin/env python3
"""One bounded S 3-view shape-from-silhouette test.

Side and front are primary constraints; the actual approved front 3/4 drawing
carves away geometric solutions impossible from that third camera.
Back remains held-out for evaluation. No generated sculpt substitutions.
"""
import numpy as np,cv2,json,hashlib
from pathlib import Path
import scipy.ndimage as ndi,trimesh
from skimage.measure import marching_cubes

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"art/s-creature/experiments/authority-visualhull"
OUT=BASE/"hull-v2-three-view";OUT.mkdir(exist_ok=True)
qa=json.loads((BASE/"SEGMENTATION_QA.json").read_text())
SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert qa["authority_sha256"]==SHA
assert hashlib.sha256((BASE/"s-authority-unaltered.png").read_bytes()).hexdigest()==SHA

def mask(name):
    m=cv2.imread(str(BASE/(name+"_mask.png")),cv2.IMREAD_GRAYSCALE)
    assert m is not None and m.max()>200
    return m>127

side,front,diag=mask("side"),mask("front"),mask("front34")
Nx,Ny,Nz=110,244,184
xmin,xmax=-.51,.51
ymin,ymax=-1.64,1.72
zmin,zmax=-.03,2.60
xx=np.linspace(xmin,xmax,Nx)
yy=np.linspace(ymin,ymax,Ny)
zz=np.linspace(zmin,zmax,Nz)
dx,dy,dz=xx[1]-xx[0],yy[1]-yy[0],zz[1]-zz[0]
def map_z(m,bb):
    ind=np.rint(bb[3]-1-(zz-zmin)/(zmax-zmin)*(bb[3]-bb[1]-1)).astype(int)
    return np.clip(ind,0,m.shape[0]-1)
def proj_base(m,bb,coord):
    mx=np.rint(bb[0]+(coord-coord.min())/(coord.max()-coord.min())*(bb[2]-bb[0]-1)).astype(int)
    return m[map_z(m,bb)[None,:],np.clip(mx,0,m.shape[1]-1)[:,None]]

side2=proj_base(side,qa["results"]["side"]["bbox_local"],yy)
front2=proj_base(front,qa["results"]["front"]["bbox_local"],xx)
base=front2[:,None,:]&side2[None,:,:]
base_n=int(base.sum())
if base_n<15000:raise RuntimeError("Empty 2-view prior")

# Exact third camera coordinate: FROM (x positive, y negative) looking to origin.
# Camera right is +x,+y. This maps the creature nose left and tail right.
right=(xx[:,None]+yy[None,:])/np.sqrt(2)
ind=np.where(base)
rlist=right[ind[0],ind[1]]
rmin,rmax=np.quantile(rlist,[.0002,.9998])
margin=(rmax-rmin)*.012
rmin-=margin;rmax+=margin

diagbb=qa["results"]["front34"]["bbox_local"]
source_diag=cv2.dilate(diag.astype(np.uint8),np.ones((3,3),np.uint8),iterations=1)>0
xi=np.rint(diagbb[0]+((right-rmin)/(rmax-rmin))*(diagbb[2]-diagbb[0]-1)).astype(int)
# Off-screen voxels should never pass visual-hull gating.
valid=(xi>=0)&(xi<diag.shape[1])
xi=np.clip(xi,0,diag.shape[1]-1)
zi=map_z(diag,diagbb)
third=source_diag[zi[None,None,:],xi[:,:,None]]&valid[:,:,None]
trimmed=base&third
trimmed_n=int(trimmed.sum())
fraction=trimmed_n/base_n
if fraction<.20:
    raise RuntimeError(f"Third view inconsistent: retains {fraction:.1%}, revise camera calibration rather than accepting bad model.")

blur=ndi.gaussian_filter(trimmed.astype(np.float32),sigma=(1.23,1.16,1.08))
volume=blur>=.415
labels,num=ndi.label(volume,np.ones((3,3,3),dtype=np.uint8))
sizes=np.bincount(labels.ravel())[1:]
if len(sizes)==0:raise RuntimeError("No 3D body after constraints")
order=np.argsort(sizes)[::-1]
keep=labels==int(order[0]+1)
largest_fraction=float(keep.sum()/max(int(volume.sum()),1))
if largest_fraction<.53:
    raise RuntimeError(f"Multi view inconsistent: largest mesh only {largest_fraction:.1%}")
keep=ndi.binary_fill_holes(keep)

padding=3
padded=np.pad(keep.astype(np.float32),padding)
vertices,faces,_,_=marching_cubes(padded,.5,spacing=(dx,dy,dz),allow_degenerate=False)
vertices+=np.array([xmin-padding*dx,ymin-padding*dy,zmin-padding*dz])
mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
if mesh.volume<0:mesh.invert()
if not mesh.is_watertight or mesh.body_count!=1:
    raise RuntimeError("S 3-view surface not single watertight component")
before={"faces":len(mesh.faces),"vertices":len(mesh.vertices),"is_volume":bool(mesh.is_volume)}
simplify="NOT_ATTEMPTED"
try:
    if len(mesh.faces)>100000:
        t=mesh.simplify_quadric_decimation(face_count=100000,aggression=3)
        if t.volume<0:t.invert()
        if t.is_watertight and t.body_count==1 and t.is_volume:
            mesh=t
            simplify="ADOPTED_QEM"
        else:
            simplify="REJECT_QEM_TOPOLOGY"
except Exception as e:
    simplify=f"REJECT_QEM_EXCEPTION_{str(e)[:120]}"

path=OUT/"S-authority-visualhull-3view-v2.glb"
mesh.export(path)
def iou(a,b):
    return float(np.count_nonzero(a&b)/max(np.count_nonzero(a|b),1))
projection_side=keep.any(axis=0)
projection_front=keep.any(axis=1)
# 3/4 projected silhouette is evaluated by reducing occupancy per mapping coordinate.
# This is training data; use BACK view for independent held-out judgment.
report={
 "status":"MESH_CREATED_NEEDS_VISUAL_REVIEW",
 "source_image_sha256":SHA,
 "camera_inputs":["SIDE","FRONT","FRONT34"],
 "held_out_camera":"BACK",
 "axes":"x lateral, y forward negative, z vertical",
 "grid":[Nx,Ny,Nz],
 "base_two_view_voxels":base_n,
 "third_view_retained_voxels":trimmed_n,
 "third_view_retention_fraction":fraction,
 "connected_body_fraction":largest_fraction,
 "top_components_voxels":[int(sizes[i]) for i in order[:12]],
 "pre_simplification":before,
 "qem_result":simplify,
 "mesh_faces":len(mesh.faces),"mesh_vertices":len(mesh.vertices),
 "watertight":bool(mesh.is_watertight),"signed_volume_positive":bool(mesh.volume>0),
 "body_components":int(mesh.body_count),
 "train_side_iou":iou(projection_side,side2),
 "train_front_iou":iou(projection_front,front2),
 "mesh_glb":str(path.relative_to(ROOT)),
 "mesh_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
 "game_approved":False,"animation_approved":False,
 "note":"This is a visual hull from three artistic images; occluded geometry and material details remain undetermined."
}
(OUT/"THREE_VIEW_QA.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
