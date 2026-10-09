"""Real Blender five-angle verification of the image-constrained S mesh."""
import bpy,json
from pathlib import Path
from mathutils import Vector

ROOT=Path(bpy.path.abspath("//")).resolve()
BASE=ROOT/"art/s-creature/experiments/authority-visualhull/hull-v1"
SOURCE=BASE/"S-authority-visualhull-v1.glb"
OUT=BASE/"review";OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if not meshes:raise RuntimeError("GLB did not contain renderable actual mesh")
mat=bpy.data.materials.new("S_visual_hull_actual_geometry")
mat.diffuse_color=(.66,.69,.73,1)
for ob in meshes:
    ob.data.materials.clear();ob.data.materials.append(mat)
scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type="BOTH"
scene.render.resolution_x=800;scene.render.resolution_y=800
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.world.color=(.05,.06,.07)

p=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
lo=Vector([min(q[i] for q in p) for i in range(3)])
hi=Vector([max(q[i] for q in p) for i in range(3)])
ctr=(lo+hi)*.5; ext=hi-lo
# Explicitly fail if glTF axis transform swapped this design unexpectedly.
assert ext.y>ext.x and ext.z>ext.x, f"Unexpected hull up-axis: extents={ext}"
camdata=bpy.data.cameras.new("S_AUTHORITATIVE_FIVE_VIEWS")
cam=bpy.data.objects.new("S_AUTHORITATIVE_FIVE_VIEWS",camdata)
scene.collection.objects.link(cam);scene.camera=cam;camdata.type="ORTHO"
views={
    "side":Vector((1,0,0)),
    "front":Vector((0,-1,0)),
    "front34":Vector((1,-1,0)).normalized(),
    "rear34":Vector((1,1,0)).normalized(),
    "back":Vector((0,1,0))
}
for name,d in views.items():
    cam.location=ctr+d*7
    cam.rotation_euler=((ctr-cam.location).to_track_quat("-Z","Y")).to_euler()
    right=Vector((-d.y,d.x,0)).normalized()
    projection=[(q-ctr).dot(right) for q in p]
    camdata.ortho_scale=max(max(projection)-min(projection),ext.z)*1.18
    scene.render.filepath=str(OUT/f"S_visualhull_v1_{name}.png")
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/"S-authority-visualhull-v1.blend"))
(OUT/"BLENDER_RENDER_QA.json").write_text(json.dumps({
  "model":str(SOURCE.relative_to(ROOT)), "mesh_objects":len(meshes),
  "extents_xyz":list(ext),"bounding_box":[list(lo),list(hi)],
  "render_views":list(views),"lighting":"BLENDER_WORKBENCH",
  "morphology_approved":False},indent=2)+"\n")
print("RENDER_DONE",list(ext))
