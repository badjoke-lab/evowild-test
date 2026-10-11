"""EvoWild S actual QEM anatomy ROI survey against immutable canonical PNG.
Blender-only numerical survey of source M's chest/shoulder/hip/thorax.
No modeling, no output art that could be elevated into a new reference.
"""
import bpy, numpy as np, json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"body-authority-survey-20261011"
OUT.mkdir(parents=True,exist_ok=True)
REF=ROOT/"references/00_s_type_modeling_image_v1.png"
DONOR=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
R="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
D="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(REF.read_bytes()).hexdigest()==R
assert hashlib.sha256(DONOR.read_bytes()).hexdigest()==D
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
m=bpy.data.objects["S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"]
assert len(src.data.vertices)==29948 and len(src.data.polygons)==59932
assert len(m.data.vertices)==31948 and len(m.data.polygons)==63932
bpy.context.scene.frame_set(1)
def points(obj):
    bpy.context.view_layer.update()
    e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=e.to_mesh()
    try:return np.array([e.matrix_world@v.co for v in me.vertices],dtype=np.float64)
    finally:e.to_mesh_clear()
p=points(m);don=points(src)
bins=[]
for y in np.arange(-2.7,2.01,.15):
    a=p[np.abs(p[:,1]-y)<.075]
    if len(a)<10:continue
    bins.append({"y":round(float(y),3),"vertices":len(a),
      "X_05_50_95":np.percentile(a[:,0],[5,50,95]).round(5).tolist(),
      "Z_05_25_50_75_95":np.percentile(a[:,2],[5,25,50,75,95]).round(5).tolist(),
      "world_xyz_min":a.min(axis=0).round(5).tolist(),
      "world_xyz_max":a.max(axis=0).round(5).tolist()})
# For shoulders and hip, use only high axial cross-section to exclude
# dangling legs/feet and sample native donor body-skin thickness.
roi={}
for tag,y0,y1,z0,z1 in [
    ("SHOULDER_ROOT",-1.35,-.65,1.03,2.05),
    ("CHEST_TORSO",-1.15,-.20,1.1,2.0),
    ("UPPER_BACK",-.50,.60,1.35,2.25),
    ("HINDQUARTER",.35,1.35,1.1,2.25),
    ("WAIST",-.05,.65,1.1,2.05),
    ("HEAD_CREATURE",-2.70,-1.35,.95,2.5)]:
    a=p[(p[:,1]>y0)&(p[:,1]<y1)&(p[:,2]>z0)&(p[:,2]<z1)]
    roi[tag]={"bounds_yz":[y0,y1,z0,z1],"count":len(a)}
    if len(a)>20:
        roi[tag]["xyz_10pct"]=np.percentile(a,10,axis=0).round(5).tolist()
        roi[tag]["xyz_50pct"]=np.percentile(a,50,axis=0).round(5).tolist()
        roi[tag]["xyz_90pct"]=np.percentile(a,90,axis=0).round(5).tolist()
        roi[tag]["xmin_xmax"]=[round(float(a[:,0].min()),5),round(float(a[:,0].max()),5)]
        roi[tag]["zmin_zmax"]=[round(float(a[:,2].min()),5),round(float(a[:,2].max()),5)]
report={"authority_reference_png_sha256":R,"immutable_QEM_donor_sha256":D,
        "source_QEM_not_edited":True,
        "survey_derived_M_no_modifications":True,
        "M_evaluated_vertices":len(p),
        "global_bounds":[p.min(axis=0).round(6).tolist(),p.max(axis=0).round(6).tolist()],
        "per_Y_cross_sections":bins,"proposed_anatomy_ROIs":roi,
        "approved_reference_replaced":False,
        "production_S_morphology_approved":False}
(OUT/"ORIGINAL_QEM_S_BODY_REAL_COORDINATE_SURVEY.json").write_text(json.dumps(report,indent=2)+"\n")
print("BODY_SURVEY_REAL_QEM_BOUNDS",report["global_bounds"])
for k,v in roi.items():print("BODY_SURVEY_ROI",k,json.dumps(v))
