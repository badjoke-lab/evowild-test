"""Render B1a-v4 local shoulder/chest cleanup and verify hard-scope locks."""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b1a-v4'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

rp=os.path.join(OUT,'S-vibe-b1a-v4-validation.json')
report=json.load(open(rp))
fixed=report['fixed_vertex_indices']
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

assert fixed_hash()==report['fixed_geometry_hash'], 'B1a fixed-scope hash mismatch before render'

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b1a_v4_'+stem+'.png')
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
        line='current_stage: experimental Vibe Gate B1a-v4 local shoulder/chest cleanup rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b1a-v4.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B1a-v4 five views against B0-v025, B1a-v2, B1a-v3 and approved S references. Decide KEEP/REVISE. Do not start B1b before explicit decision.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b1a_v4_status: REVIEW_PENDING',
 'vibe_gate_b1a_v4_scope: same locked shoulder/chest region; stronger boundary-tapered Taubin relax',
 'vibe_gate_b1a_v4_renders:',
 '- output/review/vibe-b1a-v4/S_vibe_b1a_v4_side.png',
 '- output/review/vibe-b1a-v4/S_vibe_b1a_v4_front.png',
 '- output/review/vibe-b1a-v4/S_vibe_b1a_v4_front34.png',
 '- output/review/vibe-b1a-v4/S_vibe_b1a_v4_rear34.png',
 '- output/review/vibe-b1a-v4/S_vibe_b1a_v4_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B1A_V2_REVIEW',
 current_stage='B1a-v4 local shoulder/chest cleanup rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-b1a-v4.blend',
 next_action='Review B1a-v4 against B0-v025, B1a-v2, B1a-v3 and approved S references. Do not start B1b before explicit decision.',
 accepted=False,
 modeling_status='STOPPED',
 editable_next=[],
 keep_fixed_next=['B0-v025 source remains recovery source'],
 review_renders=[
  'output/review/vibe-b1a-v4/S_vibe_b1a_v4_side.png',
  'output/review/vibe-b1a-v4/S_vibe_b1a_v4_front.png',
  'output/review/vibe-b1a-v4/S_vibe_b1a_v4_front34.png',
  'output/review/vibe-b1a-v4/S_vibe_b1a_v4_rear34.png',
  'output/review/vibe-b1a-v4/S_vibe_b1a_v4_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B1A_V4_RENDER_COMPLETE_STOPPED')
