"""Independent reload audit; compare old/new deformation on identical edge IDs.

Also test the entire body so defects cannot be hidden outside the hip ROI.
No model is saved or modified on disk.
"""
import bpy,hashlib,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'verification/S_ZERO_R6_HIP_DEFORMATION_TEST_B.blend'
NEW=ROOT/'verification/S_ZERO_R6_HIP_DEFORMATION_RECOVERED_C.blend'
OUT=ROOT/'evidence/INDEPENDENT_SAVED_DEFORMATION.json'
assert not OUT.exists()
hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OLD,NEW]}
data={}
for label,path in [('before',OLD),('after',NEW)]:
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
    b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data
    rest=np.array([v.co[:] for v in m.vertices],dtype=np.float64)
    edges=np.array([e.vertices[:] for e in m.edges],dtype=np.int64)
    m.calc_loop_triangles();tris=np.array([t.vertices[:] for t in m.loop_triangles])
    states={}
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    for state,frame in [('NEUTRAL',1),('NEAR_FORWARD',12),('NEAR_BACK',24)]:
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());posed_mesh=ev.to_mesh()
        states[state]=np.array([v.co[:] for v in posed_mesh.vertices],dtype=np.float64)
        ev.to_mesh_clear()
    data[label]={'rest':rest,'edges':edges,'tris':tris,'states':states,
        'weights_min_sum':min(sum(g.weight for g in v.groups) for v in m.vertices),
        'weights_max_sum':max(sum(g.weight for g in v.groups) for v in m.vertices),
        'pose_frames':[p.co.x for fc in rig.animation_data.action.fcurves for p in fc.keyframe_points]}
assert np.array_equal(data['before']['rest'],data['after']['rest'])
rest=data['after']['rest'];x,y,z=rest.T
hip=(x>.20)&(x<1.35)&(z>1.10)&(z<2.10)&~((x>1.07)&(z>1.78-.75*(x-1.12)))
common_edges=data['before']['edges']
common_edges=common_edges[np.all(hip[common_edges],axis=1)]
common_tris=data['after']['tris']
common_tris=common_tris[np.all(hip[common_tris],axis=1)]
def metric(pos,edges,tris):
    length=np.linalg.norm(rest[edges[:,1]]-rest[edges[:,0]],axis=1)
    er=np.linalg.norm(pos[edges[:,1]]-pos[edges[:,0]],axis=1)/length
    before=np.cross(rest[tris[:,1]]-rest[tris[:,0]],rest[tris[:,2]]-rest[tris[:,0]])
    after=np.cross(pos[tris[:,1]]-pos[tris[:,0]],pos[tris[:,2]]-pos[tris[:,0]])
    area=np.linalg.norm(before,axis=1);valid=area>=1e-9
    ar=np.linalg.norm(after[valid],axis=1)/area[valid]
    return {'edge_count':len(edges),'triangle_count':len(tris),'excluded_rest_triangles':int((~valid).sum()),
        'edge_max':float(er.max()),'edge_min':float(er.min()),'edges_over_1_5':int((er>1.5).sum()),
        'area_min':float(ar.min()),'area_max':float(ar.max()),'triangles_below_0_35':int((ar<.35).sum()),
        'rest_normal_dot_negative':int((np.sum(before[valid]*after[valid],axis=1)<0).sum())}
records={}
for label,d in data.items():
    records[label]={'weights_sum_range':[d['weights_min_sum'],d['weights_max_sum']],'states':{}}
    for state,pos in d['states'].items():
        e=d['edges'];t=d['tris']
        native=metric(pos,e[np.all(hip[e],axis=1)],t[np.all(hip[t],axis=1)])
        common=metric(pos,common_edges,common_tris)
        whole=metric(pos,e,t)
        records[label]['states'][state]={'native_hip':native,'same_original_edges_and_corrected_triangles':common,'whole_body':whole}
        print(label,state,'native',native['edge_max'],native['area_min'],'common',common['edge_max'],common['area_min'],'whole',whole['edge_max'],whole['area_min'])
for p in [OLD,NEW]:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p)]
out={'blender':bpy.app.version_string,'source_hashes':hashes,'rest_coordinates_exact':True,
     'comparison_method':'Original B edge IDs for both models; corrected C triangle indices for common-tessellation area comparison. Native and whole-body metrics also retained.',
     'records':records,'limits':'Only saved frames 1/12/24; no gait, ground contact, intermediate-frame sweep or runtime approval. Negative rest-normal dot is diagnostic only.'}
OUT.write_text(json.dumps(out,indent=2)+'\n')
