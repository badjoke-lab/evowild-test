"""Stage-2 candidate search on genuine V5 Stage-1 S Hunyuan (Blender 4.3.2).

No edits to any source .blend. Reverse-face-causing original rejected proposal
is scaled & subdivided, with face-area/normal tests at float32 precision.
One technically safe visual *candidate*, never automatic artistic KEEP.
"""
import bpy, hashlib, json, sys
from pathlib import Path
import numpy as np
from mathutils import Vector

ROOT=Path.cwd()
ST=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
V3=ST/'review-v3/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend'
V4=ST/'review-v4/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend'
ST1=ST/'review-v5/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_STAGE1.blend'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
REJECT=ST/'review-v5/STAGE2_REJECTED_PROPOSAL.npz'
REJECT_JSON=ST/'review-v5/STAGE2_REJECTED_PREFLIGHT.json'
O=ST/'review-v5-stage2-candidate';O.mkdir(parents=True,exist_ok=True)
OUTPUT=O/'S_HUNYUAN_SHOULDER_CHEST_V5_STAGE2_CANDIDATE_UNAPPROVED.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p.relative_to(ROOT)):sha(p) for p in (V3,V4,ST1,REF)}
assert protected[str(V3.relative_to(ROOT))]=='820f6ade08f626db7d163dade691fd03e6fa54aa75e8d43ae38ef617252623ec'
assert protected[str(V4.relative_to(ROOT))]=='38efa5c29e5ac7b1a6a6afba1256d498763e0f8d3b8e7435d9b38b4b183e879e'
assert protected[str(ST1.relative_to(ROOT))]=='96b1bbc709f1db0dcd559540e28bd79d3863cfcc73ea2a5d916a020108a91f53'
assert protected[str(REF.relative_to(ROOT))]=='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert bpy.app.version[:3]==(4,3,2)

bpy.ops.wm.open_mainfile(filepath=str(ST1))
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.data.name=='geometry_0')
assert len(body.data.vertices)==38802 and len(body.data.polygons)==77684
mesh=body.data
base=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
faces=np.array([p.vertices[:] for p in mesh.polygons],dtype=np.int32)
with bpy.data.libraries.load(str(V3),link=False) as (src,dst):
    assert 'geometry_0' in src.meshes
    dst.meshes=['geometry_0']
refmesh=dst.meshes[0]
v3=np.array([v.co[:] for v in refmesh.vertices],dtype=np.float32)
assert np.array_equal(faces,np.array([p.vertices[:] for p in refmesh.polygons],dtype=np.int32))
bpy.data.meshes.remove(refmesh)
rj=json.loads(REJECT_JSON.read_text())
assert rj['status']=='REJECTED_BEFORE_MESH_MUTATION' and rj['new_reversed_faces']==7
npz=np.load(REJECT,allow_pickle=False)
indices=npz['indices'].astype(np.int32)
target=npz['coordinates'].astype(np.float32)
assert np.array_equal(np.sort(indices),indices)
delta=np.zeros_like(base)
delta[indices]=target-base[indices]
assert int(np.count_nonzero(np.any(delta!=0,axis=1)))==498
categories={}
for patch in rj['patches']:
    k=patch['kind'];categories.setdefault(k,set()).update(int(v) for v in patch['vertices'])
names={
 'oblique_only':categories['upper_oblique'],
 'pectoral_only':categories['pectoral_inset'],
 'combined':set(indices.tolist()),
}
def face_geometry(v):
    p=v.astype(np.float64)
    n=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
    return n,np.linalg.norm(n,axis=1)
n0,a0=face_geometry(base)
n3,a3=face_geometry(v3)
eligible=(a3>1e-12)&(a0>1e-12)
area_before=np.ones(len(faces),dtype=np.float64)
area_before[eligible]=a0[eligible]/a3[eligible]
minimum_base=float(area_before[eligible].min())
assert abs(minimum_base-0.32293604)<1e-5,minimum_base
world=np.array([(body.matrix_world@Vector(p))[:] for p in base],dtype=np.float64)
center=(world[faces[:,0]]+world[faces[:,1]]+world[faces[:,2]])/3
scope=(center[:,1]>-.59)&(center[:,1]<-.045)&(center[:,2]>-.4)&(center[:,2]<.25)
count_before=int(np.count_nonzero(eligible&scope&(area_before<.45)))
assert count_before==23,count_before
front=(world[:,1]>-.53)&(world[:,1]<-.29)&(world[:,2]>-.08)&(world[:,2]<.14)
frontwidth=lambda arr:float(np.diff(np.quantile(arr[front,0],[.025,.975]))[0])
width_before=frontwidth(base)
records=[]
winner=None
for kind,chosen in names.items():
    mask=np.zeros(len(base),dtype=np.float32);mask[list(chosen)]=1
    for alpha in (.025,.04,.06,.08,.10,.12,.15,.18,.22,.26,.30,.38,.45,.55):
        proposed=(base.astype(np.float64)+alpha*delta*mask[:,None]).astype(np.float32)
        changed=np.any(base!=proposed,axis=1)
        if not np.any(changed):continue
        n1,a1=face_geometry(proposed)
        surviving=eligible&(a1>1e-12)
        flips=int(np.count_nonzero((np.sum(n0*n1,axis=1)<=0)&surviving))
        newdegen=int(np.count_nonzero((a0>1e-12)&(a1<=1e-12)))
        ratio=np.ones(len(faces),dtype=np.float64);ratio[surviving]=a1[surviving]/a3[surviving]
        minratio=float(ratio[surviving].min())
        shrunk=int(np.count_nonzero(surviving&scope&(ratio<.45)))
        local_move=float(np.linalg.norm(proposed-base,axis=1).max())
        newwidth=frontwidth(proposed)
        area_gate=(minratio>=minimum_base-.001 and shrunk<=count_before)
        ok=flips==0 and newdegen==0 and area_gate and local_move<=.004 and abs(newwidth-width_before)<.001
        row=dict(kind=kind,alpha=alpha,changed_vertices=int(changed.sum()),
                 maximum_local_displacement=local_move,minimum_v3_face_area_ratio=minratio,
                 shoulder_faces_under_0_45=shrunk,new_face_reversals=flips,
                 new_degenerate_faces=newdegen,front_width=newwidth,
                 numerical_gate='PASS' if ok else 'REJECT')
        records.append(row)
        if ok:
            # Favor oblique shoulder contour (the unsolved artistic concern)
            # without rewarding aggressive amplitudes over geometry safety.
            value=(5 if kind=='oblique_only' else (3 if kind=='combined' else 0))+alpha*5-(count_before-shrunk)*.15
            if winner is None or value>winner[0]:
                winner=(value,row,proposed)
