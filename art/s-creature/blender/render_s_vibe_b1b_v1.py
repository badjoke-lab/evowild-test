"""Render B1b-v1 X-only shoulder/chest plane fairing and verify hard locks."""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b1b-v1'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

rp=os.path.join(OUT,'S-vibe-b1b-v1-validation.json')
report=json.load(open(rp))
fixed=report['fixed_vertex_indices']
editable=report['editable_vertex_indices']
preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]

def fixed_hash():
    h=hashlib.sha256()
    for i in fixed:
        h.update(b'body');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for i in editable:
        h.update(b'yz');h.update(str(i).encode());h.update(repr((mesh.vertices[i].co.y,mesh.vertices[i].co.z)).encode())
    for o in sorted(preserved,key=lambda o:o.name):
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(o.name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

assert fixed_hash()==report['fixed_geometry_hash'], 'B1b-v1 hard-scope hash mismatch before render'

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b1b_v1_'+stem+'.png')
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
        line='current_stage: experimental Vibe B1b-v1 X-only shoulder-plane shaping rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b1b-v1.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B1b-v1 five views against B0-v025 and approved S references. Decide KEEP/REVISE. Do not advance beyond B1 shoulder/chest before explicit decision.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b1b_v1_status: REVIEW_PENDING',
 'vibe_gate_b1b_v1_scope: X-only shoulder/chest plane fairing; all body Y/Z exact fixed',
 'vibe_gate_b1b_v1_renders:',
 '- output/review/vibe-b1b-v1/S_vibe_b1b_v1_side.png',
 '- output/review/vibe-b1b-v1/S_vibe_b1b_v1_front.png',
 '- output/review/vibe-b1b-v1/S_vibe_b1b_v1_front34.png',
 '- output/review/vibe-b1b-v1/S_vibe_b1b_v1_rear34.png',
 '- output/review/vibe-b1b-v1/S_vibe_b1b_v1_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B1B_V1_REVIEW',
 current_stage='B1b-v1 X-only shoulder-plane shaping rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-b1b-v1.blend',
 next_action='Review B1b-v1 against B0-v025 and approved S references. Do not advance beyond B1 shoulder/chest before explicit decision.',
 accepted=False,
 modeling_status='STOPPED',
 editable_next=[],
 review_renders=[
  'output/review/vibe-b1b-v1/S_vibe_b1b_v1_side.png',
  'output/review/vibe-b1b-v1/S_vibe_b1b_v1_front.png',
  'output/review/vibe-b1b-v1/S_vibe_b1b_v1_front34.png',
  'output/review/vibe-b1b-v1/S_vibe_b1b_v1_rear34.png',
  'output/review/vibe-b1b-v1/S_vibe_b1b_v1_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B1B_V1_RENDER_COMPLETE_STOPPED')
