"""Read-only audit of saved R8C evidence. Does not remake any R8 artifact."""
import hashlib,json,datetime
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
R8=HERE.parent/'r8-form-20261023'
OUT=HERE/'R8C_EVIDENCE_REVIEW.json'
assert not OUT.exists()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n): return json.loads((R8/'evidence'/n).read_text())
s=read('INDEPENDENT_R7_R8C_SWEEP.json'); reload=read('FINAL_FILESC_INDEPENDENT_RELOAD.json')
remote=json.loads((HERE/'R8C_REMOTE_BYTE_VERIFY.json').read_text())
assert remote['all_byte_equal'] and remote['r8_saved_artifact_count']==253
times=[1+i*.25 for i in range(93)]
assert s['variant']=='C' and s['same_body_topology'] and s['weights_bones_keyframes_exact']
assert reload['final_rig_evaluated_coordinates_equal_trial_at_all_93_times']
assert [x['time'] for x in reload['times']]==times
for key,path in [('static','S_ZERO_CANDIDATE_REVISED_R8C.blend'),('rig','verification/S_ZERO_R8C_HIP_DEFORMATION_VERIFIED.blend'),('trial','verification/S_ZERO_R8_FORM_TRIAL_C.blend')]:
    assert sha(R8/path)==reload['file_sha256'][key]
summary={}
for name,record in s['records'].items():
    f=record['frames'];assert [x['time'] for x in f]==times
    summary[name]={
        'samples':len(f),'edge_max':max(x['whole_body']['edge_max'] for x in f),
        'area_min':min(x['whole_body']['area_min'] for x in f),
        'area_max':max(x['whole_body']['area_max'] for x in f),
        'area_p01_min':min(x['whole_body']['area_p01'] for x in f),
        'self_overlap_counts':sorted(set(x['contacts']['whole_body_nonadjacent_triangle_BVH'] for x in f)),
        'hip_attachment_contact_count_range':[min(sum(x['contacts']['hip_to_other_mesh_BVH'].values()) for x in f),max(sum(x['contacts']['hip_to_other_mesh_BVH'].values()) for x in f)]}
    for x in f:
        assert x['fixed_vertex_animation_displacement']==0
        for k in ['edges_over_1_5','triangles_below_0_35','triangles_below_0_6','triangles_above_2','rest_normal_dot_negative']:assert x['whole_body'][k]==0
assert all(not x['new_self_pairs'] and not x['new_contact_objects'] for x in s['per_time_comparison'])
image_records=[]
for n in ['RENDER_R7_static.json','RENDER_R8C_static.json','RENDER_R7_hip.json','RENDER_R8C_hip.json']:
    d=read(n)
    for r in d['renders']:
        assert sha(R8/r['file'])==r['sha256'];Image.open(R8/r['file']).verify();image_records.append(r['file'])
for mode in ['static','hip']:
    a=read('RENDER_R7_'+mode+'.json');b=read('RENDER_R8C_'+mode+'.json')
    assert len(a['renders'])==len(b['renders'])
    for x,y in zip(a['renders'],b['renders']):
        for key in ['frame','view','camera_matrix','ortho_scale']:assert x[key]==y[key],key
captures=[]
for n in ['MCP_CAPTURE_C_static.json','MCP_CAPTURE_C_motion_1_12.json','MCP_CAPTURE_C_motion_13_23_RECOVERED.json','MCP_CAPTURE_C_motion_24_24.json']:
    records=read(n)
    if isinstance(records,dict):records=records['captures']
    for r in records:
        assert sha(R8/r['file'])==r['sha256'];Image.open(R8/r['file']).verify();captures.append(r)
motion=[r for r in captures if r['detail'] and r['view']=='SIDE']
assert sorted(r['time'] for r in motion)==[1+i*.5 for i in range(47)]
protected=read('START_PROTECTION.json')['files']
for p,record in protected.items(): assert sha(REPO/p)==record['sha256'],p
viewed=['R7_R8C_STATIC_FIVE_VIEWS.png','R7_R8C_STATIC_128PX.png','REFERENCE_R7_R8C_PELVIS.png','REFERENCE_R7_R8C_SIDE_SILHOUETTE.png','R7_R8C_SIDE_HIP_FIVE_POSES.png','R7_R8C_REAR_BACK_THREE_POSES.png','R8C_INTEGER_FRAMES_VIEWPORT.png','R8C_HALF_FRAMES_VIEWPORT.png']
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':remote['commit'],
 'remote_bytes_report':'R8C_REMOTE_BYTE_VERIFY.json','no_R8_model_or_image_recreated':True,
 'saved_final_files_match_deformation_evidence':True,'sample_times':times,'summaries':summary,
 'minimum_per_time_area_delta':min(s['per_time_comparison'],key=lambda x:x['min_area_delta']),
 'new_self_pairs_or_contact_objects':False,'render_files_hash_verified':len(image_records),
 'matched_R7_R8C_render_cameras':True,'viewport_files_hash_verified':len(captures),
 'side_viewport_times':[r['time'] for r in motion],'pre_R8_protected_files_hash_verified':len(protected),
 'actually_viewed_comparison_images':{p:sha(R8/'comparisons'/p) for p in viewed},
 'primary_reference_sha256':sha(REPO/'art/s-creature/references/00_s_type_modeling_image_v1.png'),
 'static_decision':'REVISE','deformation_decision':'REVISE','production_promotion':False,
 'limits':['Finite 93 samples, not continuous collision proof.','Rest-normal signs do not prove absence of every inversion.','Four pre-existing self-overlap pairs and 240–242 attachment contacts remain.','No true run gait, foot contact, PC/mobile runtime acceptance.','No matching original REAR34 view or calibrated reference silhouette IoU.']}
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['render_files_hash_verified','viewport_files_hash_verified','pre_R8_protected_files_hash_verified','static_decision','deformation_decision']}))
