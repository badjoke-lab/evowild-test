"""Render B0-v025 continuity candidate and verify preserved crest/toes."""
import bpy, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b0-v025'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]

def preserved_hash():
    h=hashlib.sha256()
    for o in sorted(preserved,key=lambda o:o.name):
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(o.name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

rp=os.path.join(OUT,'S-vibe-b0-v025-validation.json')
report=json.load(open(rp))
assert preserved_hash()==report['preserved_geometry_hash']

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b0_v025_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

assert preserved_hash()==report['preserved_geometry_hash']
report['rendered_views']=list(views)
report['render_preserved_geometry_unchanged']=True
report['status']='REVIEW_PENDING'
with open(rp,'w') as f: json.dump(report,f,indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe Gate B0-v025 continuity candidate rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b0-v025.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B0-v025 five-view continuity candidate against accepted Gate A. Decide whether voxel remesh preserves silhouette and safely unifies limb roots. Do not start B1 before B0 decision.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b0_v025_status: REVIEW_PENDING',
 'vibe_gate_b0_v025_method: core+four limbs joined then voxel remesh 0.025',
 'vibe_gate_b0_v025_renders:',
 '- output/review/vibe-b0-v025/S_vibe_b0_v025_side.png',
 '- output/review/vibe-b0-v025/S_vibe_b0_v025_front.png',
 '- output/review/vibe-b0-v025/S_vibe_b0_v025_front34.png',
 '- output/review/vibe-b0-v025/S_vibe_b0_v025_rear34.png',
 '- output/review/vibe-b0-v025/S_vibe_b0_v025_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B0_V025_REVIEW',
 current_stage='B0-v025 continuity candidate rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-b0-v025.blend',
 next_action='Review B0-v025 against accepted Gate A five-view. Decide whether continuity method is safe before B1.',
 accepted=False,
 modeling_status='STOPPED',
 editable_next=[],
 keep_fixed_next=['accepted Gate A source remains immutable'],
 review_renders=[
  'output/review/vibe-b0-v025/S_vibe_b0_v025_side.png',
  'output/review/vibe-b0-v025/S_vibe_b0_v025_front.png',
  'output/review/vibe-b0-v025/S_vibe_b0_v025_front34.png',
  'output/review/vibe-b0-v025/S_vibe_b0_v025_rear34.png',
  'output/review/vibe-b0-v025/S_vibe_b0_v025_back.png'
 ]
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B0_V025_RENDER_COMPLETE_STOPPED')
