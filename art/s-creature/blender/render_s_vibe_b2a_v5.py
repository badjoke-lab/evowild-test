"""Render B2a-v5 pre-union forelimb-root rebuild candidate."""
import bpy,os,json,hashlib,bmesh

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b2a-v5');os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B2a_v5_continuous_body']
preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]

def preserved_hash():
    h=hashlib.sha256()
    for o in sorted(preserved,key=lambda o:o.name):
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(o.name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

rp=os.path.join(OUT,'S-vibe-b2a-v5-validation.json')
report=json.load(open(rp))
assert preserved_hash()==report['preserved_geometry_hash']

bm=bmesh.new();bm.from_mesh(body.data)
assert len([e for e in bm.edges if len(e.link_faces)!=2])==0
bm.free()

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b2a_v5_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

assert preserved_hash()==report['preserved_geometry_hash']
report['rendered_views']=list(views)
report['render_preserved_geometry_unchanged']=True
report['render_nonmanifold_edge_count']=0
report['status']='REVIEW_PENDING'
json.dump(report,open(rp,'w'),indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe B2a-v5 pre-union forelimb-root rebuild rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b2a-v5.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B2a-v5 five views against B2a-v4/B1c-v2/B0-v025 and approved S references. Decide KEEP/REVISE. Do not start B2b.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b2a_v5_status: REVIEW_PENDING',
 'vibe_gate_b2a_v5_scope: pre-union forelimb root topology rebuild + same 0.025 voxel continuity',
 'vibe_gate_b2a_v5_renders:',
 '- output/review/vibe-b2a-v5/S_vibe_b2a_v5_side.png',
 '- output/review/vibe-b2a-v5/S_vibe_b2a_v5_front.png',
 '- output/review/vibe-b2a-v5/S_vibe_b2a_v5_front34.png',
 '- output/review/vibe-b2a-v5/S_vibe_b2a_v5_rear34.png',
 '- output/review/vibe-b2a-v5/S_vibe_b2a_v5_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B2A_V5_REVIEW',
 current_stage='B2a-v5 pre-union forelimb-root rebuild rendered; review pending; modeling stopped',
 current_model_file='output/S-vibe-b2a-v5.blend',
 next_action='Review B2a-v5 against B2a-v4/B1c-v2/B0-v025 and approved S references. Decide KEEP/REVISE. Do not start B2b.',
 accepted=False,modeling_status='STOPPED',editable_next=[],
 review_renders=[
  'output/review/vibe-b2a-v5/S_vibe_b2a_v5_side.png',
  'output/review/vibe-b2a-v5/S_vibe_b2a_v5_front.png',
  'output/review/vibe-b2a-v5/S_vibe_b2a_v5_front34.png',
  'output/review/vibe-b2a-v5/S_vibe_b2a_v5_rear34.png',
  'output/review/vibe-b2a-v5/S_vibe_b2a_v5_back.png'
 ],
 b2a_status='REVIEW_PENDING',b2b_status='BLOCKED'
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B2A_V5_RENDER_COMPLETE_STOPPED')
