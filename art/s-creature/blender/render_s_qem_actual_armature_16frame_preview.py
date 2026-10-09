"""Render ALL 16 actual keyed frames from stored QEM Blender armature test.
No changes to source creature geometry, bones, weights or keyframes.
The accompanying GIF is a slowed pose-test preview, NOT running gait.
"""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments/qem-deformation-gate-20261010/armature-test-v1"
DIR=OUT/"motion-preview-16-frames"
DIR.mkdir(parents=True,exist_ok=True)
facts=json.loads((OUT/"ARMATURE_TEST_QA.json").read_text())
assert facts["real_armature_modifier"] and facts["armature_bones"]==5
assert facts["gate"]=="PASS_LIMITED_ARMATURE_SKINNING"
src=bpy.data.objects["QEM_SOURCE_IMMUTABLE_29948_VERTICES"]
posed=bpy.data.objects["QEM_EXACT_SURFACE_ARMATURE_SKIN_TEST"]
arm=bpy.data.objects["S_QEM_ARMATURE_DEFORMATION_PROOF"]
assert len(posed.data.vertices)==29948 and len(posed.data.polygons)==59932
assert len(arm.data.bones)==5
assert [m.type for m in posed.modifiers].count("ARMATURE")==1
scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
camera=scene.camera
center=Vector((0,0,1.275))
v=Vector((1,-1,0)).normalized()
camera.location=center+v*9
camera.rotation_euler=((center-camera.location).to_track_quat("-Z","Y")).to_euler()
camera.data.type="ORTHO"
camera.data.ortho_scale=4.50 # slightly tighter than objective shape reviews
src.hide_render=True;posed.hide_render=False;arm.hide_render=True
files=[]
for f in range(1,17):
    scene.frame_set(f)
    scene.render.filepath=str(DIR/f"S_QEM_real_armature_frame_{f:02d}.png")
    bpy.ops.render.render(write_still=True)
    files.append(scene.render.filepath)
(DIR/"PREVIEW_DESCRIPTION.json").write_text(json.dumps({
 "source":"Stored actual QEM armature Blender model, keyframes 1, 8, 16",
 "rendered_frames":list(range(1,17)),
 "camera":"front34, same for every frame; closer crop ortho 4.50",
 "geometry_alteration":"none (existing armature pose only)",
 "gait_test":"NO, simple limited limb hinge pose loop",
 "animation_loop":"one test cycle",
 "original_fps":scene.render.fps,
 "preview_gif_frame_duration_ms":83,
 "gif_not_full_frame_rate":True,
 "game_ready":False
},indent=2)+"\n")
print("QEM_REAL_RIG_16_KEYED_FRAMES_RENDERED",len(files))
