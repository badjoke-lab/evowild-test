"""Fix the real GLB orientation after detecting glTF Z-up/Y-up mismatch.

This is an isolated corrected-asset run, NOT a visual redesign.
"""
from pathlib import Path
from math import pi
import json,bpy,bmesh
from mathutils import Vector,Matrix

ROOT=Path(bpy.path.abspath("//")).resolve()
BASE=ROOT/"art/s-creature/experiments/authority-visualhull/hull-v1"
SOURCE=BASE/"S-authority-visualhull-v1.glb"
OUT=BASE/"upright-v1";REV=OUT/"review";REV.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
objs=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(objs)>=1,"NO_ACTUAL_3D_MESH"

def get_extents():
    pts=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
    low=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    high=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return low,high,pts

before_lo,before_hi,_=get_extents()
before_ext=before_hi-before_lo
# Documented known issue: direct trimesh GLB export erroneously rotated
# world physical Z-up S figure into Blender positive Z = source longitudinal Y.
assert before_ext.z>before_ext.y, f"Input orientation unexpectedly changed: {before_ext}"
rot=Matrix.Rotation(-pi/2,4,'X')
for ob in objs:
    ob.matrix_world=rot @ ob.matrix_world
    # Apply transform, ensuring the saved native BLEND is upright without ad-hoc
    # camera tricks and re-exported GLB stays appropriately oriented.
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    for polygon in ob.data.polygons:
        polygon.use_smooth=True
after_lo,after_hi,pts=get_extents()
after_ext=after_hi-after_lo
assert after_ext.y>after_ext.z and after_ext.z>after_ext.x, f"Incorrect reorientation {after_ext}"

scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="SINGLE"
scene.display.shading.single_color=(.69,.72,.75)
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type="BOTH"
scene.render.resolution_x=850
scene.render.resolution_y=850
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.world.color=(.045,.055,.07)
scene.render.film_transparent=False

ctr=(after_lo+after_hi)*.5
dists={"side":Vector((1,0,0)),"front":Vector((0,-1,0)),
       "front34":Vector((1,-1,0)).normalized(),
       "rear34":Vector((1,1,0)).normalized(),
       "back":Vector((0,1,0))}
camera_data=bpy.data.cameras.new("REAL_UprightS_FiveView")
camera=bpy.data.objects.new("REAL_UprightS_FiveView",camera_data)
scene.collection.objects.link(camera);scene.camera=camera;camera_data.type="ORTHO"
for name,d in dists.items():
    camera.location=ctr+d*7
    camera.rotation_euler=((ctr-camera.location).to_track_quat("-Z","Y")).to_euler()
    right=Vector((-d.y,d.x,0)).normalized()
    projected=[p.dot(right) for p in pts]
    camera_data.ortho_scale=max(max(projected)-min(projected),after_ext.z)*1.16
    scene.render.filepath=str(REV/f"S_visualhull_upright_{name}.png")
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-authority-visualhull-upright-v1.blend"))
bpy.ops.object.select_all(action="DESELECT")
for ob in objs:ob.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/"S-authority-visualhull-upright-v1.glb"),
                          export_format="GLB",use_selection=True,export_yup=True,export_apply=True)

summary={
 "original_mesh":str(SOURCE.relative_to(ROOT)),
 "corrected_blend":str((OUT/"S-authority-visualhull-upright-v1.blend").relative_to(ROOT)),
 "corrected_glb":str((OUT/"S-authority-visualhull-upright-v1.glb").relative_to(ROOT)),
 "before_extents_xyz":list(before_ext),"after_extents_xyz":list(after_ext),
 "glTF_import_orientation_correction_degrees_x":-90,
 "smooth_face_normals_for_visual_review_only":True,
 "production_ready":False,
 "morphology_approved":False}
(OUT/"UPRIGHT_QA.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
