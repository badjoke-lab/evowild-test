"""Reproducible local sculpt of the original Hunyuan S mesh, Blender 4.3.2.

Compact, smooth brush fields build shoulder/pectoral/humeral masses and recess
axilla. No replacement geometry, remeshing, topology edits or global scaling.
Run from repository root with Blender --background --python-exit-code 1 --python.
"""
import bpy, hashlib, json, sys
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path.cwd()
STATION=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
SRC=STATION/'S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
OUT=STATION/'review-v1';OUT.mkdir(exist_ok=True)
DEST=OUT/'S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protect={str(p.relative_to(ROOT)):sha(p) for p in (SRC,REF)}
assert sha(SRC)=='1f26bbd4485721a69d74c0c4c4da917dacf9341c15932785e42ba478c3f71c37'
assert sha(REF)=='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert bpy.app.version[:3]==(4,3,2)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=body.data
assert mesh.name=='geometry_0' and len(mesh.vertices)==38802 and len(mesh.polygons)==77684
if body.mode!='OBJECT':
 bpy.context.view_layer.objects.active=body;bpy.ops.object.mode_set(mode='OBJECT')
original=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
world=np.array([body.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
faces=np.array([p.vertices[:] for p in mesh.polygons],dtype=np.int32)
x,y,z=world.T
mid=-.03588832542300224
side=np.sign(x-mid);lateral=np.clip(np.abs(x-mid)/.12,0,1)
def brush(yc,zc,yr,zr):
 q=((y-yc)/yr)**2+((z-zc)/zr)**2
 return np.maximum(0,1-q)**2
# Deltoid/scapular mass: an oblique ridge flowing from upper shoulder
# toward anterior humerus, rather than uniform torso inflation.
shoulder=np.maximum(0,1-((y-(-.365+.34*(.07-z)))/.145)**2-((z-.04)/.205)**2)**2
pectoral=brush(-.445,-.065,.17,.17)
upperarm=brush(-.235,-.245,.11,.17)
axilla=brush(-.185,-.055,.095,.105)
chestfloor=brush(-.355,-.165,.19,.115)
# A restrained posterior lift makes the chest-to-waist underside turn upward.
tuck=brush(-.065,-.072,.115,.085)
# Hard protection boundary with zero displacement beyond this anatomical ROI.
roi=(y>-.59)&(y<.06)&(z>-.40)&(z<.25)
D=np.zeros_like(world)
D[:,0]=side*lateral*(.025*shoulder+.010*pectoral+.022*upperarm-.021*axilla-.010*tuck)
D[:,1]=-.023*pectoral+.006*upperarm+.008*axilla
D[:,2]=.007*shoulder-.025*chestfloor+.014*axilla+.023*tuck
D[~roi]=0
# All fields evaluated on original points: deterministic and no accumulated drift.
inv=body.matrix_world.inverted()
for v,p in zip(mesh.vertices,world+D):v.co=inv@Vector(p)
mesh.update()
body.name='S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1'
body['CAUTION_geometry_not_yet_edited']=False
body['sculpt_revision']='V1; shoulder/pectoral/upper-arm native mesh displacement'
bpy.context.scene['S_morphology_has_NOT_been_modified']=False
bpy.context.scene['full_creature_modeling_approved']=False
body['review_decision']='PENDING_VISUAL_REVIEW'
# Save original materials and guides, before temporary clay render setup.
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(DEST))
body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1'];mesh=body.data
saved=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
assert np.array_equal(np.array([p.vertices[:] for p in mesh.polygons],dtype=np.int32),faces)
expected=np.array([inv@Vector(p) for p in world+D],dtype=np.float32)
assert np.array_equal(saved,expected)
delta=saved-original;lengths=np.linalg.norm(delta,axis=1);changed=lengths>0
assert changed.sum()>1000 and not np.any(changed[~roi])
assert all(sha(ROOT/p)==v for p,v in protect.items())
np.savez_compressed(OUT/'vertex_delta.npz',indices=np.where(changed)[0],before=original[changed],after=saved[changed],delta=delta[changed])
report=dict(result='ACTUAL_NATIVE_MESH_SCULPT_SAVED_AND_RELOADED',blender_version=bpy.app.version_string,
 source_commit='f8c10657e75bde0105bffff932bb1976f3ff71c5',mesh=mesh.name,object=body.name,
 vertices=len(mesh.vertices),faces=len(mesh.polygons),changed_vertices=int(changed.sum()),
 max_displacement=float(lengths.max()),mean_changed_displacement=float(lengths[changed].mean()),
 affected_bounds=[world[changed].min(0).tolist(),world[changed].max(0).tolist()],
 preserved_outside_roi=True,topology_unchanged=True,reload_exact_match=True,protected_sha256=protect,
 protected_unchanged=True,output_blend=str(DEST.relative_to(ROOT)),output_sha256=sha(DEST),
 brush_peak_world_units=dict(shoulder_lateral=.025,pectoral_forward=.023,upperarm_lateral=.022,axilla_recess=.021,chestfloor_down=.025,waist_tuck_up=.023),
 image_registration='Approximate; no claim of pixel alignment; REAR34 is continuity review only')
(OUT/'SCULPT_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print('SCULPT_SAVE_RELOAD_PASS',json.dumps(report),flush=True)
sys.path.insert(0,str(ROOT/'art/s-creature/blender'))
from s_hunyuan_sculpt_review_render import render
render(body,world,OUT,'AFTER')
assert all(sha(ROOT/p)==v for p,v in protect.items())
print('SCULPT_FIVE_VIEWS_AND_DETAILS_RENDERED',flush=True)
