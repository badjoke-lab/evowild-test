"""Render ACTUAL 3D source-view-carved volumetric QEM-free S surface in Blender.

A true single physical triangle mesh, not a plane/card/sprite. Exact original
S source PNG must be packed. Gallery/GLB are independent editable geometry.
Pending/art-studio visual gate is mandatory. Cannot be gameplay or final S.
"""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/multiview-visual-hull-v0"
REVIEW=OUT/"review";REVIEW.mkdir(parents=True,exist_ok=True)
R="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
REF=ROOT/"references/00_s_type_modeling_image_v1.png"
assert hashlib.sha256(REF.read_bytes()).hexdigest()==R
data=json.loads((OUT/"REAL_SOURCE_MULTIVIEW_VOLUME_V0_QA.json").read_text())
assert data["original_QEM_TRELLIS_R0_R5_A0_meshes_imported"] is False
assert data["actual_mesh_3d_vertices"]>2000
assert not data["production_asset"]
bpy.ops.wm.read_factory_settings(use_empty=True)
im=bpy.data.images.load(str(REF),check_existing=True)
im.pack()
im.name="IMMUTABLE_S_USER_APPROVED_ORIGINAL_00"
scene=bpy.context.scene
scene["user_authorized_original_S_reference"]=R
scene["original_reference_packed"]=im.packed_file is not None
scene["technical_source_carved_visual_hull_only"]=True
scene["canonical_S_morphology_approved"]=False
scene["not_flat_image"]=True
scene["prior_QEM_R0_R5_A0_imported"]=False
file=OUT/"S-SOURCE-SIDE-FRONT-BACK-REAL-VOLUME-V0-NOT-APPROVED.obj"
verts=[];tris=[]
with file.open() as f:
    for line in f:
        if line.startswith("v "):
            vals=line.strip().split()
            verts.append(tuple(map(float,vals[1:4])))
        elif line.startswith("f "):
            vals=line.strip().split()
            tris.append(tuple(int(v)-1 for v in vals[1:4]))
assert len(verts)==data["actual_mesh_3d_vertices"]
assert len(tris)==data["actual_mesh_triangles"]
mesh=bpy.data.meshes.new("ACTUAL_REFERENCE_VOXEL_CARVED_3D_GEOMETRY")
mesh.from_pydata(verts,[],tris)
mesh.update()
obj=bpy.data.objects.new("SOURCE_ALIGNED_S_TRUE_VOLUME_V0_UNAPPROVED",mesh)
scene.collection.objects.link(obj)
for pol in obj.data.polygons:pol.use_smooth=True
mat=bpy.data.materials.new("NEUTRAL_DARK_NAVY_TO_JUDGE_3D_SILHOUETTE")
mat.diffuse_color=(.11,.18,.30,1.)
obj.data.materials.append(mat)
camera_data=bpy.data.cameras.new("Real_3D_Five_View_Orthographic")
cam=bpy.data.objects.new("Real_3D_Five_View_Camera",camera_data)
scene.collection.objects.link(cam)
scene.camera=cam
camera_data.type="ORTHO"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.light="STUDIO"
scene.display.shading.show_cavity=True
scene.display.shading.show_shadows=True
scene.render.image_settings.file_format="PNG"
scene.render.resolution_x=1280
scene.render.resolution_y=960
scene.render.resolution_percentage=100
focus=Vector((0,.64,1.91))
for name,direction in {
    "SIDE":Vector((1,0,0)),
    "FRONT":Vector((0,-1,0)),
    "FRONT34":Vector((1,-1,0)).normalized(),
    "REAR34":Vector((1,1,0)).normalized(),
    "BACK":Vector((0,1,0)),
}.items():
    cam.location=focus+direction*13
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    camera_data.ortho_scale=7.5
    scene.render.filepath=str(REVIEW/("REAL_SOURCE_VOLUME_V0_"+name+".png"))
    bpy.ops.render.render(write_still=True)
outblend=OUT/"S-ORIGINAL-SOURCE-3VIEW-VOLUME-V0-UNAPPROVED.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(outblend),compress=True)
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active=obj
bpy.ops.export_scene.gltf(filepath=str(OUT/"S-ORIGINAL-SOURCE-3VIEW-VOLUME-V0-UNAPPROVED.glb"),
   export_format="GLB",use_selection=True,export_apply=True)
print("S_TRUE_SOURCE_DRIVEN_3D",len(verts),len(tris),
      "rendered actual Blender complete",True,
      "source morph approved",False)
