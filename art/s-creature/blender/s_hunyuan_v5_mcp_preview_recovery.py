"""Run in the current LIVE Blender MCP GUI via execute_blender_code.

Apply *preview only* of the independently tested V5 constrained candidate.
Requires the separate V5_WORKING.blend loaded with unchanged V4 mesh positions.
Do not save .blend automatically. For rollback run s_hunyuan_v5_mcp_revert_preview.py.
"""
import bpy, bmesh, hashlib, json
import numpy as np
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
STATION=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
V4=STATION/'review-v4/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend'
PROPOSAL=STATION/'review-v5-proposals/V5_RECOVERY_GEOMETRIC_PROPOSAL.npz'
REPORT=STATION/'review-v5-proposals/V5_LOCAL_RECOVERY_CANDIDATE_SEARCH.json'
OUT=STATION/'review-v5'
OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(REF)=='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert sha(V4)=='38efa5c29e5ac7b1a6a6afba1256d498763e0f8d3b8e7435d9b38b4b183e879e'
assert bpy.app.version[:3]==(4,3,2)
currentfile=Path(bpy.data.filepath).resolve()
assert currentfile.parent==OUT and currentfile.name=='S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_WORKING.blend',str(currentfile)
bodies=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.name=='geometry_0']
assert len(bodies)==1,len(bodies)
body=bodies[0];mesh=body.data
assert len(mesh.vertices)==38802 and len(mesh.polygons)==77684
assert body.mode=='OBJECT','switch to Object Mode before preview'
before=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
with bpy.data.libraries.load(str(V4),link=False) as (src,dst):
    assert 'geometry_0' in src.meshes
    dst.meshes=['geometry_0']
v4mesh=dst.meshes[0]
v4=np.array([v.co[:] for v in v4mesh.vertices],dtype=np.float32)
f4=np.array([tuple(p.vertices) for p in v4mesh.polygons],dtype=np.int32)
bpy.data.meshes.remove(v4mesh)
faces=np.array([tuple(p.vertices) for p in mesh.polygons],dtype=np.int32)
assert np.array_equal(faces,f4)
assert np.array_equal(before,v4),'V5 working mesh already changed; STOP, do not overwrite work'
p=np.load(PROPOSAL,allow_pickle=False)
indices=p['indices'].astype(np.int32)
target=p['coordinates'].astype(np.float32)
original=p['original_v4_coordinates'].astype(np.float32)
assert len(indices)==len(target)==807 and np.all(indices>=0) and np.all(indices<len(before))
assert np.array_equal(before[indices],original)
expected=before.copy()
expected[indices]=target
info=json.loads(REPORT.read_text())['best_candidate']
assert info['geometry_gate']=='PASS' and info['moved_vertices']==807
def norms(x):
    v=x.astype(np.float64)
    ns=np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]])
    return ns,np.linalg.norm(ns,axis=1)
n0,a0=norms(before)
n1,a1=norms(expected)
assert np.count_nonzero((a0>1e-12)&(a1<=1e-12))==0
valid=(a0>1e-12)&(a1>1e-12)
assert np.count_nonzero(np.sum(n0[valid]*n1[valid],axis=1)<=0)==0
assert float(np.linalg.norm(expected-before,axis=1).max())<.004
backup=OUT/'V5_RECOVERY_PREVIEW_BEFORE.npy'
assert not backup.exists(),'A preview backup already exists. Revert/resolve it first.'
np.save(backup,before)
# Genuine existing mesh edited using BMesh Edit Mode.
bpy.context.view_layer.objects.active=body
body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bm=bmesh.from_edit_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.verts.index_update()
idx_set=set(int(i) for i in indices)
for vert in bm.verts:
    if vert.index in idx_set:
        vert.co=expected[vert.index]
bmesh.update_edit_mesh(mesh,loop_triangles=True,destructive=False)
bpy.ops.object.mode_set(mode='OBJECT')
actual=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
if not np.array_equal(actual,expected):
    mesh.vertices.foreach_set('co',before.ravel())
    mesh.update()
    raise AssertionError('actual edited coordinates differ from approved proposal: restored before')
body['v5_preview_only']='CONSTRAINED LOCAL RECOVERY, UNSAVED'
body['review_decision']='PENDING_VISUAL_REVIEW'
scene=bpy.context.scene
scene['full_creature_modeling_approved']=False
print('S_HUNYUAN_V5_LIVE_PREVIEW_APPLIED_NOT_SAVED',json.dumps({
    'mesh':mesh.name,'edited_vertices':len(indices),
    'max_move':float(np.linalg.norm(actual-before,axis=1).max()),
    'before_backup':str(backup),'visual_review_required':True,
    'no_blend_saved':True,'originals_unchanged':True}))
