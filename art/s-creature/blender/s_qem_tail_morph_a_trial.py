"""EvoWild S: non-destructive REAL QEM tail morphology hypothesis A.

The authentic reference has a long swept segmented tail, but the original QEM
has a short pointed stub. Test only whether lengthening EXISTING tail vertices
is topologically safe. Does not synthesize fins, approve design, touch source,
change topology, or claim a full race model. The design gate remains REJECT
until actual 5-view visual approval against hash-locked authority PNG.
"""
from pathlib import Path
import bpy, math, json, hashlib
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"tail-morph-a-v1"
REVIEW=OUT/"review"
REVIEW.mkdir(parents=True,exist_ok=True)
SOURCE_PATH=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
DESIGN=ROOT/"references/00_s_type_modeling_image_v1.png"
assert hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(DESIGN.read_bytes()).hexdigest()=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
srcs=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(srcs)==1,[(o.name,o.type) for o in srcs]
src=srcs[0]
src.name="QEM_IMMUTABLE_DONOR"
assert len(src.data.vertices)==29948 and len(src.data.polygons)==59932
world=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
tri=np.asarray([tuple(f.vertices) for f in src.data.polygons],dtype=np.int32)
start_sig=hashlib.sha256(world.tobytes()).hexdigest()
start_tri=world[tri]
start_norm=np.cross(start_tri[:,1]-start_tri[:,0],start_tri[:,2]-start_tri[:,0])
start_area=np.linalg.norm(start_norm,axis=1)
valid=start_area>1e-10
assert valid.sum()>59000

dst=src.copy()
dst.data=src.data.copy()
dst.name="S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"
bpy.context.scene.collection.objects.link(dst)
dst.matrix_world=src.matrix_world.copy()
dst.shape_key_add(name="SOURCE_GEOMETRY_BASIS",from_mix=False)
key=dst.shape_key_add(name="TAIL_STUB_LENGTH_EXPERIMENT",from_mix=False)
key.value=1.0
inverse_rot=src.matrix_world.inverted().to_3x3()

def smooth(t):
    x=np.maximum(0.,np.minimum(1.,t))
    return x*x*(3-2*x)

# Posterior = positive Y. At +Y 2.2 most OTHER mesh is low hind-foot
# vertices (z<0.5). The slim elevated (z>1.35, |x| small) spur is
# the tail. Fade around the rump rather than displacing entire haunches.
y=world[:,1];z=world[:,2];x=np.abs(world[:,0])
tail_y=smooth((y-1.46)/.75)
tail_z=smooth((z-1.19)/.34)
tail_x=1.-smooth((x-.16)/.22)
strength=tail_y*tail_z*tail_x
region=np.flatnonzero(strength>.002)
tip=np.flatnonzero((y>1.80)&(z>1.43)&(x<.34))
assert len(region)>=30,("no stable original tail region",len(region))
assert len(tip)>=12,("tail-tip original vertices missing",len(tip))

def evaluated():
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    obj=dst.evaluated_get(deps)
    mesh=obj.to_mesh()
    try:
        return np.asarray([obj.matrix_world @ v.co for v in mesh.vertices],dtype=np.float64)
    finally:obj.to_mesh_clear()

def face_qa(a):
    faces=a[tri]
    n=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
    length=np.linalg.norm(n,axis=1)
    ratio=np.divide(length,start_area,out=np.ones_like(length),where=valid)
    return {
        "flipped":int(np.count_nonzero((np.sum(n*start_norm,axis=1)<0)&valid)),
        "collapsed":int(np.count_nonzero((length<1e-10)&valid)),
        "area_lt_half":int(np.count_nonzero((ratio<.5)&valid)),
        "area_gt_double":int(np.count_nonzero((ratio>2.)&valid)),
        "min_ratio":float(ratio[valid].min()),
        "max_ratio":float(ratio[valid].max()),
    }

