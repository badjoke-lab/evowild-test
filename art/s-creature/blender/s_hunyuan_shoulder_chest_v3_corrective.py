"""V3 corrective sculpt: recover V1's uninterrupted shoulder topology,
quantify suspicious V2 changes and replace narrow V2 crease with broad planes.

Technical repair experiment only; quality KEEP requires independent visual review.
Blender 4.3.2, real geometry_0, fixed topology. Source/V1/V2 protected.
"""
import bpy, hashlib, json, sys
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path.cwd()
S=R/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
REF=R/'art/s-creature/references/00_s_type_modeling_image_v1.png'
BASE=S/'S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend'
V1=S/'review-v1/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1.blend'
V2=S/'review-v2/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V2.blend'
O=S/'review-v3';O.mkdir(parents=True,exist_ok=True)
V3=O/'S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend'
sha=lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
checks={str(p.relative_to(R)):sha(p) for p in [REF,BASE,V1,V2]}
assert sha(REF)=='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert sha(BASE)=='1f26bbd4485721a69d74c0c4c4da917dacf9341c15932785e42ba478c3f71c37'
assert sha(V1)=='13d911bbefed39ec602df35b812ce04d27815ac3a7afe3ec0205d77aa65fd212'
assert sha(V2)=='05171a0f0652517a28bb615525f0d4d707ff4bafbe5ac63e87dcd7ef0ce4fc02'
assert bpy.app.version[:3]==(4,3,2)
# Collect V2 real mesh first, before opening authoritative previous V1.
bpy.ops.wm.open_mainfile(filepath=str(V2))
v2_body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V2']
v2_local=np.array([v.co[:] for v in v2_body.data.vertices],dtype=np.float64)
v2_faces=np.array([p.vertices[:] for p in v2_body.data.polygons],dtype=np.int32)
bpy.ops.wm.open_mainfile(filepath=str(V1))
body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1']
mesh=body.data
assert mesh.name=='geometry_0'
before=np.array([v.co[:] for v in mesh.vertices],dtype=np.float64)
faces=np.array([p.vertices[:] for p in mesh.polygons],dtype=np.int32)
assert np.array_equal(faces,v2_faces)
assert before.shape==v2_local.shape==(38802,3) and faces.shape==(77684,3)
transform=body.matrix_world.copy()
inv=transform.inverted()
world=np.array([(transform@v.co)[:] for v in mesh.vertices],dtype=np.float64)
x,y,z=world.T
mid=-.03588832542300224
side=np.where(x>=mid,1.,-1.)
distance=np.abs(x-mid)

def normals(points):
    a=points[faces[:,1]]-points[faces[:,0]]
    b=points[faces[:,2]]-points[faces[:,0]]
    n=np.cross(a,b)
    size=np.linalg.norm(n,axis=1)
    return n,size
n1,a1=normals(before)
n2,a2=normals(v2_local)
valid=(a1>1e-12)&(a2>1e-12)
cos=np.zeros(len(faces))
cos[valid]=np.clip(np.sum(n1[valid]*n2[valid],axis=1)/(a1[valid]*a2[valid]),-1,1)
angular=np.degrees(np.arccos(cos[valid]))
area_ratio=np.ones(len(faces))
area_ratio[valid]=a2[valid]/a1[valid]
# Focus on the damaged shoulder range observed in actual SIDE / FRONT34.
shoulder_roi=(y>-.59)&(y<-.12)&(z>-.25)&(z<.24)
roi_faces=np.any(shoulder_roi[faces],axis=1)
v2_shift=np.linalg.norm(v2_local-before,axis=1)
ordered=np.argsort((1-cos)*roi_faces)[::-1]
worst=[dict(face=int(i),vertices=faces[i].tolist(),normal_angle_deg=float(np.degrees(np.arccos(np.clip(cos[i],-1,1)))),area_ratio=float(area_ratio[i]),v2_shift_max=float(v2_shift[faces[i]].max())) for i in ordered if valid[i] and roi_faces[i]][:30]
diagnostic=dict(
    candidate='V2', baseline='V1', type='mesh_geometry_diagnostics_not_a_proven_notch_cause',
    changed_vertices=int(np.count_nonzero(v2_shift>0)),
    shoulder_faces=int(roi_faces.sum()),
    shoulder_valid_faces=int(np.count_nonzero(valid&roi_faces)),
    shoulder_normal_turn_gt_20deg=int(np.count_nonzero((cos<np.cos(np.deg2rad(20)))&valid&roi_faces)),
    shoulder_normal_turn_gt_45deg=int(np.count_nonzero((cos<np.cos(np.deg2rad(45)))&valid&roi_faces)),
    shoulder_area_ratio_below_half=int(np.count_nonzero((area_ratio<.5)&valid&roi_faces)),
    shoulder_area_ratio_above_2x=int(np.count_nonzero((area_ratio>2)&valid&roi_faces)),
    top_thirty_changed_faces=worst)
