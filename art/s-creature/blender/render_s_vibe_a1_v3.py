"""Render crest-only A1-v3; stop."""
import bpy, os, json, hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-a1-v3'); os.makedirs(REVIEW,exist_ok=True)
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
mesh=core.data
cage=bpy.data.collections['S_REBUILD_GATE_A']
FIXED_CORE=set(range(0,160))
def hash_fixed():
    h=hashlib.sha256()
    for i in sorted(FIXED_CORE):
        h.update(core.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH' or o==core: continue
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()
rp=os.path.join(OUT,'S-vibe-a1-v3-validation.json')
report=json.load(open(rp))
assert hash_fixed()==report['fixed_geometry_hash_after']
scene=bpy.context.scene
for stem in ('side','front','front34','back'):
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_a1_v3_'+stem+'.png')
    bpy.ops.render.render(write_still=True)
assert hash_fixed()==report['fixed_geometry_hash_after']
report['rendered_views']=['side','front','front34','back']
report['render_geometry_unchanged']=True
report['status']='REVIEW_PENDING'
with open(rp,'w') as f: json.dump(report,f,indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
old=open(cp).read()
lines=[]
for line in old.splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe Gate A1-v3 crest-only rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-a1-v3.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review A1-v3 crest only against C5/H6 and A1-v2. Do not start A2.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_a1_v3_status: REVIEW_PENDING',
 'vibe_gate_a1_v3_scope: crest only',
 'vibe_gate_a1_v3_head_neck_unchanged: true',
 'vibe_gate_a1_v3_non_a1_geometry_unchanged: true',
 'vibe_gate_a1_v3_renders:',
 '- output/review/vibe-a1-v3/S_vibe_a1_v3_side.png',
 '- output/review/vibe-a1-v3/S_vibe_a1_v3_front.png',
 '- output/review/vibe-a1-v3/S_vibe_a1_v3_front34.png',
 '- output/review/vibe-a1-v3/S_vibe_a1_v3_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_A1_V3_REVIEW',
 current_stage='A1-v3 crest-only rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-a1-v3.blend',
 next_action='Review crest-only A1-v3. Do not start A2 without acceptance.',
 accepted=False,
 gate_a_status='A1_V3_REVIEW_PENDING',
 modeling_status='STOPPED',
 review_renders=[
  'output/review/vibe-a1-v3/S_vibe_a1_v3_side.png',
  'output/review/vibe-a1-v3/S_vibe_a1_v3_front.png',
  'output/review/vibe-a1-v3/S_vibe_a1_v3_front34.png',
  'output/review/vibe-a1-v3/S_vibe_a1_v3_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_A1_V3_RENDER_COMPLETE_STOPPED')
