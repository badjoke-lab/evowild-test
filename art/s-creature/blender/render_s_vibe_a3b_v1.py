"""Render A3b-v1 hindlimb review and verify hard-scope locks."""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-a3b-v1'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
hindL=bpy.data.objects['S_hindlimb_L']
hindR=bpy.data.objects['S_hindlimb_R']
editable={hindL.name,hindR.name}

def fixed_hash():
    h=hashlib.sha256()
    fixed=[o for o in cage.objects if o.type=='MESH' and o.name not in editable]
    for o in sorted(fixed,key=lambda o:o.name):
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
    for o in (hindL,hindR):
        for k in range(8):
            i=56+k
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(o.data.vertices[i].co)).encode())
    return h.hexdigest()

rp=os.path.join(OUT,'S-vibe-a3b-v1-validation.json')
report=json.load(open(rp))
assert fixed_hash()==report['fixed_geometry_hash']

scene=bpy.context.scene
for stem in ('side','front','front34','back'):
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_a3b_v1_'+stem+'.png')
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
        line='current_stage: experimental Vibe Gate A3b-v1 hindlimb joint rhythm rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-a3b-v1.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review A3b-v1 hindlimb rhythm against S references. Do not edit feet or tail before explicit A3 decision.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_a3b_v1_status: REVIEW_PENDING',
 'vibe_gate_a3b_v1_scope: S_hindlimb_L/R stations 0-6 only; foot-root station 7 and all toes fixed',
 'vibe_gate_a3b_v1_renders:',
 '- output/review/vibe-a3b-v1/S_vibe_a3b_v1_side.png',
 '- output/review/vibe-a3b-v1/S_vibe_a3b_v1_front.png',
 '- output/review/vibe-a3b-v1/S_vibe_a3b_v1_front34.png',
 '- output/review/vibe-a3b-v1/S_vibe_a3b_v1_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_A3B_V1_REVIEW',
 current_stage='A3b-v1 hindlimb joint rhythm rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-a3b-v1.blend',
 next_action='Review A3b-v1 hindlimb rhythm. Do not edit feet or tail before explicit A3 decision.',
 accepted=False,
 gate_a_status='A1_ACCEPTED_A2_ACCEPTED_A3A_KEEP_A3B_V1_REVIEW_PENDING',
 modeling_status='STOPPED',
 editable_next=[],
 review_renders=[
  'output/review/vibe-a3b-v1/S_vibe_a3b_v1_side.png',
  'output/review/vibe-a3b-v1/S_vibe_a3b_v1_front.png',
  'output/review/vibe-a3b-v1/S_vibe_a3b_v1_front34.png',
  'output/review/vibe-a3b-v1/S_vibe_a3b_v1_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_A3B_V1_RENDER_COMPLETE_STOPPED')