(O/'V2_SHOULDER_GEOMETRY_DIAGNOSTICS.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
print('V2_NOTCH_SUSPECT_MESH_DIAGNOSTICS',json.dumps({k:v for k,v in diagnostic.items() if k!='top_thirty_changed_faces'}),flush=True)

# Undo V2 narrow trench and its nonuniform local clamp by working from V1.
# Continuous wide fields and 3D smooth support avoid single narrow negative
# Gaussian ridges; no artificial separate plate meshes or flat shader tricks.
def smooth(a,b,t):
    q=np.clip((t-a)/(b-a),0,1)
    return q*q*(3-2*q)
def gaussian(yc,zc,yr,zr):
    return np.exp(-((y-yc)/yr)**2-((z-zc)/zr)**2)
fade=(smooth(-.57,-.48,y)*(1-smooth(-.045,.04,y))*
      smooth(-.38,-.31,z)*(1-smooth(.16,.24,z)))
lateral=smooth(.024,.092,distance)
shoulder=gaussian(-.398,-.018,.17,.15)
# Wide, asymmetric directional band with no hollowed-out notch next to it.
axis=-.386+.34*(.085-z)
oblique=np.exp(-((y-axis)/.125)**2-((z-.013)/.184)**2)
pectoral=gaussian(-.453,-.137,.122,.12)
humerus=gaussian(-.237,-.235,.09,.15)
tuck=gaussian(-.186,-.106,.095,.107)
D=np.zeros_like(world)
D[:,0]=side*lateral*(-.014*shoulder+.0065*oblique+.0058*humerus-.004*tuck+.002*pectoral)
D[:,1]=-.0024*pectoral+.0018*oblique
D[:,2]=.0032*oblique+.0038*gaussian(-.322,-.22,.13,.082)-.0023*pectoral
D*=fade[:,None]
assert np.isfinite(D).all()

# Critically, repair inverted/degenerate triangles by scaling the ENTIRE
# smooth corrective displacement, never damping isolated vertices (V2 error).
affected=np.where(fade>0)[0]
local_delta=np.zeros_like(before)
for i in affected:
    local_delta[i]=np.asarray((inv@Vector(world[i]+D[i]))[:],dtype=np.float64)-before[i]
factor=1.0
retries=0
while factor>=.01:
    proposal=(before+local_delta*factor).astype(np.float32).astype(np.float64)
    n3,a3=normals(proposal)
    still_valid=(a1>1e-12)&(a3>1e-12)
    flipped=(np.sum(n1[still_valid]*n3[still_valid],axis=1)<0).sum()
    new_degenerate=int(np.count_nonzero((a1>1e-12)&(a3<=1e-12)))
    if flipped==0 and new_degenerate==0:break
    factor*=.8;retries+=1
else:
    raise RuntimeError('No globally smooth displacement passes topology gate')
assert factor>.20, 'V3 correction too weak to be meaningful: stop rather than fake improvement'
for i in affected:
    mesh.vertices[int(i)].co=Vector(proposal[i])
mesh.update()
body.name='S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3'
body['sculpt_revision']='V3 V1-derived corrective smooth shoulder plane; V2 notch not inherited'
body['review_decision']='PENDING_VISUAL_REVIEW'
bpy.context.scene['full_creature_modeling_approved']=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(V3),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(V3))
body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3']
after=np.array([v.co[:] for v in body.data.vertices],dtype=np.float64)
assert np.array_equal(faces,np.array([f.vertices[:] for f in body.data.polygons],dtype=np.int32))
assert np.array_equal(after,proposal)
changed=np.any(after!=before,axis=1)
assert np.count_nonzero(changed)>200
assert np.count_nonzero(changed[fade==0])==0
assert all(sha(R/p)==h for p,h in checks.items())
n3,a3=normals(after)
valid3=(a1>1e-12)&(a3>1e-12)
assert not np.any(np.sum(n1[valid3]*n3[valid3],axis=1)<0)
assert np.count_nonzero(a3<=1e-12)<=np.count_nonzero(a1<=1e-12)
front=(y>-.53)&(y<-.29)&(z>-.08)&(z<.14)
width=lambda arr: float(np.diff(np.quantile(arr[front,0],[.025,.975]))[0])
report=dict(
    result='V3_REAL_MESH_EDITED_RELOADED_TECHNICAL_PASS_NO_ART_APPROVAL',
    source='V1 independent corrective branch', rejected_v2_kept=True,
    blender_version=bpy.app.version_string, mesh='geometry_0',
    vertices=len(after),faces=len(faces),changed_from_v1=int(changed.sum()),
    max_move_from_v1=float(np.linalg.norm(after-before,axis=1).max()),
    global_displacement_factor=factor, safety_retries=retries,
    v1_front_width_quantile=width(before),v2_front_width_quantile=width(v2_local),v3_front_width_quantile=width(after),
    newly_reversed_normals=0,newly_degenerate_faces=0,
    existing_degenerate_faces=int(np.count_nonzero(a1<=1e-12)),
    reload_exact=True,topology_intact=True,outside_roi_unchanged=True,
    protected_hashes=checks,output_hash=sha(V3),
    file=str(V3.relative_to(R)),decision='PENDING_VISUAL_REVIEW')
(O/'V3_TECHNICAL_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez_compressed(O/'V1_TO_V3_DELTA.npz',vertices=np.where(changed)[0],before=before[changed],after=after[changed])
print('V3_ACTUAL_NATIVE_MESH_EDIT_RELOAD_PASS',json.dumps(report),flush=True)
sys.path.insert(0,str(R/'art/s-creature/blender'))
from s_hunyuan_sculpt_review_render import render
render(body,world,O,'V3')
assert all(sha(R/p)==h for p,h in checks.items())
print('V3_REAL_FIVE_VIEW_AND_DETAIL_RENDER_PASS',flush=True)
