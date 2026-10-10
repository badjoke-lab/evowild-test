"""EvoWild S original-QEM torso silhouette trial A.

Isolated deformation-only shape key on a REAL donor clone: reduce artificial
dorsal hump near central rear body, extend central abdominal volume modestly.
No new parts, no original source edits, no skeleton/rig or game approval.
Authoritative S image SHA and original donor GLB SHA locked.
"""
import bpy, numpy as np, json, hashlib
from mathutils import Vector
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"torso-profile-b-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(ref.read_bytes()).hexdigest()=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(donor.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
scene=bpy.context.scene
scene.frame_set(1)
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
assert src.type=="MESH"
assert len(src.data.vertices)==29948 and len(src.data.polygons)==59932
source=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
source_sig=hashlib.sha256(source.tobytes()).hexdigest()
faces=np.asarray([tuple(f.vertices) for f in src.data.polygons],dtype=np.int32)
orig=source[faces]
norm0=np.cross(orig[:,1]-orig[:,0],orig[:,2]-orig[:,0])
area0=np.linalg.norm(norm0,axis=1)
valid=area0>1e-10
dst=src.copy()
dst.data=src.data.copy()
dst.name="S_QEM_TORSO_PROFILE_B_NOT_APPROVED"
scene.collection.objects.link(dst)
dst.matrix_world=src.matrix_world.copy()
dst.shape_key_add(name="DONOR_BASIS",from_mix=False)
key=dst.shape_key_add(name="ISOLATED_DORSAL_TOPLINE_B_NO_CREST",from_mix=False)
key.value=1.
inverse=src.matrix_world.inverted()
x=source[:,0]
y=source[:,1]
z=source[:,2]

def smooth(t):
    q=np.maximum(0.,np.minimum(1.,t))
    return q*q*(3.-2.*q)
# Critical A correction: original long crest sweeps back over the dorsal
# body and occupies the previous z>2.1 region. A accidentally deformed crest
# tips. B restricts ONLY lower torso dorsal sheet (z1.6–2.12), and explicitly
# retains every vertex over z=2.20 and every head/leg vertex.
peak=smooth((y+.12)/.57)*(1.-smooth((y-.70)/.52))
peak*=smooth((z-1.52)/.20)*(1.-smooth((z-1.98)/.18))
peak*=1.-smooth((np.abs(x)-.20)/.20)
belly=np.zeros_like(peak)  # Isolate topline; A belly/width caused quality fail.
width=np.zeros_like(peak)
assert int(np.count_nonzero(peak>.02))>200
assert int(np.count_nonzero(belly>.02))>100

