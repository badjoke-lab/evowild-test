"""Render A2a-v1 thorax/waist review and verify hard-scope locks."""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-a2a-v1'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
crest=bpy.data.objects['S_reference_crest_v11']
mesh=core.data
EDIT=set(range(64,96)); FIXED=set(range(160))-EDIT

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(FIXED):
        h.update(b'core'); h.update(str(i).encode()); h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for i,v in enumerate(crest.data.vertices):
        h.update(b'crest'); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH' or o in (core,crest): continue
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

rp=os.path.join(OUT,'S-vibe-a2a-v1-validation.json')
report=json.load(open(rp))
assert fixed_hash()==report['fixed_geometry_hash']

scene=bpy.context.scene
for stem in ('side','front','front34','back'):
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_a2a_v1_'+stem+'.png')
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
        line='current_stage: experimental Vibe Gate A2a-v1 thorax/waist massing rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-a2a-v1.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review A2a-v1 thorax/waist massing against approved S references. Do not edit pelvis or begin A2b before explicit A2a decision.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_a2a_v1_status: REVIEW_PENDING',
 'vibe_gate_a2a_v1_scope: core rings 8-11 cross-sectional mass only; Y fixed',
 'vibe_gate_a2a_v1_renders:',
 '- output/review/vibe-a2a-v1/S_vibe_a2a_v1_side.png',
 '- output/review/vibe-a2a-v1/S_vibe_a2a_v1_front.png',
 '- output/review/vibe-a2a-v1/S_vibe_a2a_v1_front34.png',
 '- output/review/vibe-a2a-v1/S_vibe_a2a_v1_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_A2A_V1_REVIEW',
 current_stage='A2a-v1 thorax/waist massing rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-a2a-v1.blend',
 next_action='Review A2a-v1 thorax/waist massing. Do not edit pelvis or start A2b before explicit A2a decision.',
 accepted=False,
 gate_a_status='A1_ACCEPTED_A2A_V1_REVIEW_PENDING',
 modeling_status='STOPPED',
 editable_next=[],
 review_renders=[
  'output/review/vibe-a2a-v1/S_vibe_a2a_v1_side.png',
  'output/review/vibe-a2a-v1/S_vibe_a2a_v1_front.png',
  'output/review/vibe-a2a-v1/S_vibe_a2a_v1_front34.png',
  'output/review/vibe-a2a-v1/S_vibe_a2a_v1_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_A2A_V1_RENDER_COMPLETE_STOPPED')