report=dict(status='CANDIDATE_SEARCH_ONLY_NOT_ARTISTIC_KEEP',
            source_stage1_sha=sha(ST1),reference_sha=sha(REF),
            blender=bpy.app.version_string,faces=int(len(faces)),vertices=int(len(base)),
            original_rejected_flips=7,original_rejected_min_v3_area_ratio=0.03089278146,
            accepted_stage1_min_area_ratio=minimum_base,
            accepted_stage1_shrunk_face_count=count_before,front_width_stage1=width_before,
            attempts=len(records),passing=sum(r['numerical_gate']=='PASS' for r in records),
            trials=records,protected_sha256=protected,
            assertion='Cannot claim sculpt improvement until real images viewed.')
if winner is None:
    report['outcome']='NO_SAFE_CANDIDATE; Stage1 remains latest saved version'
else:
    _,best,coords=winner
    report['winner']=best
    # Write a real new mesh candidate, but only after numerical checks; it
    # remains separate and UNAPPROVED, never replaces Stage1.
    for v,p in zip(mesh.vertices,coords):v.co=p
    mesh.update()
    body['artistic_approval']='NO - STAGE2 EXPERIMENT ONLY'
    body['stage2_test']='Reject/keep requires visual review against original illustration.'
    bpy.context.scene['full_creature_modeling_approved']=False
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(OUTPUT))
    body=next(o for o in bpy.data.objects if o.type=='MESH' and o.data.name=='geometry_0')
    final=np.array([v.co[:] for v in body.data.vertices],dtype=np.float32)
    assert np.array_equal(final,coords)
    assert np.array_equal(faces,np.array([p.vertices[:] for p in body.data.polygons],dtype=np.int32))
    report['candidate_blend']=str(OUTPUT.relative_to(ROOT))
    report['candidate_sha256']=sha(OUTPUT)
    report['outcome']='REAL_SAVED_UNAPPROVED_VISUAL_CANDIDATE'
    # Reuse exactly the Stage1 render setup in memory for matched camera/lights.
    # It references only the current bpy.data.filepath and geometry_0.
    renderer=(ROOT/'art/s-creature/blender/s_hunyuan_v5_stage1_render.py').read_text()
    renderer=renderer.replace("elif VERSION!='V5_STAGE1':", "elif VERSION not in ('V5_STAGE1','V5_STAGE2_CANDIDATE'):")
    renderer=renderer.replace("base=np.load(OUT.parent/'review-v4/V3_BASE_COORDS.npy').astype(np.float32)", "base=__V3_BASE_COORDS.astype(np.float32)")
    assert "base=__V3_BASE_COORDS.astype(np.float32)" in renderer
    assert "VERSION not in ('V5_STAGE1','V5_STAGE2_CANDIDATE')" in renderer
    for tag in ('SIDE','FRONT','FRONT34'):
        # render exact same 1000x800 ortho/CPU scene as Stage1 detail
        exec(compile(renderer,'same-camera-V5-stage1-render.py','exec'),{'TAG':tag,'DETAIL':True,'VERSION':'V5_STAGE2_CANDIDATE','__V3_BASE_COORDS':v3})
        assert (O/('V5_STAGE2_CANDIDATE_DETAIL_'+tag+'.png')).is_file()
    report['rendered_detail_views']=['SIDE','FRONT','FRONT34']
assert {str(p.relative_to(ROOT)):sha(p) for p in (V3,V4,ST1,REF)}==protected
(O/'STAGE2_BOUNDED_SEARCH_AND_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print('S_V5_STAGE2_BOUNDED_SEARCH_COMPLETE',json.dumps({k:v for k,v in report.items() if k not in ('trials','protected_sha256')}),flush=True)