original_tail_end=float(y[tip].max())
scan=[]
chosen=None
for extend in (.56,.40,.28,.16):
    # Preserve original topological connectivity and rest vertex order.
    candidate=world.copy()
    candidate[:,1]+=extend*strength
    # Small downward sweep on DISTAL upper tail only, not a pasted/new fin.
    candidate[:,2]-=.07*strength
    for i,w in enumerate(candidate):
        key.data[i].co=inverse_rot @ Vector(w-src.matrix_world.translation)
    bpy.context.view_layer.update()
    vv=evaluated()
    qa=face_qa(vv)
    maxpos=float(np.max(np.abs(vv-candidate)))
    selected_actual=vv[tip]
    length_change=float(selected_actual[:,1].max()-original_tail_end)
    row={
       "requested_extension":extend,
       "observed_tail_tip_gain_y":length_change,
       "modified_vertices":int(np.count_nonzero(np.linalg.norm(vv-world,axis=1)>1e-5)),
       "strong_influence_vertices":int(np.count_nonzero(strength>.5)),
       "max_coordinate_consistency_error":maxpos,
       "face_quality":qa,
       "topology_safe":all(qa[k]==0 for k in
                          ("flipped","collapsed","area_lt_half","area_gt_double")),
    }
    scan.append(row)
    print("TAIL_MORPH_A_SCAN",json.dumps(row))
    if row["topology_safe"]:
        chosen=row
        break
# The best evidence includes an actual deformation even if no QA candidate
# passes; do not silently replace it with a safe fake.
if chosen is None:
    selected=scan[-1]
else:selected=chosen
if selected["requested_extension"]!=scan[-1]["requested_extension"] and chosen is None:
    raise AssertionError("impossible")
if chosen is None:
    extend=scan[-1]["requested_extension"]
    candidate=world.copy()
    candidate[:,1]+=extend*strength
    candidate[:,2]-=.07*strength
    for i,w in enumerate(candidate):
        key.data[i].co=inverse_rot @ Vector(w-src.matrix_world.translation)
bpy.context.view_layer.update()
factual=face_qa(evaluated())
assert factual==selected["face_quality"]

still=np.asarray([src.matrix_world@v.co for v in src.data.vertices],dtype=np.float64)
assert hashlib.sha256(still.tobytes()).hexdigest()==start_sig
assert len(src.data.vertices)==len(dst.data.vertices)==29948
assert len(src.data.polygons)==len(dst.data.polygons)==59932

scene=bpy.context.scene
camera=scene.camera
assert camera and camera.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
camera.data.type="ORTHO"
camera.data.ortho_scale=5.6
center=Vector((0,0,1.275))
views={
 "SIDE":Vector((1,0,0)),
 "FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))
}
for view,d in views.items():
    camera.location=center+d*9
    camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
    src.hide_render=False
    dst.hide_render=True
    scene.render.filepath=str(REVIEW/f"REAL_QEM_A_SOURCE_{view}.png")
    bpy.ops.render.render(write_still=True)
    src.hide_render=True
    dst.hide_render=False
    scene.render.filepath=str(REVIEW/f"REAL_QEM_A_TAIL_TRIAL_{view}.png")
    bpy.ops.render.render(write_still=True)

scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-real-tail-morph-a-v1.blend"),compress=True)
report={
  "variant":"local tail-length shape-key A only",
  "original_glb_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
  "reference_png_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
  "source_unchanged":True,
  "original_mesh_vertex_count":29948,
  "variant_mesh_vertex_count":29948,
  "original_triangles":59932,
  "variant_triangles":59932,
  "changed_region_vertices":int(len(region)),
  "original_tail_tip_y":original_tail_end,
  "sweep":"posterior Y lengthening and slight distal vertical taper only",
  "candidate_scan":scan,
  "selected":selected,
  "geometry_gate":"PASS_LOCAL_SHAPE_KEY_TRIANGLES" if selected["topology_safe"] else "FAIL_LOCAL_SHAPE_KEY_TRIANGLES",
  "reference_shape_gate":"NOT_APPROVED_VISUAL_REVIEW_PENDING",
  "full_tail_segmented":False,
  "motion_rig_validated_for_changed_shape":False,
  "game_production_approved":False,
  "note":"This is an original-QEM tail-local edit trial, not an approved S-type silhouette or substitute asset. Original donor retained."
}
(OUT/"TAIL_MORPH_A_GEOMETRY_QA.json").write_text(json.dumps(report,indent=2)+"\n")
print("QEM_TAIL_MORPH_A_RESULT",report["geometry_gate"],"selected",selected,"design",report["reference_shape_gate"])
