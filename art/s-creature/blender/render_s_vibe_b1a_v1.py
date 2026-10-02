"""Render B1a-v1 local shoulder/chest cleanup and verify hard-scope locks."""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b1a-v1'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

rp=os.path.join(OUT,'S-vibe-b1a-v1-validation.json')
report=json.load(open(rp))
reg=report['region']
YMIN,YMAX=reg['y_min'],reg['y_max']
ZMIN,ZMAX=reg['z_min'],reg['z_max']
MY,MZ=reg['margin_y'],reg['margin_z']

def smoothstep01(t):
    t=max(0.0,min(1.0,t))
    return t*t*(3.0-2.0*t)

def boundary_weight(co):
    y,z=co.y,co.z
    if not (YMIN <= y <= YMAX and ZMIN <= z <= ZMAX):
        return 0.0
    dy=min(y-YMIN,YMAX-y); dz=min(z-ZMIN,ZMAX-z)
    return smoothstep01(dy/MY)*smoothstep01(dz/MZ)

# The region membership is based on the saved candidate coordinates.
# Fixed hash is reproduced by hashing all vertices outside the spatial region,
# plus every preserved non-body mesh.
fixed=[i for i,v in enumerate(mesh.vertices) if boundary_weight(v.co)==0.0]
preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]

def fixed_hash():
    h=hashlib.sha256()
    for i in fixed:
        h.update(b'body');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for o in sorted(preserved,key=lambda o:o.name):
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(o.name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

# Because smoothing can move an editable vertex across a box edge, spatial
# recomputation after the edit can misclassify it as fixed. Use the count/hash
# check from refinement as authority by storing explicit fixed indices now if needed.
if fixed_hash()!=report['fixed_geometry_hash']:
    # Reconstruct fixed indices conservatively from the unchanged source relation:
    # vertices that are still outside the region AND have no displacement metadata
    # cannot be resolved here, so fail explicitly rather than weaken validation.
    raise AssertionError('B1a fixed-scope hash mismatch before render')

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b1a_v1_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

assert fixed_hash()==report['fixed_geometry_hash']
report['rendered_views']=list(views)
report['render_fixed_geometry_unchanged']=True
report['status']='REVIEW_PENDING'
with open(rp,'w') as f: json.dump(report,f,indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe Gate B1a-v1 local shoulder/chest cleanup rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b1a-v1.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B1a-v1 five views against B0-v025 and approved S references. Decide whether local cleanup removes voxel waviness without silhouette drift. Do not start B1b before explicit decision.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b1a_v1_status: REVIEW_PENDING',
 'vibe_gate_b1a_v1_scope: boundary-tapered local relax in locked shoulder/chest Y/Z region',
 'vibe_gate_b1a_v1_renders:',
 '- output/review/vibe-b1a-v1/S_vibe_b1a_v1_side.png',
 '- output/review/vibe-b1a-v1/S_vibe_b1a_v1_front.png',
 '- output/review/vibe-b1a-v1/S_vibe_b1a_v1_front34.png',
 '- output/review/vibe-b1a-v1/S_vibe_b1a_v1_rear34.png',
 '- output/review/vibe-b1a-v1/S_vibe_b1a_v1_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B1A_V1_REVIEW',
 current_stage='B1a-v1 local shoulder/chest cleanup rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-b1a-v1.blend',
 next_action='Review B1a-v1 against B0-v025 and approved S references. Do not start B1b before explicit decision.',
 accepted=False,
 modeling_status='STOPPED',
 editable_next=[],
 keep_fixed_next=['B0-v025 source remains recovery source'],
 review_renders=[
  'output/review/vibe-b1a-v1/S_vibe_b1a_v1_side.png',
  'output/review/vibe-b1a-v1/S_vibe_b1a_v1_front.png',
  'output/review/vibe-b1a-v1/S_vibe_b1a_v1_front34.png',
  'output/review/vibe-b1a-v1/S_vibe_b1a_v1_rear34.png',
  'output/review/vibe-b1a-v1/S_vibe_b1a_v1_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B1A_V1_RENDER_COMPLETE_STOPPED')
