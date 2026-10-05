"""Render B1d-v2 tapered shoulder-limb bridge and verify hard locks."""
import bpy, bmesh, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b1d-v2'); os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

rp=os.path.join(OUT,'S-vibe-b1d-v2-validation.json')
report=json.load(open(rp))
fixed=report['fixed_vertex_indices']
preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]

def fixed_hash():
    h=hashlib.sha256()
    for i in fixed:
        h.update(b'body');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for o in sorted(preserved,key=lambda o:o.name):
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(o.name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

assert fixed_hash()==report['fixed_geometry_hash'], 'B1d-v2 fixed-scope hash mismatch before render'

bm=bmesh.new();bm.from_mesh(mesh)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b1d_v2_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

assert fixed_hash()==report['fixed_geometry_hash']
report['rendered_views']=list(views)
report['render_fixed_geometry_unchanged']=True
report['render_non_manifold_edge_count']=0
report['status']='REVIEW_PENDING'
with open(rp,'w') as f: json.dump(report,f,indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe B1d-v2 tapered shoulder-limb bridge rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b1d-v2.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B1d-v2 five views against B1d-v1/B1c-v2/B0-v025 and approved S references. Decide KEEP/REVISE. B2 remains blocked.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b1d_v2_status: REVIEW_PENDING',
 'vibe_gate_b1d_v2_scope: refined shoulder-root patch; tapered bridge guide; topology/boundary fixed',
 'vibe_gate_b1d_v2_renders:',
 '- output/review/vibe-b1d-v2/S_vibe_b1d_v2_side.png',
 '- output/review/vibe-b1d-v2/S_vibe_b1d_v2_front.png',
 '- output/review/vibe-b1d-v2/S_vibe_b1d_v2_front34.png',
 '- output/review/vibe-b1d-v2/S_vibe_b1d_v2_rear34.png',
 '- output/review/vibe-b1d-v2/S_vibe_b1d_v2_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B1D_V2_REVIEW',
 current_stage='B1d-v2 tapered shoulder-limb bridge rendered; review pending; modeling stopped',
 branch='exp/s-creature-vibe-modeling',
 current_model_file='output/S-vibe-b1d-v2.blend',
 next_action='Review B1d-v2 against B1d-v1/B1c-v2/B0-v025 and approved S references. Decide KEEP/REVISE. B2 remains blocked.',
 accepted=False,
 modeling_status='STOPPED',
 editable_next=[],
 review_renders=[
  'output/review/vibe-b1d-v2/S_vibe_b1d_v2_side.png',
  'output/review/vibe-b1d-v2/S_vibe_b1d_v2_front.png',
  'output/review/vibe-b1d-v2/S_vibe_b1d_v2_front34.png',
  'output/review/vibe-b1d-v2/S_vibe_b1d_v2_rear34.png',
  'output/review/vibe-b1d-v2/S_vibe_b1d_v2_back.png'
 ],
 b2_status='BLOCKED'
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B1D_V2_RENDER_COMPLETE_STOPPED')
