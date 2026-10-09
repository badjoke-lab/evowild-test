#!/usr/bin/env python3
"""Produce *real* EvoWild S multiview-constrained 3D visual hull.

Not a procedural animal made of tubes, and not texture transfer: exact binary
side/front silhouettes from the approved source are carved into a 3D voxel
volume. Back and 3/4 art are held out for visual evaluation.
This proves or disproves a geometry-constrained blockout, NOT final morphology.
"""
from pathlib import Path
import json, hashlib
import numpy as np, cv2, scipy.ndimage as ndi, trimesh
from skimage.measure import marching_cubes

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"art/s-creature/experiments/authority-visualhull"
OUT=BASE/"hull-v1"
OUT.mkdir(parents=True,exist_ok=True)

qa=json.loads((BASE/"SEGMENTATION_QA.json").read_text())
ref=BASE/"s-authority-unaltered.png"
source_sha=hashlib.sha256(ref.read_bytes()).hexdigest()
assert source_sha==qa["authority_sha256"]=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"

side=cv2.imread(str(BASE/"side_mask.png"),0)>127
front=cv2.imread(str(BASE/"front_mask.png"),0)>127
back=cv2.imread(str(BASE/"back_mask.png"),0)>127
assert side.any() and front.any() and back.any()

NX,NY,NZ=104,228,176
xmin,xmax=-.51,.51
ymin,ymax=-1.64,1.72
zmin,zmax=-.03,2.60
x=np.linspace(xmin,xmax,NX)
y=np.linspace(ymin,ymax,NY)
z=np.linspace(zmin,zmax,NZ)
dx,dy,dz=x[1]-x[0],y[1]-y[0],z[1]-z[0]

def get_sample(m, bbox, horiz, height):
    # pix ground is bbox lower, uppermost crest is bbox higher.
    xx=np.rint(bbox[0]+(horiz-horiz.min())/(horiz.max()-horiz.min())*(bbox[2]-bbox[0]-1)).astype(int)
    zz=np.rint(bbox[3]-1-(height-zmin)/(zmax-zmin)*(bbox[3]-bbox[1]-1)).astype(int)
    xx=np.clip(xx,0,m.shape[1]-1);zz=np.clip(zz,0,m.shape[0]-1)
    return m[zz[None,:],xx[:,None]]

# SIDE target y/z and FRONT target x/z.
side2=get_sample(side,qa["results"]["side"]["bbox_local"],y,z)
front2=get_sample(front,qa["results"]["front"]["bbox_local"],x,z)
volume=front2[:,None,:]&side2[None,:,:]
initial_voxels=int(volume.sum())
if initial_voxels<11000:raise RuntimeError(f"visual hull volume unexpectedly empty: {initial_voxels}")

# Smooth binary voxel stair-steps only; avoid inventing limbs or crest geometry.
scalar=ndi.gaussian_filter(volume.astype(np.float32),sigma=(.68,.72,.65))
smoothed=scalar>=.42
labels,n=ndi.label(smoothed,np.ones((3,3,3),dtype=np.uint8))
sizes=np.bincount(labels.ravel())[1:]
order=np.argsort(sizes)[::-1]
connected=[{"label":int(i+1),"voxels":int(sizes[i])} for i in order[:15]]
# Keep the physical main figure, never inadvertently bridge across blank space.
if not len(order):raise RuntimeError("No connected hull components")
largest=int(order[0]+1)
figure=(labels==largest)
kept_voxels=int(figure.sum())
fraction=kept_voxels/max(int(smoothed.sum()),1)
if fraction<.65:
    raise RuntimeError(f"Largest hull component only {fraction:.2%}; masks not safe")
figure=ndi.binary_fill_holes(figure)

# Make the correct surface truly closed by padding the binary array.
pad=3
field=np.pad(figure.astype(np.float32),pad,mode="constant")
vv,ff,_,_=marching_cubes(field,level=.5,spacing=(dx,dy,dz),allow_degenerate=False)
vv=vv+np.array([xmin-pad*dx,ymin-pad*dy,zmin-pad*dz])
mesh=trimesh.Trimesh(vertices=vv,faces=ff,process=True)
if not mesh.is_winding_consistent:mesh.fix_normals()
raw_summary={
  "vertices":len(mesh.vertices),"faces":len(mesh.faces),
  "body_count":int(mesh.body_count),
  "watertight":bool(mesh.is_watertight),
  "extents":mesh.extents.tolist(),
  "bounds":mesh.bounds.tolist()
}
# This mesh is the first actual shape-donor, not the final skinned creature.
# QEM decimation is limited to topology cleanup; no voxel rebuild from TRELLIS.
try:
    reduced=mesh.simplify_quadric_decimation(face_count=min(85000,len(mesh.faces)),aggression=3)
    if not reduced.is_watertight or reduced.body_count!=1:
        raise RuntimeError("QEM topology damage; keeping raw hull")
    mesh=reduced
    simplified=True
except Exception as exc:
    simplified=False
    raw_summary["qem_error"]=str(exc)

dest=OUT/"S-authority-visualhull-v1.glb"
mesh.export(dest)
# Objective agreement with input projections before Blender real-render review.
pred_side=figure.any(axis=0)  # y/z
pred_front=figure.any(axis=1) # x/z
def iou(a,b):
    return float(np.count_nonzero(a & b)/max(1,np.count_nonzero(a | b)))
metrics={
    "side_training_mask_iou":iou(pred_side,side2),
    "front_training_mask_iou":iou(pred_front,front2),
    "note":"Training 2D mask IOUs measure fitted projections, not visual quality or true 3D accuracy",
}
summary={
 "authority_sha256":source_sha,
 "source_masks":["side_mask.png","front_mask.png"],
 "held_out_views":["back_mask.png","front34_mask.png"],
 "axes":"Blender: X lateral, Y nose-to-tail, Z vertical",
 "grid":[NX,NY,NZ],
 "grid_range":{"x":[xmin,xmax],"y":[ymin,ymax],"z":[zmin,zmax]},
 "input_voxels":initial_voxels,
 "kept_voxels":kept_voxels,
 "main_component_fraction":fraction,
 "component_sizes":connected,
 "raw_hull":raw_summary,
 "decimated":simplified,
 "output_file":str(dest.relative_to(ROOT)),
 "output_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
 "output_bytes":dest.stat().st_size,
 "actual_mesh":{"vertices":len(mesh.vertices),"faces":len(mesh.faces),
                "watertight":bool(mesh.is_watertight),
                "winding_consistent":bool(mesh.is_winding_consistent),
                "body_count":int(mesh.body_count),
                "is_volume":bool(mesh.is_volume)},
 "metrics":metrics,
 "review":"UNAPPROVED_SILHOUETTE_CAGE; PENDING real five-view render and held-out view review",
 "skinning_approved":False,
 "production_approved":False,
}
(OUT/"HULL_QA.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:summary[k] for k in ("input_voxels","kept_voxels","main_component_fraction","raw_hull","decimated","actual_mesh","metrics","output_bytes")},indent=2))
