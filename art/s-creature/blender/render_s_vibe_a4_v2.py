"""Render A4-v2 tail review and verify hard-scope locks."""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-a4-v2'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
mesh=core.data
EDIT=set(range(120,160)); FIXED=set(range(160))-EDIT

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(FIXED):
        h.update(b'core');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH' or o==core: continue
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

rp=os.path.join(OUT,'S-vibe-a4-v2-validation.json')
report=json.load(open(rp))
assert fixed_hash()==report['fixed_geometry_hash']

scene=bpy.context.scene
for stem in ('side','front','front34','back'):
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_a4_v2_'+stem+'.png')
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
        line='current_stage: experimental Vibe Gate A4-v2 tail stem/tip rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-a4-v2.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review A4-v2 tail against approved S body reference. Do not start A5 before explicit A4 decision.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_a4_v2_status: REVIEW_PENDING',
 'vibe_gate_a4_v2_scope: tail rings 15-19 only',
 'vibe_gate_a4_v2_renders:',
 '- output/review/vibe-a4-v2/S_vibe_a4_v2_side.png',
 '- output/review/vibe-a4-v2/S_vibe_a4_v2_front.png',
 '- output/review/vibe-a4-v2/S_vibe_a4_v2_front34.png',
 '- output/review/vibe-a4-v2/S_vibe_a4_v2_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_A4_V2_REVIEW',
 current_stage='A4-v2 tail stem/tip rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-a4-v2.blend',
 next_action='Review A4-v2 tail. Do not start A5 before explicit A4 decision.',
 accepted=False,
 gate_a_status='A1_ACCEPTED_A2_ACCEPTED_A3_ACCEPTED_A4_V2_REVIEW_PENDING',
 modeling_status='STOPPED',
 editable_next=[],
 review_renders=[
  'output/review/vibe-a4-v2/S_vibe_a4_v2_side.png',
  'output/review/vibe-a4-v2/S_vibe_a4_v2_front.png',
  'output/review/vibe-a4-v2/S_vibe_a4_v2_front34.png',
  'output/review/vibe-a4-v2/S_vibe_a4_v2_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_A4_V2_RENDER_COMPLETE_STOPPED')
