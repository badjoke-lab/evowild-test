"""Render B2a-v2 local-refined proximal forelimb root and verify scope/manifold."""
import bpy, bmesh, os, json, hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b2a-v2'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

rp=os.path.join(OUT,'S-vibe-b2a-v2-validation.json')
report=json.load(open(rp))
s=report['support']; s0r=report['station0']; s1r=report['station1']
XMIN,XMAX=s['abs_x_min'],s['abs_x_max']
YMIN,YMAX=s['y_min'],s['y_max']
ZMIN,ZMAX=s['z_min'],s['z_max']
S0_X,S0_Y,S0_Z=s0r['abs_x'],s0r['y'],s0r['z']
S1_X,S1_Y,S1_Z=s1r['abs_x'],s1r['y'],s1r['z']
EPS=1e-5
preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]

def inside_local(co,eps=0.0):
    ax=abs(co.x)
    if not ((XMIN-eps)<=ax<=(XMAX+eps) and (YMIN-eps)<=co.y<=(YMAX+eps) and (ZMIN-eps)<=co.z<=(ZMAX+eps)):
        return False
    sign=1.0 if co.x>=0 else -1.0
    a=Vector((sign*S0_X,S0_Y,S0_Z))
    b=Vector((sign*S1_X,S1_Y,S1_Z))
    axis=b-a
    t=(co-a).dot(axis)/axis.length_squared
    return -eps<=t<=1.0+eps

def outside_body_coords():
    return sorted(tuple(v.co) for v in mesh.vertices if not inside_local(v.co,EPS))

def fixed_hash():
    h=hashlib.sha256()
    for co in outside_body_coords():
        h.update(repr(co).encode())
    for o in sorted(preserved,key=lambda o:o.name):
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(o.name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

assert fixed_hash()==report['fixed_geometry_hash'], 'B2a-v2 fixed-scope hash mismatch before render'

bm=bmesh.new();bm.from_mesh(mesh)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0, f'B2a-v2 non-manifold before render {len(nonmanifold)}'

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b2a_v2_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

assert fixed_hash()==report['fixed_geometry_hash']
report['rendered_views']=list(views)
report['render_fixed_geometry_unchanged']=True
report['render_non_manifold_edge_count']=0
report['status']='REVIEW_PENDING'
with open(rp,'w') as f: json.dump(report,f,indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe B2a-v2 local-refined proximal forelimb root rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b2a-v2.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B2a-v2 five views against B2a-v1/B1c-v2 and approved S references. Decide KEEP/REVISE. Do not start B2b.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b2a_v2_status: REVIEW_PENDING',
 'vibe_gate_b2a_v2_scope: one local station0-to-station1 subdivision + accepted A3a tapered elliptical guide',
 'vibe_gate_b2a_v2_renders:',
 '- output/review/vibe-b2a-v2/S_vibe_b2a_v2_side.png',
 '- output/review/vibe-b2a-v2/S_vibe_b2a_v2_front.png',
 '- output/review/vibe-b2a-v2/S_vibe_b2a_v2_front34.png',
 '- output/review/vibe-b2a-v2/S_vibe_b2a_v2_rear34.png',
 '- output/review/vibe-b2a-v2/S_vibe_b2a_v2_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B2A_V2_REVIEW',
 current_stage='B2a-v2 local-refined proximal forelimb root rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-b2a-v2.blend',
 next_action='Review B2a-v2 against B2a-v1/B1c-v2 and approved S references. Decide KEEP/REVISE. Do not start B2b.',
 accepted=False,
 modeling_status='STOPPED',
 editable_next=[],
 review_renders=[
  'output/review/vibe-b2a-v2/S_vibe_b2a_v2_side.png',
  'output/review/vibe-b2a-v2/S_vibe_b2a_v2_front.png',
  'output/review/vibe-b2a-v2/S_vibe_b2a_v2_front34.png',
  'output/review/vibe-b2a-v2/S_vibe_b2a_v2_rear34.png',
  'output/review/vibe-b2a-v2/S_vibe_b2a_v2_back.png'
 ],
 b2_status='OPEN',
 b2a_status='REVIEW_PENDING',
 b2b_status='BLOCKED'
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B2A_V2_RENDER_COMPLETE_STOPPED')
