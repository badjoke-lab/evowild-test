"""Render A1-v8 crest-only review and verify every non-crest coordinate remains fixed."""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-a1-v8'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
crest=bpy.data.objects['S_layered_crest_v8']

def fixed_hash():
    h=hashlib.sha256()
    for i,v in enumerate(core.data.vertices):
        h.update(core.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH' or o in (core,crest): continue
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

rp=os.path.join(OUT,'S-vibe-a1-v8-validation.json')
report=json.load(open(rp))
assert fixed_hash()==report['fixed_geometry_hash']

scene=bpy.context.scene
for stem in ('side','front','front34','back'):
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_a1_v8_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

assert fixed_hash()==report['fixed_geometry_hash']
report['rendered_views']=['side','front','front34','back']
report['render_geometry_unchanged']=True
report['status']='REVIEW_PENDING'
with open(rp,'w') as f: json.dump(report,f,indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe Gate A1-v8 crest-only rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-a1-v8.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review A1-v8 crest in SIDE/FRONT/FRONT34/BACK. If crest passes, review complete A1 head/crest/neck; do not start A2 before explicit acceptance.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_a1_v8_status: REVIEW_PENDING',
 'vibe_gate_a1_v8_scope: crest face orientation only',
 'vibe_gate_a1_v8_noncrest_geometry_unchanged: true',
 'vibe_gate_a1_v8_renders:',
 '- output/review/vibe-a1-v8/S_vibe_a1_v8_side.png',
 '- output/review/vibe-a1-v8/S_vibe_a1_v8_front.png',
 '- output/review/vibe-a1-v8/S_vibe_a1_v8_front34.png',
 '- output/review/vibe-a1-v8/S_vibe_a1_v8_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_A1_V8_REVIEW',
 current_stage='A1-v8 crest-only rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-a1-v8.blend',
 next_action='Review v8 crest in SIDE/FRONT/FRONT34/BACK. If crest passes, decide whether complete A1 head/crest/neck is accepted. Do not start A2 before explicit A1 acceptance.',
 accepted=False,
 gate_a_status='A1_V8_REVIEW_PENDING',
 modeling_status='STOPPED',
 editable_next=[],
 review_renders=[
  'output/review/vibe-a1-v8/S_vibe_a1_v8_side.png',
  'output/review/vibe-a1-v8/S_vibe_a1_v8_front.png',
  'output/review/vibe-a1-v8/S_vibe_a1_v8_front34.png',
  'output/review/vibe-a1-v8/S_vibe_a1_v8_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_A1_V8_RENDER_COMPLETE_STOPPED')