def evaluated():
    bpy.context.view_layer.update()
    obj=dst.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=obj.to_mesh()
    try:
        return np.asarray([obj.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:obj.to_mesh_clear()

def facesqa(v):
    t=v[faces]
    n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
    lens=np.linalg.norm(n,axis=1)
    ratios=np.divide(lens,area0,out=np.ones_like(lens),where=valid)
    return {
      "face_flipped":int(np.count_nonzero((np.sum(n*norm0,axis=1)<0)&valid)),
      "face_collapsed":int(np.count_nonzero((lens<1.e-10)&valid)),
      "area_less_half":int(np.count_nonzero((ratios<.5)&valid)),
      "area_more_double":int(np.count_nonzero((ratios>2.)&valid)),
      "min_ratio":float(ratios[valid].min()),
      "max_ratio":float(ratios[valid].max())
    }

scans=[]
selected=None
for back_shift in (.22,.18,.14,.10,.06):
    v=source.copy()
    v[:,2]-=back_shift*peak
    v[:,2]-=.0*belly
    v[:,0]+=np.sign(x)*.0*width
    for i,w in enumerate(v):
        key.data[i].co=inverse@Vector(w)
    actual=evaluated()
    qa=facesqa(actual)
    err=float(np.max(np.abs(v-actual)))
    crest_freeze_error=float(np.max(np.abs(actual[source[:,2]>2.20] - source[source[:,2]>2.20])))
    foot_freeze_error=float(np.max(np.abs(actual[source[:,2]<.70] - source[source[:,2]<.70])))
    assert crest_freeze_error<1.e-5 and foot_freeze_error<1.e-5,(crest_freeze_error,foot_freeze_error)

    changed=int(np.count_nonzero(np.linalg.norm(actual-source,axis=1)>1e-5))
    # Explicit silhouette ROI limited to main body without crest and hindleg.
    roi=(y>.10)&(y<.9)&(z>1.60)&(z<2.18)&(np.abs(x)<.29)
    before=float(source[roi,2].max())
    after=float(actual[roi,2].max())
    row={
      "peak_amplitude":back_shift,
      "belly_lowering_max":0.,
      "width_increase_max":0.,
      "affected_vertices":changed,
      "source_peak_ROI_zmax":before,
      "derived_peak_ROI_zmax":after,
      "source_vs_variant_world_error":err,
      "crest_freeze_max_error":crest_freeze_error,
      "foot_freeze_max_error":foot_freeze_error,
      "face_quality":qa,
      "local_skin_quality_PASS":all(qa[k]==0 for k in
          ("face_flipped","face_collapsed","area_less_half","area_more_double"))
    }
    scans.append(row)
    print("QEM_TORSO_B_SCAN",json.dumps(row))
    if row["local_skin_quality_PASS"]:
        selected=row
        break
if selected is None:
    selected=scans[-1]
    a=selected["peak_amplitude"]
    v=source.copy()
    v[:,2]-=a*peak
    v[:,2]-=.0*belly
    v[:,0]+=np.sign(x)*.0*width
    for i,w in enumerate(v):key.data[i].co=inverse@Vector(w)
assert facesqa(evaluated())==selected["face_quality"]
assert hashlib.sha256(np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64).tobytes()).hexdigest()==source_sig
assert len(dst.data.vertices)==29948 and len(dst.data.polygons)==59932

report={
 "authority_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
 "donor_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
 "original_source_unchanged":True,
 "source_mesh_vertices":29948,"source_triangles":59932,
 "variant_mesh_vertices":29948,"variant_triangles":59932,
 "target_regions":["central rear dorsal topline only, strictly excluding long crest and foot regions"],
 "topline_vertices_with_weight":int(np.count_nonzero(peak>.02)),
 "abdomen_vertices_with_weight":int(np.count_nonzero(belly>.02)),
 "candidates":scans,
 "selected":selected,
 "geometry_gate":"PASS_LIMITED_ORIGINAL_TRIANGLE_DEFORMATION" if selected["local_skin_quality_PASS"] else "FAIL_TRIANGLE_DEFORMATION",
 "S_visual_design_gate":"REVIEW_REQUIRED_NOT_APPROVED",
 "rig_revalidated_after_change":False,
 "fully_running_race_gait":False,
 "approved_for_game":False
}
(OUT/"QEM_TORSO_B_QA.json").write_text(json.dumps(report,indent=2)+"\n")
cam=scene.camera
assert cam and cam.type=="CAMERA"
cam.data.type="ORTHO"
cam.data.ortho_scale=5.3
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
focus=Vector((0,0,1.275))
views={
 "SIDE":Vector((1,0,0)),
 "FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))
}
for tag,dr in views.items():
    cam.location=focus+dr*9
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    src.hide_render=False
    dst.hide_render=True
    bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"].hide_render=True
    scene.render.filepath=str(REV/f"S_QEM_REAL_SOURCE_{tag}.png")
    bpy.ops.render.render(write_still=True)
    src.hide_render=True
    dst.hide_render=False
    scene.render.filepath=str(REV/f"S_QEM_REAL_TORSO_{tag}.png")
    bpy.ops.render.render(write_still=True)
src.hide_render=True
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-real-torso-profile-B-TRIAL.blend"),compress=True)
print("QEM_TORSO_B_FINAL",report["geometry_gate"],"peak",selected["peak_amplitude"],
      "affected",selected["affected_vertices"],"faces",selected["face_quality"])
