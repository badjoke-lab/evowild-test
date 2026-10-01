"""Render curved-laminar A1-v5 and verify fixed geometry."""
import bpy, os, json, hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-a1-v5'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
fan=bpy.data.objects['S_curved_laminar_crest_v5']

def fixed_hash():
    h=hashlib.sha256()
    for i in range(160):
        h.update(str(i).encode()); h.update(repr(tuple(core.data.vertices[i].co)).encode())
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH' or o==core or o==fan: continue
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

rp=os.path.join(OUT,'S-vibe-a1-v5-validation.json')
report=json.load(open(rp))
assert fixed_hash()==report['fixed_geometry_hash']
scene=bpy.context.scene
for stem in ('side','front','front34','back'):
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_a1_v5_'+stem+'.png')
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
        line='current_stage: experimental Vibe Gate A1-v5 curved laminar crest rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-a1-v5.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review A1-v5 against C5/H6 and FRONT hard-fails. Do not start A2.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_a1_v5_status: REVIEW_PENDING',
 'vibe_gate_a1_v5_scope: curved crest only; v2 head/neck and all non-crest geometry fixed',
 'vibe_gate_a1_v5_renders:',
 '- output/review/vibe-a1-v5/S_vibe_a1_v5_side.png',
 '- output/review/vibe-a1-v5/S_vibe_a1_v5_front.png',
 '- output/review/vibe-a1-v5/S_vibe_a1_v5_front34.png',
 '- output/review/vibe-a1-v5/S_vibe_a1_v5_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_A1_V5_REVIEW',
 current_stage='A1-v5 curved laminar crest rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-a1-v5.blend',
 next_action='Review A1-v5 only. Do not start A2 without explicit A1 acceptance.',
 accepted=False,
 gate_a_status='A1_V5_REVIEW_PENDING',
 modeling_status='STOPPED',
 review_renders=[
  'output/review/vibe-a1-v5/S_vibe_a1_v5_side.png',
  'output/review/vibe-a1-v5/S_vibe_a1_v5_front.png',
  'output/review/vibe-a1-v5/S_vibe_a1_v5_front34.png',
  'output/review/vibe-a1-v5/S_vibe_a1_v5_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_A1_V5_RENDER_COMPLETE_STOPPED')
