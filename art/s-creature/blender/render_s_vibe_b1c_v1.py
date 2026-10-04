"""Render B1c-v1 local shoulder-root resurface and verify scope/manifold."""
import bpy, bmesh, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b1c-v1'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

rp=os.path.join(OUT,'S-vibe-b1c-v1-validation.json')
report=json.load(open(rp))
s=report['support']
XMIN,XMAX=s['abs_x_min'],s['abs_x_max']
YMIN,YMAX=s['y_min'],s['y_max']
ZMIN,ZMAX=s['z_min'],s['z_max']
SUPPORT_EPS=1e-5
preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]

def inside_support(co, eps=0.0):
    ax=abs(co.x)
    return (XMIN-eps) <= ax <= (XMAX+eps) and (YMIN-eps) <= co.y <= (YMAX+eps) and (ZMIN-eps) <= co.z <= (ZMAX+eps)

def outside_body_coords():
    return sorted(tuple(v.co) for v in mesh.vertices if not inside_support(v.co, SUPPORT_EPS))

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

assert fixed_hash()==report['fixed_geometry_hash'], 'B1c-v1 fixed-scope hash mismatch before render'

bm=bmesh.new(); bm.from_mesh(mesh)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0, f'B1c-v1 non-manifold before render: {len(nonmanifold)}'

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b1c_v1_'+stem+'.png')
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
        line='current_stage: experimental Vibe B1c-v1 local shoulder-root resurface rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b1c-v1.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B1c-v1 five views against B0-v025 and B1b-v2/v4 plus approved S references. Decide KEEP/REVISE. B2 remains blocked.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b1c_v1_status: REVIEW_PENDING',
 'vibe_gate_b1c_v1_scope: support-contained local subdivision + small XYZ fairing',
 'vibe_gate_b1c_v1_renders:',
 '- output/review/vibe-b1c-v1/S_vibe_b1c_v1_side.png',
 '- output/review/vibe-b1c-v1/S_vibe_b1c_v1_front.png',
 '- output/review/vibe-b1c-v1/S_vibe_b1c_v1_front34.png',
 '- output/review/vibe-b1c-v1/S_vibe_b1c_v1_rear34.png',
 '- output/review/vibe-b1c-v1/S_vibe_b1c_v1_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B1C_V1_REVIEW',
 current_stage='B1c-v1 local shoulder-root resurface rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-b1c-v1.blend',
 next_action='Review B1c-v1 against B0-v025, B1b-v2/v4 and approved S references. Decide KEEP/REVISE. B2 remains blocked.',
 accepted=False,
 modeling_status='STOPPED',
 editable_next=[],
 review_renders=[
  'output/review/vibe-b1c-v1/S_vibe_b1c_v1_side.png',
  'output/review/vibe-b1c-v1/S_vibe_b1c_v1_front.png',
  'output/review/vibe-b1c-v1/S_vibe_b1c_v1_front34.png',
  'output/review/vibe-b1c-v1/S_vibe_b1c_v1_rear34.png',
  'output/review/vibe-b1c-v1/S_vibe_b1c_v1_back.png'
 ],
 b2_status='BLOCKED'
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B1C_V1_RENDER_COMPLETE_STOPPED')
