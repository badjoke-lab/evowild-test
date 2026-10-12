"""EvoWild S: AN ARTIST-READY ORIGINAL HUNYUAN SCULPT STATION.

Does not re-generate or modify the creature's geometry. Opens the best
user-recognized real 3-view Hunyuan .blend, locks original PNG SHA,
packs four authentic illustration panels into actual Blender file,
sets correctly oriented ortho image reference empties and cameras,
and creates scoped sculpt mask groups for artist operation.
ZERO substituted highest-authority imagery; ZERO fake model improvements.
"""
import bpy,math,json,hashlib
from mathutils import Vector,Matrix
from pathlib import Path
import numpy as np
ROOT=next(q for q in Path(__file__).resolve().parents
          if (q/'art/s-creature/references/00_s_type_modeling_image_v1.png').exists())
EXP=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
SOURCE=EXP/'hunyuan2mv-original-source-20261012/HUNYUAN2MV_S_THREEVIEW_REAL_ASSET_UNAPPROVED.blend'
OUT=EXP/'original-hunyuan-authority-sculpt-station-20261012'
OUT.mkdir(exist_ok=True,parents=True)
PREV=OUT/'reference-panels';PREV.mkdir(exist_ok=True)
SHA='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
BASE='6651109695536db026d9b52fe10c3fa829cab82915cda1955a5f56eedcec4345'
assert hashlib.sha256(REF.read_bytes()).hexdigest()==SHA
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==BASE
assert REF.stat().st_size==1982782
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
bodyobjs=[o for o in scene.objects if o.type=='MESH']
assert len(bodyobjs)==1
body=bodyobjs[0]
assert len(body.data.vertices)==38802 and len(body.data.polygons)==77684
body.name='KEEP_ORIGINAL_HUNYUAN_S_THREEVIEW_BODY__NOT_SCULPTED'
before=np.array([list(body.matrix_world@v.co) for v in body.data.vertices],dtype=np.float64)
b_hash=hashlib.sha256(before.tobytes()).hexdigest()
b_topology=hashlib.sha256(
    np.asarray([list(f.vertices) for f in body.data.polygons],dtype=np.int32).tobytes()).hexdigest()
bpy.context.view_layer.objects.active=body
body.select_set(True)
# A sculpt artist MUST work against these actual illustration panels
# from original file, not the erroneous earlier chat screenshot.
panels={
 'SIDE':{"crop":[18,75,756,512],"view":[1,0,0],"plane_m":(2.30,1.36)},
 'FRONT':{"crop":[766,81,949,513],"view":[0,-1,0],"plane_m":(.70,1.43)},
 'BACK':{"crop":[951,81,1124,513],"view":[0,1,0],"plane_m":(.65,1.43)},
 'FRONT34':{"crop":[1127,81,1433,513],"view":[1,-1,0],"plane_m":(1.02,1.44)},
}
model_center=Vector((-.0355,.035,-.0354))
def make_collection(name):
    col=bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col
