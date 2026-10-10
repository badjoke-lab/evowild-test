"""EvoWild S actual QEM-derived tail D — tapered swept cap experiment.

Begins with topology-PASS C .blend. Preserves exact original QEM donor and
all A/C objects; derives a separate D shape-key mesh. Identifies the original
three SEWN plate cap vertices (not detached meshes), draws their tips rearward,
and narrows trailing tips into laminae. Tests actual evaluated triangle quality.
No independent/proxy/pasted fin meshes. Design / motion remain unapproved.
"""
import bpy, numpy as np, hashlib, json
from mathutils import Vector
from mathutils.kdtree import KDTree
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"tail-tapered-d-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
DESIGN=ROOT/"references/00_s_type_modeling_image_v1.png"
DONOR=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(DESIGN.read_bytes()).hexdigest()=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(DONOR.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
trialA=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
trialC=bpy.data.objects["S_QEM_C_SEWN_INTEGRATED_PLATES_EXPERIMENT_NOT_APPROVED"]
assert len(src.data.vertices)==len(trialA.data.vertices)==29948
assert len(trialC.data.vertices)==30029
assert len(trialC.data.polygons)==60094
def sourceworld(obj):
    return np.asarray([obj.matrix_world@v.co for v in obj.data.vertices],dtype=np.float64)
s0=sourceworld(src)
srcsig=hashlib.sha256(s0.tobytes()).hexdigest()
# Compare against exact A evaluated shape-key positions.
bpy.context.scene.frame_set(1)
def evaluated(obj):
    bpy.context.view_layer.update()
    ob=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ob.to_mesh()
    try:
        return np.asarray([ob.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:ob.to_mesh_clear()
baseA=evaluated(trialA)
baseC=evaluated(trialC)
tree=KDTree(len(baseA))
for i,w in enumerate(baseA):
    tree.insert(Vector(w),i)
tree.balance()
cap_candidates=[]
for i,w in enumerate(baseC):
    _,_,dist=tree.find(Vector(w))
    if dist>.028:
        cap_candidates.append(i)
assert 45 <= len(cap_candidates) <= 140,("incorrect C plate-cap inference",len(cap_candidates))
y=baseC[:,1]
regions=[
 {"name":"ROOT","low":1.78,"high":2.08,"flare":-.025},
 {"name":"MID","low":2.08,"high":2.43,"flare":+.024},
 {"name":"TIP","low":2.43,"high":2.92,"flare":-.018},
]
groups=[]
for spec in regions:
    idx=np.asarray([i for i in cap_candidates if spec["low"]<=y[i]<spec["high"]],dtype=int)
    assert len(idx)>=8,(spec["name"],len(idx))
    groups.append(idx)
unassigned=set(cap_candidates)-set(int(v) for arr in groups for v in arr)
assert len(unassigned)<20,("too many unmatched cap vertices",len(unassigned))
# Deduct original closed-manifold base from this source C (0 bad edges already).
faces=np.asarray([tuple(f.vertices) for f in trialC.data.polygons],dtype=np.int32)
origtri=baseC[faces]
norm0=np.cross(origtri[:,1]-origtri[:,0],origtri[:,2]-origtri[:,0])
area0=np.linalg.norm(norm0,axis=1)
valid=area0>1.e-10
assert valid.sum()==len(faces)
dst=trialC.copy()
dst.data=trialC.data.copy()
dst.name="S_QEM_D_TAPERED_PLATES_DEFORM_TRIAL_NOT_APPROVED"
bpy.context.scene.collection.objects.link(dst)
dst.matrix_world=trialC.matrix_world.copy()
dst.shape_key_add(name="C_SEWN_PLATES_BASIS",from_mix=False)
key=dst.shape_key_add(name="D_TAPERED_LAMINA_PROFILE",from_mix=False)
key.value=1.
inv=dst.matrix_world.inverted()
def smooth(u):
    t=np.maximum(0.,np.minimum(1.,u))
    return t*t*(3.-2.*t)
def triQA(v):
    x=v[faces]
    n=np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0])
    length=np.linalg.norm(n,axis=1)
    area_ratio=np.divide(length,area0,out=np.ones_like(length),where=valid)
    return {
     "flips_vs_C":int(np.count_nonzero((np.sum(n*norm0,axis=1)<0)&valid)),
     "collapsed":int(np.count_nonzero((length<1.e-10)&valid)),
     "smaller_than_half_C_area":int(np.count_nonzero((area_ratio<.5)&valid)),
     "larger_than_twice_C_area":int(np.count_nonzero((area_ratio>2.)&valid)),
     "min_ratio":float(area_ratio[valid].min()),
     "max_ratio":float(area_ratio[valid].max())
    }

scans=[]
selected=None
for blade_growth in (.22,.17,.13,.09,.05):
    trial=baseC.copy()
    local=[]
    for spec,idx in zip(regions,groups):
        yvals=baseC[idx,1]
        lo,hi=float(np.min(yvals)),float(np.max(yvals))
        u=smooth((yvals-lo)/max(hi-lo,1.e-4))
        centerx=float(np.mean(baseC[idx,0]))
        # Rearward swept tapered lamina: tip extends and narrows, not a block.
        trial[idx,1]+=blade_growth*1.15*u
        trial[idx,2]+=blade_growth*.58*u
        trial[idx,0]=centerx+(baseC[idx,0]-centerx)*(1.-.65*u)+spec["flare"]*u
        local.append({
           "plate":spec["name"],"top_vertex_count":int(len(idx)),
           "source_y_range":[lo,hi],
           "max_growth_y":float(np.max(blade_growth*1.15*u)),
           "max_growth_z":float(np.max(blade_growth*.58*u)),
        })
    for i,w in enumerate(trial):
        key.data[i].co=inv@Vector(w)
    actual=evaluated(dst)
    qa=triQA(actual)
    drift=float(np.max(np.abs(actual-trial)))
    row={
      "blade_growth":blade_growth,
      "displacement_peak_world":float(np.linalg.norm(actual-baseC,axis=1).max()),
      "max_evaluation_difference":drift,
      "face_quality":qa,
      "plate_shapes":local,
      "topology_unchanged_from_manifold_C":True,
      "deformation_gate_PASS":all(qa[k]==0 for k in
        ("flips_vs_C","collapsed","smaller_than_half_C_area","larger_than_twice_C_area"))
    }
    scans.append(row)
    print("S_QEM_TAIL_D_SWEEP",json.dumps(row))
    if row["deformation_gate_PASS"]:
        selected=row
        break
if selected is None:
    selected=scans[-1]
    blade_growth=selected["blade_growth"]
    trial=baseC.copy()
    for spec,idx in zip(regions,groups):
        vals=baseC[idx,1]
        u=smooth((vals-vals.min())/max(vals.max()-vals.min(),1e-4))
        cx=baseC[idx,0].mean()
        trial[idx,1]+=blade_growth*1.15*u
        trial[idx,2]+=blade_growth*.58*u
        trial[idx,0]=cx+(baseC[idx,0]-cx)*(1.-.65*u)+spec["flare"]*u
    for i,w in enumerate(trial):key.data[i].co=inv@Vector(w)
assert triQA(evaluated(dst))==selected["face_quality"]
assert hashlib.sha256(sourceworld(src).tobytes()).hexdigest()==srcsig
assert len(trialC.data.vertices)==len(dst.data.vertices)==30029
assert len(trialC.data.polygons)==len(dst.data.polygons)==60094

qa={
 "authoritative_image_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
 "donor_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
 "original_source_preserved":True,
 "sewn_C_base_preserved":True,
 "original_mesh_vertices":29948,"original_mesh_faces":59932,
 "derived_C_and_D_vertices":30029,"derived_C_and_D_triangles":60094,
 "C_topology_manifold":"PASS_VERIFIED_C",
 "cap_vertex_candidates":len(cap_candidates),
 "cap_vertex_groups":[int(len(x)) for x in groups],
 "scan":scans,"selected":selected,
 "gate":"PASS_TAPERED_CAP_DEFORMATION_ONLY" if selected["deformation_gate_PASS"] else "FAIL_TAPERED_CAP_DEFORMATION",
 "authority_visual_gate":"NOT_APPROVED_PENDING_REAL_FIVE_VIEW",
 "self_intersection_check":"NOT_RUN",
 "new_skin_weights":"NOT_RUN",
 "game_approved":False
}
(OUT/"QEM_TAIL_TAPERED_D_QA.json").write_text(json.dumps(qa,indent=2)+"\n")
scene=bpy.context.scene
cam=scene.camera
assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.image_settings.file_format="PNG"
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
cam.data.type="ORTHO"
views={
 "SIDE":Vector((1,0,0)),
 "FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))
}
for tag,vec in views.items():
    look=Vector((0,0,1.275))
    cam.data.ortho_scale=5.65
    cam.location=look+vec*9
    cam.rotation_euler=(look-cam.location).to_track_quat("-Z","Y").to_euler()
    for which,ob in [("SEWN_C",trialC),("TAPERED_D",dst)]:
        for candidate in (src,trialA,trialC,dst):candidate.hide_render=candidate!=ob
        scene.render.filepath=str(REV/f"QEM_TAIL_{which}_{tag}.png")
        bpy.ops.render.render(write_still=True)
# These are actual close-ups so reviewers can inspect the 3-D plate geometry.
for tag,vec in (("SIDE",Vector((1,0,0))),("REAR34",Vector((1,1,0)).normalized())):
    look=Vector((0,2.14,1.64))
    cam.data.ortho_scale=1.65
    cam.location=look+vec*5
    cam.rotation_euler=(look-cam.location).to_track_quat("-Z","Y").to_euler()
    for which,ob in [("SEWN_C",trialC),("TAPERED_D",dst)]:
        for candidate in (src,trialA,trialC,dst):candidate.hide_render=candidate!=ob
        scene.render.filepath=str(REV/f"QEM_TAIL_CLOSE_{which}_{tag}.png")
        bpy.ops.render.render(write_still=True)
for obj in (src,trialA,trialC):obj.hide_render=True
dst.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-tail-tapered-laminae-D-TRIAL.blend"),compress=True)
print("QEM_TAIL_D_FINAL",qa["gate"],"candidates",qa["cap_vertex_candidates"],"selected",selected["blade_growth"])
