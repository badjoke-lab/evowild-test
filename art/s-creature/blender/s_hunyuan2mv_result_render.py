"""Actual Blender model import, 5 viewpoints, original reference locked.
Only runs when public Hunyuan2-mv inference returned a real GLB. Never
declares art/rig/gait accepted. Does not use screenshots as model geometry.
"""
import bpy,hashlib,json,math
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/hunyuan2mv-original-source-20261012"
REF=ROOT/"references/00_s_type_modeling_image_v1.png"
SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(REF.read_bytes()).hexdigest()==SHA
qa=json.loads((OUT/"ONE_PUBLIC_ZERO_GPU_REAL_SHAPE_ATTEMPT.json").read_text())
assert qa["generated"] and qa["candidate_file"].endswith(".glb")
G=OUT/qa["candidate_file"]
assert G.is_file() and hashlib.sha256(G.read_bytes()).hexdigest()==qa["candidate_sha256"]
REVIEW=OUT/"actual-blender-review";REVIEW.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
image=bpy.data.images.load(str(REF))
image.pack()
bpy.ops.import_scene.gltf(filepath=str(G))
mesh=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert mesh,("Space output was not real mesh")
assert sum(len(o.data.vertices) for o in mesh)>300
all_co=[o.matrix_world@v.co for o in mesh for v in o.data.vertices]
lo=Vector(tuple(min(v[i] for v in all_co) for i in range(3)))
hi=Vector(tuple(max(v[i] for v in all_co) for i in range(3)))
center=(lo+hi)*.5
dim=hi-lo
scene=bpy.context.scene
camdata=bpy.data.cameras.new("SOURCE_S_5VIEW_ASSET_PROOF_CAMERA")
cam=bpy.data.objects.new("SOURCE_S_5VIEW_ASSET_PROOF_CAMERA",camdata)
scene.collection.objects.link(cam)
scene.camera=cam
camdata.type="ORTHO";camdata.ortho_scale=max(dim)*1.30
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.show_cavity=True
scene.display.shading.show_shadows=True
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
views={"SIDE":(1,0,0),"FRONT":(0,-1,0),
       "FRONT34":(1,-1,0),"REAR34":(1,1,0),"BACK":(0,1,0)}
for name,d in views.items():
    direct=Vector(d).normalized()
    cam.location=center+direct*(max(dim)*2.5)
    cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str(REVIEW/("REAL_MV2_SOURCE_S_"+name+".png"))
    bpy.ops.render.render(write_still=True)
scene["A_SOURCE_MODEL_REFERENCE_LOCK_SHA256"]=SHA
scene["source_art_morphology_approved"]=False
scene["commercial_license_cleared"]=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"HUNYUAN2MV_S_THREEVIEW_REAL_ASSET_UNAPPROVED.blend"),compress=True)
f={
 "canonical_SHA256":SHA,
 "actual_external_generated_GLb_sha256":qa["candidate_sha256"],
 "original_meshes_imported":False,
 "new_GLb_mesh_objects":len(mesh),
 "actual_mesh_vertices":sum(len(o.data.vertices) for o in mesh),
 "actual_mesh_faces":sum(len(o.data.polygons) for o in mesh),
 "raw_world_dimensions_xyz":list(dim),
 "five_actual_Blender_views":list(views.keys()),
 "pose_alignment_calibrated":False,
 "geometry_art_match":"REVIEW_PENDING",
 "approved_S":"NO",
 "gait_rig_pass":False,
 "production_or_main":False
}
(OUT/"REAL_HUNYUAN2MV_S_BLENDER_AUDIT.json").write_text(json.dumps(f,indent=2)+"\n")
print("S_MULTIVIEW_REAL_ASSET_BLENDER_EVIDENCE",f)