allref=make_collection('AUTHORITY__ONLY_00_S_TYPE_MODELING_IMAGE_V1')
cameras=make_collection('SCULPT_5_ORTHO_REVIEW_CAMERAS')
for tag,info in panels.items():
    path=PREV/('SOURCE_ORIGINAL_UNEDITED_CROP_'+tag+'.png')
    assert path.is_file(),('Missing direct-PNG crop prepared with PIL in runner',path)
    img=bpy.data.images.load(str(path),check_existing=False)
    assert img.size[0]==info['crop'][2]-info['crop'][0]
    assert img.size[1]==info['crop'][3]-info['crop'][1]
    img.name='AUTHORITY_SOURCE_CROP_'+tag
    img.pack()
    view=Vector(info['view']).normalized()
    forward=-view
    right=forward.cross(Vector((0,0,1))).normalized()
    up=Vector((0,0,1))
    normal=right.cross(up)
    # All 4 image cards are placed BEHIND source model in their camera
    # direction; the card is an editor guide, hidden from gameplay/export.
    rot=Matrix((tuple(right),tuple(up),tuple(normal))).transposed().to_quaternion()
    empty=bpy.data.objects.new('CANONICAL_REFERENCE_PANEL__'+tag,None)
    allref.objects.link(empty)
    empty.empty_display_type='IMAGE'
    empty.data=img
    empty.rotation_mode='QUATERNION';empty.rotation_quaternion=rot
    empty.location=model_center-view*1.3
    empty.empty_image_depth='BACK'
    empty.empty_image_side='DOUBLE_SIDED'
    empty.color=(1,1,1,.42)
    empty.empty_display_size=float(info['plane_m'][0])
    empty.empty_image_offset=(-.5,-.5)
    empty.hide_render=True
    empty['authority_source_sha256']=SHA
    empty['crop_from_original_image_pixels']=str(info['crop'])
    empty['alignment_status']='APPROXIMATE REGISTRATION ONLY; ARTIST MUST CALIBRATE BEFORE SCULPT PASS'
    empty['reference_orthographic_view']=tag
    # Distinct camera; no camera-invented ref image.
    cd=bpy.data.cameras.new('ORIGINAL_REFERENCE_'+tag+'_ORTHO')
    cam=bpy.data.objects.new('VIEW_'+tag+'_SOURCE_MODEL_CHECK',cd)
    cameras.objects.link(cam)
    cd.type='ORTHO';cd.ortho_scale=2.16
    cam.location=model_center+view*5
    cam.rotation_euler=(model_center-cam.location).to_track_quat('-Z','Y').to_euler()
    cam['source_actual_illustration_panel']=tag
# REAR34 for real 3D continuity only, never claim original reference for it.
direction=Vector((1,1,0)).normalized()
cd=bpy.data.cameras.new('UNILLUSTRATED_REAR34_CONTINUITY_CHECK')
cam=bpy.data.objects.new('VIEW_REAR34_3D_COHERENCE_ONLY',cd)
cameras.objects.link(cam);cd.type='ORTHO';cd.ortho_scale=2.16
cam.location=model_center+direction*5
cam.rotation_euler=(model_center-cam.location).to_track_quat('-Z','Y').to_euler()
cam['REAL_REAR34_IS_NOT_DEPICTED_IN_AUTHORITY']=True
scene.camera=bpy.data.objects['VIEW_FRONT34_SOURCE_MODEL_CHECK']
# Original user actual entire illustration is embedded as an immutable image
# alongside its exact 4 cropped frames.
master=bpy.data.images.get('IMMUTABLE_S_USER_APPROVED_ORIGINAL_00')
if master is None:
    master=bpy.data.images.load(str(REF),check_existing=False)
master.name='00_S_TYPE_MODELING_IMAGE_V1__HIGHEST_AUTHORITY'
if master.packed_file is None:master.pack()
# Named 3D sculpture ROI vertex groups are selection aids only (weights,
# no vertex motion). None of these count as geometry accomplishments.
verts=np.array([list(body.matrix_world@v.co) for v in body.data.vertices])
local_weights={}
for label,(y0,y1,z0,z1) in {
 'SCULPT_ROI_SHOULDER_AND_CHEST':(-.59,-.015,-.19,.25),
 'PRESERVE_HEAD_CREST':(-2.0,-.60,-.9,2.0),
 'PRESERVE_PELVIS_AND_REAR':(.0,4.0,-.9,2.0),
}.items():
    vg=body.vertex_groups.new(name='EDITOR_GUIDE__'+label)
    ids=np.where((verts[:,1]>y0)&(verts[:,1]<y1)&(verts[:,2]>z0)&(verts[:,2]<z1))[0]
    for i in ids:vg.add([int(i)],1.,'REPLACE')
    local_weights[label]=len(ids)
