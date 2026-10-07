"""Render authority R0-A4 v3 five-view review and stop."""
import bpy,bmesh,os,json

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','authority-r0-a4-v3'); os.makedirs(REVIEW,exist_ok=True)
body=bpy.data.objects['S_B2a_v5_continuous_body']
rp=os.path.join(OUT,'S-authority-r0-a4-v3-validation.json')
report=json.load(open(rp))

assert report['gate']=='R0-A4-v3-authority-split-hoof-blades'
assert report['body_geometry_unchanged']
assert report['body_topology_unchanged']
assert report['retained_meshes_unchanged']
assert report['generic_toe_objects_remaining']==0
assert report['dominant_prongs_per_foot']==2
assert report['central_base_objects_per_foot']==0

bm=bmesh.new(); bm.from_mesh(body.data)
assert len([e for e in bm.edges if len(e.link_faces)!=2])==0
bm.free()

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_authority_r0_a4_v3_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

report['rendered_views']=list(views)
report['status']='REVIEW_PENDING'
report['modeling_status']='STOPPED'
json.dump(report,open(rp,'w'),indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: authority reset R0-A4 v3 split hoof/blade feet rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-authority-r0-a4-v3.blend'
    elif line.startswith('next_action:'):
        line='next_action: Compare R0-A4 v3 five views directly with references/00_s_type_modeling_image_v1.png. Decide KEEP/REVISE/REJECT. Do not start R0-A5 before acceptance.'
    lines.append(line)
lines += [
 '',
 'authority_r0_a4_v3_status: REVIEW_PENDING / STOPPED',
 'authority_r0_a4_v3_model: output/S-authority-r0-a4-v3.blend',
 'authority_r0_a5_status: BLOCKED_PENDING_R0_A4_REVIEW',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='AUTHORITY_R0_A4_V3_REVIEW',
 current_stage='R0-A4 v3 split hoof/blade feet rendered; review pending; modeling stopped',
 current_model_file='output/S-authority-r0-a4-v3.blend',
 next_action='Review R0-A4 v3 five views directly against references/00_s_type_modeling_image_v1.png. Decide KEEP/REVISE/REJECT. Do not start R0-A5 before acceptance.',
 accepted=False,modeling_status='STOPPED',editable_next=[],
 review_renders=[
  'output/review/authority-r0-a4-v3/S_authority_r0_a4_v3_side.png',
  'output/review/authority-r0-a4-v3/S_authority_r0_a4_v3_front.png',
  'output/review/authority-r0-a4-v3/S_authority_r0_a4_v3_front34.png',
  'output/review/authority-r0-a4-v3/S_authority_r0_a4_v3_rear34.png',
  'output/review/authority-r0-a4-v3/S_authority_r0_a4_v3_back.png'
 ],
 r0_a4_v3={
  'source':'output/S-authority-r0-a3-v2.blend',
  'output':'output/S-authority-r0-a4-v3.blend',
  'scope':'split hoof/blade feet',
  'decision':'REVIEW_PENDING',
  'status':'STOPPED_AFTER_FIVE_VIEW_RENDER',
  'plan':'S_AUTHORITY_R0_A4_V3_PLAN.md'
 },
 r0_a5_status='BLOCKED_PENDING_R0_A4_REVIEW'
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('S_AUTHORITY_R0_A4_V3_RENDER_COMPLETE_STOPPED')
