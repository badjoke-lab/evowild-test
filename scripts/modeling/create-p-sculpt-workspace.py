"""Author an editable canonical-P Blender review workspace from real existing v6 GLB.

This file is NOT new anatomy or a finished model. It intentionally packs the
unchanged authoritative P.webp into a camera-aligned review scene.
"""
import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'public/concept/P.webp'
GLB=ROOT/'public/models/evowild-p/p-canonical-v6.glb'
OUT=ROOT/'art/p-creature/workspaces/P-v6-canonical-sculpt-review.blend'
META=ROOT/'art/p-creature/workspaces/P-v6-canonical-sculpt-review.json'
OUT.parent.mkdir(parents=True,exist_ok=True)
assert P.is_file() and GLB.is_file(), 'Canonical reference or candidate GLB missing'
expected=hashlib.sha256(P.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.name='Canonical P / editable v6 study, shape NOT approved'
bpy.ops.import_scene.gltf(filepath=str(GLB))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert len(meshes)>=1,'Imported GLB has no mesh objects'
for obj in meshes:
    obj['provenance']='p-canonical-v6.glb; unapproved geometry'
    obj['authority']='P.webp is sole species shape authority'
    obj['do_not_replace_canonical_reference']=True
refcol=bpy.data.collections.new('00_CANONICAL_REFERENCE_LOCKED')
scene.collection.children.link(refcol)
img=bpy.data.images.load(str(P),check_existing=True)
img.pack()
assert img.packed_file, 'Expected packed authoritative image'
# IMAGE empties in the same Blender workspace, safely behind the model for SIDE.
bpy.ops.object.empty_add(type='IMAGE',location=(0,3.0,1.72))
ref=bpy.context.object
ref.name='CANONICAL_P_IMAGE__DO_NOT_MODIFY'
ref.data=img
ref.empty_display_size=4.25
ref.empty_image_depth='BACK'
ref.empty_image_side='DOUBLE_SIDED'
ref.rotation_euler=(math.pi/2,0,0)
ref.color=(1.0,1.0,1.0,.52)
ref.hide_render=True
ref['canonical_sha256']=expected
ref['authority_path']='public/concept/P.webp'
ref.lock_location=[True]*3
ref.lock_rotation=[True]*3
ref.lock_scale=[True]*3
for c in list(ref.users_collection):c.objects.unlink(ref)
refcol.objects.link(ref)
camcol=bpy.data.collections.new('01_REVIEW_ORTHOGRAPHIC_CAMERAS')
scene.collection.children.link(camcol)
def cam(label,position,target=(0,0,1.48),scale=5.8):
    camera_data=bpy.data.cameras.new(label)
    obj=bpy.data.objects.new(label,camera_data)
    camcol.objects.link(obj)
    obj.location=position
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    camera_data.type='ORTHO'; camera_data.ortho_scale=scale
    camera_data.lens=50
    obj['intent']='review image/geometry; no approval'
    return obj
positions={
 'SIDE':(0,-9,2.4),
 'FRONT':(-9,0,2.4),
 'FRONT34':(-7.5,-7.5,3.5),
 'REAR34':(7.5,-7.5,3.5),
 'BACK':(9,0,2.4),
}
cameras={n:cam('CAM_'+n,p) for n,p in positions.items()}
scene.camera=cameras['SIDE']
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1280;scene.render.resolution_y=800
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.color=(.13,.13,.13)
# Record the owner of this blend and what it is NOT.
scene['approval']='REVIEW_PENDING; P v6 shape is REVISE'
scene['canonical_reference']='public/concept/P.webp'
scene['model_source']='public/models/evowild-p/p-canonical-v6.glb'
scene['next_task']='Reference guided torso/face/crest sculpt, static shape approval before gait'
# Make all reference images self-contained and ensure the current camera is selected.
bpy.ops.object.select_all(action='DESELECT')
cameras['SIDE'].select_set(True)
bpy.context.view_layer.objects.active=cameras['SIDE']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
meta={
 'workspace':OUT.relative_to(ROOT).as_posix(),
 'reference':'public/concept/P.webp',
 'reference_sha256':expected,
 'source_glb':'public/models/evowild-p/p-canonical-v6.glb',
 'source_glb_sha256':hashlib.sha256(GLB.read_bytes()).hexdigest(),
 'blend_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
 'blend_bytes':OUT.stat().st_size,
 'mesh_objects':len(meshes),
 'cameras':list(cameras),
 'packed_reference':bool(img.packed_file),
 'status':'EDITABLE_WORKSPACE_ONLY / REVIEW_PENDING / NO_MODEL_QUALITY_GAIN_CLAIM',
}
META.write_text(json.dumps(meta,indent=2)+'\n')
print('P_CANONICAL_EDITABLE_WORKSPACE',json.dumps(meta))