# Embed workflow rules in .blend itself.
docs=bpy.data.texts.new('READ_FIRST__ORIGINAL_S_ONLY__NO_FALSE_MORPHOLOGY_PASS')
docs.write("""EVOWILD RUN — S ORIGINAL HUNYUAN ART-SCULPT WORKSTATION

Highest image is ONLY art/s-creature/references/00_s_type_modeling_image_v1.png.
This .blend embeds that image and 4 actual cropped reference views.

THIS FILE DOES NOT FIX THE S APPEARANCE. It preserves the original real
Hunyuan mesh exactly. This is preparation for genuine artist-controlled
Blender Sculpt Mode / Edit Mode.

CANONICAL_REFERENCE_PANEL__SIDE/FRONT/BACK/FRONT34 are editor alignment
planes only. Crop pixel frames come from the verified original PNG;
camera-plane placement is APPROXIMATE, and needs artist alignment.

NO historic QEM/R0/R5/H0/H0b/A0/V0/V1 geometry is imported.
No guessed redrawing of the original image. No new mesh plates or decorative
primitive substitutions. No sculpt marks, no rig, no gait, no game merge.
Do not equate a model count, source-matched viewport, or Actions SUCCESS to
canonical S geometry acceptance.

First artist operation: align the main shoulder silhouette and real
armor roots to the actual illustration in SIDE / FRONT / FRONT34.
Only after accurate native mesh edit with REAL FIVE-VIEW comparison may
morphology be reviewed. If edit worsens model, reject and preserve source.
""")
scene["source_S_SHA256"]=SHA
scene["source_Hunyuan_blend_SHA256"]=BASE
scene["S_morphology_has_NOT_been_modified"]=True
scene["full_creature_modeling_approved"]=False
scene["S0_source_morphology_best_candidate_only"]=True
scene["H1_rigging_and_gameplay_disallowed"]=True
body["CAUTION_geometry_not_yet_edited"]=True
body["baseline_coords_SHA256"]=b_hash
body["baseline_face_index_SHA256"]=b_topology
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1440
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
# For startup: real mesh active, one matching original 3/4 camera selected.
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
bpy.context.view_layer.objects.active=body
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='ORTHO'
    elif area.type=='OUTLINER':
        pass
bpy.context.preferences.filepaths.save_version=0
p=OUT/'S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True)
# Sanity AFTER save no vertex/triangle changes.
after=np.array([list(body.matrix_world@v.co) for v in body.data.vertices],dtype=np.float64)
a_hash=hashlib.sha256(after.tobytes()).hexdigest()
a_topology=hashlib.sha256(
    np.asarray([list(f.vertices) for f in body.data.polygons],dtype=np.int32).tobytes()).hexdigest()
assert a_hash==b_hash and a_topology==b_topology
all_packs=[(name,im.packed_file is not None) for name,im in bpy.data.images.items()]
report={
 'SHA256_original_canonical_image':SHA,
 'SHA256_source_Hunyuan_blend':BASE,
 'source_original_mesh_vertices':38802,
 'source_original_mesh_triangles':77684,
 'source_mesh_sha256_before':b_hash,
 'source_mesh_sha256_after':a_hash,
 'source_mesh_unchanged':True,
 'original_face_topology_sha256_before':b_topology,
 'original_face_topology_sha256_after':a_topology,
 'original_face_topology_unchanged':True,
 'number_of_extra_armor_meshes':0,
 'number_of_guide_image_planes':len(panels),
 'source_guide_panels':panels,
 'reference_images_packed':[{'name':x,'packed':y} for x,y in all_packs],
 'orthographic_camera_views':['SIDE','FRONT','FRONT34','BACK','REAR34'],
 'source_original_REAR34_art_exists':False,
 'guide_registration_exact':False,
 'editor_roi_vertex_counts':local_weights,
 'sculpted_edited_geometry':False,
 'original_creature_REVIEW_ONLY':True,
 'game_approved':False,
 'main_updated':False,
 'S_type_completed_count':0,
}
(OUT/'ORIGINAL_S_SCULPT_STATION_PROVENANCE.json').write_text(json.dumps(report,indent=2)+'\n')
print('S_SOURCE_ART_SCULPT_STATION_SAVED',json.dumps(report))
