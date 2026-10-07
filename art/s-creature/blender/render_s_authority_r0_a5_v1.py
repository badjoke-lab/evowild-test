"""Render authority R0-A5 v1 long layered tail review and stop."""
import bpy,bmesh,os,json

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','authority-r0-a5-v1'); os.makedirs(REVIEW,exist_ok=True)
body=bpy.data.objects['S_B2a_v5_continuous_body']
rp=os.path.join(OUT,'S-authority-r0-a5-v1-validation.json')
report=json.load(open(rp))

assert report['gate']=='R0-A5-v1-authority-long-layered-tail'
assert report['outside_tail_support_unchanged']
assert report['preexisting_meshes_unchanged']
assert report['feet_geometry_unchanged']
assert report['body_topology_unchanged']
assert report['body_nonmanifold_edge_count']==0
assert report['blade_count']==7

bm=bmesh.new(); bm.from_mesh(body.data)
assert len([e for e in bm.edges if len(e.link_faces)!=2])==0
bm.free()

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_authority_r0_a5_v1_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

report['rendered_views']=list(views)
report['status']='REVIEW_PENDING'
report['modeling_status']='STOPPED'
json.dump(report,open(rp,'w'),indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: authority reset R0-A5 v1 long layered tail rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-authority-r0-a5-v1.blend'
    elif line.startswith('next_action:'):
        line='next_action: Compare R0-A5 v1 five views directly with references/00_s_type_modeling_image_v1.png. Decide KEEP/REVISE/REJECT. Do not start R0-A6 before acceptance.'
    lines.append(line)
lines += [
 '',
 'authority_r0_a5_v1_status: REVIEW_PENDING / STOPPED',
 'authority_r0_a5_v1_model: output/S-authority-r0-a5-v1.blend',
 'authority_r0_a6_status: BLOCKED_PENDING_R0_A5_REVIEW',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='AUTHORITY_R0_A5_V1_REVIEW',
 current_stage='R0-A5 v1 long layered tail rendered; review pending; modeling stopped',
 current_model_file='output/S-authority-r0-a5-v1.blend',
 next_action='Review R0-A5 v1 five views directly against references/00_s_type_modeling_image_v1.png. Decide KEEP/REVISE/REJECT. Do not start R0-A6 before acceptance.',
 accepted=False,modeling_status='STOPPED',editable_next=[],
 review_renders=[
  'output/review/authority-r0-a5-v1/S_authority_r0_a5_v1_side.png',
  'output/review/authority-r0-a5-v1/S_authority_r0_a5_v1_front.png',
  'output/review/authority-r0-a5-v1/S_authority_r0_a5_v1_front34.png',
  'output/review/authority-r0-a5-v1/S_authority_r0_a5_v1_rear34.png',
  'output/review/authority-r0-a5-v1/S_authority_r0_a5_v1_back.png'
 ],
 r0_a5_v1={
  'source':'output/S-authority-r0-a4-v3.blend',
  'output':'output/S-authority-r0-a5-v1.blend',
  'scope':'long layered tail',
  'decision':'REVIEW_PENDING',
  'status':'STOPPED_AFTER_FIVE_VIEW_RENDER',
  'plan':'S_AUTHORITY_R0_A5_V1_PLAN.md'
 },
 r0_a6_status='BLOCKED_PENDING_R0_A5_REVIEW'
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('S_AUTHORITY_R0_A5_V1_RENDER_COMPLETE_STOPPED')
