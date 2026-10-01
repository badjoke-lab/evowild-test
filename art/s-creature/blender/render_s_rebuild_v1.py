"""Render exactly five views; verify geometry is unchanged; stop at Gate A."""
import bpy,os,json,hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output');REVIEW=os.path.join(OUT,'review','rebuild-v1');os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
def geometry_hash():
 return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()
report=json.load(open(os.path.join(OUT,'S-rebuild-v1-gate-A.json')))
assert geometry_hash()==report['geometry_sha256']
scene=bpy.context.scene
for stem in ('side','front','front34','rear34','back'):
 scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
 scene.render.filepath=os.path.join(REVIEW,'S_rebuild_'+stem+'.png')
 bpy.ops.render.render(write_still=True)
assert geometry_hash()==report['geometry_sha256'],'Rendering changed geometry'
report['rendered_views']=['side','front','front34','rear34','back'];report['geometry_unchanged_during_render']=True
with open(os.path.join(OUT,'S-rebuild-v1-gate-A.json'),'w') as f:json.dump(report,f,indent=2)
cp=os.path.join(ROOT,'CHECKPOINT.md');old=open(cp).read();lines=[]
for line in old.splitlines():
 if line.startswith('current_stage:'):line='current_stage: S-rebuild-v1 Gate A silhouette cage saved and five views rendered; REVIEW_PENDING / STOPPED'
 elif line.startswith('current_model_file:'):line='current_model_file: output/S-rebuild-v1.blend'
 elif line.startswith('next_action:'):line='next_action: Gate A review against approved Modeling Image v1.0. Do not model further until review instructions.'
 lines.append(line)
lines+=['','gate_a_status: REVIEW_PENDING','modeling_status: STOPPED','gate_a_source: fresh empty scene; no v12 donor geometry used','gate_a_cage_vertices: '+str(report['total_cage_vertices']),'gate_a_done: small wedge head; six skull-rooted layered rear-swept crest plates; tapered non-tubular neck; compact thorax / narrow waist / light pelvis; distinct fore/hind joint chains; three toes per foot; tapered aerodynamic tail','gate_a_render_geometry_unchanged: true','gate_a_scope: S only; no eyes, Cue Band, materials/textures/color design, animation or final retopology','gate_a_limitation: low-complexity cage with overlapping limb/toe roots; no production welding or surface refinement','gate_a_renders:']
lines+=['- output/review/rebuild-v1/S_rebuild_'+stem+'.png' for stem in report['rendered_views']]
open(cp,'w').write('\n'.join(lines)+'\n')
hp=os.path.join(ROOT,'HANDOFF_STATE.json');state=json.load(open(hp))
state.update(stage='S-rebuild-gate-A',current_stage='S-rebuild-v1 Gate A cage and five renders saved; review pending; modeling stopped',current_model_file='output/S-rebuild-v1.blend',source_model_file='NONE / fresh empty scene',v12_role='technical donor/checkpoint only; no geometry reused',primary_references=['S_MODELING_IMAGE_LOCK.md','S_MORPHOLOGY_RESET_PLAN.md','approved S-type Modeling Image v1.0','references/00_full_reference.png','references/01_s_body_primary.png','references/02_s_silhouette.png'],done=state.get('done',[])+['Read image lock, reset plan, checkpoint, handoff and three repository references; inspected approved Modeling Image v1.0','Built new 760-vertex Gate A silhouette cage from an empty scene; v12 not used as morphology input','Saved output/S-rebuild-v1.blend and rendered SIDE / FRONT / FRONT34 / REAR34 / BACK','Verified render did not change geometry; stopped modeling for Gate A review'],next_action='Gate A review only. Await review decision and explicit next edit before any further modeling.',blockers=[],accepted=False,gate_a_status='REVIEW_PENDING',modeling_status='STOPPED',cage_vertex_count=report['total_cage_vertices'],review_renders=['output/review/rebuild-v1/S_rebuild_'+stem+'.png' for stem in report['rendered_views']],quality_issues=['Gate A global silhouette has not been accepted','Low-complexity cage; limb/toe root welding and anatomical surface refinement deliberately deferred'])
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('GATE_A_RENDER_COMPLETE_MODELING_STOPPED',geometry_hash())
