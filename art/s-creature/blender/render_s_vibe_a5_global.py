"""Vibe Gate A5: global five-view silhouette review only.
Source: S-vibe-a4-v2.blend.
NO geometry edits are permitted.
"""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-a5-global'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']

def geometry_hash():
    h=hashlib.sha256()
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH': continue
        h.update(o.name.encode())
        h.update(str(len(o.data.vertices)).encode())
        h.update(str(len(o.data.polygons)).encode())
        for i,v in enumerate(o.data.vertices):
            h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

before=geometry_hash()
scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_a5_'+stem+'.png')
    bpy.ops.render.render(write_still=True)
after=geometry_hash()
assert before==after

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A5-global-silhouette-review',
 'source':'S-vibe-a4-v2.blend',
 'decision':'REVIEW_PENDING',
 'geometry_edit':False,
 'geometry_hash_before':before,
 'geometry_hash_after':after,
 'geometry_unchanged':True,
 'rendered_views':list(views),
 'references':['00_full_reference.png','01_s_body_primary.png','02_s_silhouette.png'],
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-a5-global-validation.json'),'w') as f:
    json.dump(report,f,indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe Gate A5 global five-view rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-a4-v2.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review A5 SIDE/FRONT/FRONT34/REAR34/BACK globally against approved S references and decide overall experimental Gate A. Do not start Gate B before the A5 decision.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_a5_status: REVIEW_PENDING',
 'vibe_gate_a5_geometry_unchanged: true',
 'vibe_gate_a5_renders:',
 '- output/review/vibe-a5-global/S_vibe_a5_side.png',
 '- output/review/vibe-a5-global/S_vibe_a5_front.png',
 '- output/review/vibe-a5-global/S_vibe_a5_front34.png',
 '- output/review/vibe-a5-global/S_vibe_a5_rear34.png',
 '- output/review/vibe-a5-global/S_vibe_a5_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_A5_GLOBAL_REVIEW',
 current_stage='A5 global five-view rendered; overall Gate A review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-a4-v2.blend',
 next_action='Review A5 globally against approved S references and decide overall experimental Gate A. Do not start Gate B before decision.',
 accepted=False,
 gate_a_status='A5_GLOBAL_REVIEW_PENDING',
 modeling_status='STOPPED',
 editable_next=[],
 keep_fixed_next=['all geometry'],
 review_renders=[
  'output/review/vibe-a5-global/S_vibe_a5_side.png',
  'output/review/vibe-a5-global/S_vibe_a5_front.png',
  'output/review/vibe-a5-global/S_vibe_a5_front34.png',
  'output/review/vibe-a5-global/S_vibe_a5_rear34.png',
  'output/review/vibe-a5-global/S_vibe_a5_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_A5_GLOBAL_RENDER_COMPLETE_STOPPED')
