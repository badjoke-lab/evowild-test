"""Locate actual original-QEM torso deformation failure face IDs; no edit to donor.

Loads REAL Torso B .blend. Scans lower amplitudes 0.06 down to .002 via
existing shape-key value. All measurements are Blender evaluated triangle
world coordinates. Saves raw QA, views and new experimental .blend only.
"""
from pathlib import Path
import bpy, numpy as np, json, hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"torso-face-audit-20261011"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
DESIGN=ROOT/"references/00_s_type_modeling_image_v1.png"
DONOR=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(DESIGN.read_bytes()).hexdigest()=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(DONOR.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
trial=bpy.data.objects["S_QEM_TORSO_PROFILE_B_NOT_APPROVED"]
scene=bpy.context.scene
assert len(src.data.vertices)==len(trial.data.vertices)==29948
assert len(src.data.polygons)==len(trial.data.polygons)==59932
scene.frame_set(1)
def evaluated(ob):
    bpy.context.view_layer.update()
    o=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=o.to_mesh()
    try:return np.asarray([o.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:o.to_mesh_clear()
source=evaluated(src)
source_sig=hashlib.sha256(source.tobytes()).hexdigest()
tris=np.asarray([tuple(f.vertices) for f in src.data.polygons],dtype=np.int32)
p=source[tris]
n0=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0])
lens0=np.linalg.norm(n0,axis=1)
valid=lens0>1e-10
key=trial.data.shape_keys.key_blocks.get("ISOLATED_DORSAL_TOPLINE_B_NO_CREST")
assert key is not None,key
scan=[]
for amp in (.060,.050,.045,.040,.035,.030,.025,.020,.015,.010,.0075,.005,.002):
    key.value=amp/.06
    v=evaluated(trial)
    face=v[tris]
    n=np.cross(face[:,1]-face[:,0],face[:,2]-face[:,0])
    ln=np.linalg.norm(n,axis=1)
    ratio=np.divide(ln,lens0,out=np.ones_like(ln),where=valid)
    flip=np.flatnonzero((np.sum(n*n0,axis=1)<0)&valid)
    shrink=np.flatnonzero((ratio<.5)&valid)
    expand=np.flatnonzero((ratio>2)&valid)
    bad=sorted(set(map(int,np.concatenate((flip,shrink,expand)))))
    offenders=[]
    for k in bad[:60]:
        original_triangle=source[tris[k]]
        current_triangle=v[tris[k]]
        offenders.append({
          "polygon_id":int(k),
          "vertex_ids":[int(x) for x in tris[k]],
          "source_centroid_world":np.mean(original_triangle,axis=0).tolist(),
          "current_centroid_world":np.mean(current_triangle,axis=0).tolist(),
          "source_vertices_world":original_triangle.tolist(),
          "new_vertices_world":current_triangle.tolist(),
          "source_double_area":float(lens0[k]),
          "current_double_area":float(ln[k]),
          "area_ratio":float(ratio[k]),
          "inverted":bool(k in flip),
          "edge_lengths_source":[float(np.linalg.norm(original_triangle[(i+1)%3]-original_triangle[i])) for i in range(3)],
          "vertex_group_names":[[
              trial.vertex_groups[g.group].name for g in trial.data.vertices[int(idx)].groups
              if g.group<len(trial.vertex_groups)
          ] for idx in tris[k]]
        })
    row={
      "amplitude":amp,
      "key_value":float(key.value),
      "inverted_face_count":len(flip),
      "under_half_area_count":len(shrink),
      "over_twice_area_count":len(expand),
      "bad_face_ids":bad,
      "worst_area_ratio":float(ratio[valid].min()),
      "max_area_ratio":float(ratio[valid].max()),
      "offenders":offenders,
      "affected_vertices":int(np.count_nonzero(np.linalg.norm(v-source,axis=1)>1.e-5)),
      "crest_frozen_max_error":float(np.max(np.linalg.norm(v[source[:,2]>2.20]-source[source[:,2]>2.20],axis=1))),
      "feet_frozen_max_error":float(np.max(np.linalg.norm(v[source[:,2]<.70]-source[source[:,2]<.70],axis=1))),
      "gate":"PASS_TRIANGLE_ONLY" if not bad else "FAIL_TRIANGLE",
    }
    scan.append(row)
    print("QEM_TORSO_FACE_ID_DIAGNOSTIC",amp,row["gate"],
          "badids",bad[:12],"under",len(shrink),"flips",len(flip))
passing=[x for x in scan if x["gate"]=="PASS_TRIANGLE_ONLY"]
selected=passing[0] if passing else scan[-1]
key.value=selected["key_value"]
original_after=evaluated(src)
assert hashlib.sha256(original_after.tobytes()).hexdigest()==source_sig
report={
  "reference_png_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
  "original_glb_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
  "source_unchanged":True,"original_vertices":29948,"original_triangles":59932,
  "inspected":len(scan),"scan":scan,"selected":selected,
  "any_pass":bool(passing),
  "max_passing_tested_amplitude":selected["amplitude"] if passing else None,
  "mechanical_joint_quality":"NOT_TESTED",
  "visual_morphology_gate":"REVIEW_PENDING_NOT_APPROVED",
  "production_approved":False
}
(OUT/"TORSO_FACE_ID_LOCALIZATION.json").write_text(json.dumps(report,indent=2)+"\n")
cam=scene.camera
assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.image_settings.file_format="PNG"
scene.render.resolution_x=860
scene.render.resolution_y=645
scene.render.resolution_percentage=100
cam.data.type="ORTHO"
cam.data.ortho_scale=5.3
focus=Vector((0,0,1.275))
views={
  "SIDE":Vector((1,0,0)),
  "FRONT":Vector((0,-1,0)),
  "FRONT34":Vector((1,-1,0)).normalized(),
  "REAR34":Vector((1,1,0)).normalized(),
  "BACK":Vector((0,1,0))
}
trialA=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
for view,vec in views.items():
    cam.location=focus+vec*9
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    for part,obj in (("SOURCE",src),("SELECTED",trial)):
        for other in (src,trialA,trial):other.hide_render=other!=obj
        scene.render.filepath=str(REV/f"QEM_TORSO_FACE_{part}_{view}.png")
        bpy.ops.render.render(write_still=True)
for obj in (src,trialA):obj.hide_render=True
trial.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-torso-face-audit-TRIAL.blend"),compress=True)
print("QEM_TORSO_FACE_ID_FINAL",selected["gate"],selected["amplitude"],
      "bad_ids",selected["bad_face_ids"][:15],"pass_candidates",len(passing))
