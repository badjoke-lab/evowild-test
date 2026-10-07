"""R0-A6 full-body authority review. Render only; no geometry changes."""
import bpy,bmesh,os,json,hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','authority-r0-a6');os.makedirs(REVIEW,exist_ok=True)

def geometry_hash():
    h=hashlib.sha256()
    for o in sorted([o for o in bpy.data.objects if o.type=='MESH'],key=lambda x:x.name):
        h.update(o.name.encode())
        for v in o.data.vertices:
            h.update(repr(tuple(v.co)).encode())
        for p in o.data.polygons:
            h.update(repr(tuple(p.vertices)).encode())
        h.update(repr(tuple(tuple(r) for r in o.matrix_world)).encode())
    return h.hexdigest()

before=geometry_hash()

# Prior accepted-gate proof files.
checks=[
 ('S-authority-r0-v2-validation.json','ACCEPTED_R0_A1','KEEP'),
 ('S-authority-r0-a2-v2-validation.json','ACCEPTED_R0_A2','KEEP'),
 ('S-authority-r0-a3-v2-validation.json','ACCEPTED_R0_A3','KEEP'),
 ('S-authority-r0-a4-v3-validation.json','ACCEPTED_R0_A4','KEEP'),
 ('S-authority-r0-a5-v2-validation.json','ACCEPTED_R0_A5','KEEP'),
]
accepted=[]
for fn,status,decision in checks:
    r=json.load(open(os.path.join(OUT,fn)))
    assert r['status']==status,(fn,r['status'])
    assert r['decision']==decision,(fn,r['decision'])
    accepted.append({'file':fn,'status':status,'decision':decision})

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_authority_r0_a6_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

after=geometry_hash()
assert before==after,(before,after)

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'R0-A6-full-body-authority-review',
 'status':'REVIEW_PENDING',
 'decision':'REVIEW_PENDING',
 'source':'S-authority-r0-a5-v2.blend',
 'authority_image':'references/00_s_type_modeling_image_v1.png',
 'accepted_prior_gates':accepted,
 'geometry_hash_before':before,
 'geometry_hash_after':after,
 'geometry_unchanged':True,
 'rendered_views':list(views),
 'modeling_status':'STOPPED',
 'scope':'review only; no geometry edits',
 'next':'actual-image full-body comparison against authority'
}
json.dump(report,open(os.path.join(OUT,'S-authority-r0-a6-validation.json'),'w'),indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: R0-A6 full-body five-view authority review rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-authority-r0-a5-v2.blend'
    elif line.startswith('next_action:'):
        line='next_action: Compare R0-A6 SIDE/FRONT/FRONT34/REAR34/BACK directly with references/00_s_type_modeling_image_v1.png and decide whether R0 morphology package is accepted.'
    lines.append(line)
lines += [
 '',
 'authority_r0_a6_status: REVIEW_PENDING / STOPPED',
 'authority_r0_a6_renders:',
 '- output/review/authority-r0-a6/S_authority_r0_a6_side.png',
 '- output/review/authority-r0-a6/S_authority_r0_a6_front.png',
 '- output/review/authority-r0-a6/S_authority_r0_a6_front34.png',
 '- output/review/authority-r0-a6/S_authority_r0_a6_rear34.png',
 '- output/review/authority-r0-a6/S_authority_r0_a6_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='AUTHORITY_R0_A6_REVIEW',
 current_stage='R0-A6 full-body five-view authority review rendered; review pending; modeling stopped',
 current_model_file='output/S-authority-r0-a5-v2.blend',
 next_action='Review R0-A6 SIDE/FRONT/FRONT34/REAR34/BACK directly against references/00_s_type_modeling_image_v1.png and decide R0 package KEEP/REVISE/REJECT.',
 accepted=False,modeling_status='STOPPED',editable_next=[],
 review_renders=[
  'output/review/authority-r0-a6/S_authority_r0_a6_side.png',
  'output/review/authority-r0-a6/S_authority_r0_a6_front.png',
  'output/review/authority-r0-a6/S_authority_r0_a6_front34.png',
  'output/review/authority-r0-a6/S_authority_r0_a6_rear34.png',
  'output/review/authority-r0-a6/S_authority_r0_a6_back.png'
 ],
 r0_a6={'source':'output/S-authority-r0-a5-v2.blend','decision':'REVIEW_PENDING','status':'STOPPED_AFTER_FIVE_VIEW_RENDER','plan':'S_AUTHORITY_R0_A6_PLAN.md'}
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('S_AUTHORITY_R0_A6_RENDER_COMPLETE_STOPPED')
