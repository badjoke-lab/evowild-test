"""Reopen saved R8C/R9A rigs in an independent Blender process; inspect 93 times.

All 24 integer frames and quarter-frame samples receive strain AND BVH checks.
BVH overlaps and reference-normal signs remain diagnostics, not a continuous
collision-free-motion proof. Animation is the inherited hip test, not a gait.
"""
import bpy,bmesh,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
VARIANT='A'
SUFFIX=''
OUT=ROOT/('evidence/INDEPENDENT_R8C_R9A'+SUFFIX+'_SWEEP.json');assert not OUT.exists()
def signature(o):
    m=o.data
    return hashlib.sha256(repr(([tuple(v.co) for v in m.vertices],
      [(tuple(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],
      [(a.name,a.domain,a.data_type,[tuple(d.color) for d in a.data]) for a in m.color_attributes],
      [list(r) for r in o.matrix_world],[ma.name for ma in m.materials])).encode()).hexdigest()
def eval_points(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
    p=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return p
def base(r,e,t):
    c=np.cross(r[t[:,1]]-r[t[:,0]],r[t[:,2]]-r[t[:,0]])
    return np.linalg.norm(r[e[:,1]]-r[e[:,0]],axis=1),c,np.linalg.norm(c,axis=1)
def metric(p,e,t,den):
    le,c0,a0=den
    er=np.linalg.norm(p[e[:,1]]-p[e[:,0]],axis=1)/le
    c=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]])
    ar=np.linalg.norm(c,axis=1)/a0
    return {'edge_max':float(er.max()),'edge_min':float(er.min()),'edge_p99':float(np.quantile(er,.99)),
      'area_min':float(ar.min()),'area_max':float(ar.max()),'area_p01':float(np.quantile(ar,.01)),
      'edges_over_1_5':int((er>1.5).sum()),'triangles_below_0_35':int((ar<.35).sum()),
      'triangles_below_0_6':int((ar<.6).sum()),'triangles_above_2':int((ar>2).sum()),
      'rest_normal_dot_negative':int((np.sum(c*c0,axis=1)<0).sum())}
records={}; arrays={}; protections={}; rigs={}; mesh_faces={}
for label,source in [('R8C',ROOT/'protected/S_ZERO_R8C_RIG_PROTECTED.blend'),('R9A',ROOT/'verification/S_ZERO_R9A_FORM_TRIAL.blend')]:
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    sc=bpy.context.scene;sc.frame_set(1)
    body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=body.data
    rest=np.array([v.co[:] for v in m.vertices]);edges=np.array([e.vertices[:] for e in m.edges])
    m.calc_loop_triangles(); actual_tris=np.array([t.vertices[:] for t in m.loop_triangles])
    # A common triangulation is required for meaningful before/after strain.
    tris=actual_tris if label=='R8C' else arrays['R8C']['tris']
    mesh_faces[label]=[tuple(p.vertices) for p in m.polygons]
    weights=np.zeros((len(rest),len(body.vertex_groups)))
    for v in m.vertices:
        for g in v.groups:weights[v.index,g.group]=g.weight
    objects=[o for o in bpy.data.collections['S_ZERO_CREATURE'].objects if o.type=='MESH']
    protections[label]={o.name:signature(o) for o in objects if o!=body}
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    rigs[label]={'bones':[(bn.name,list(bn.head_local),list(bn.tail_local),[list(r) for r in bn.matrix_local]) for bn in rig.data.bones],
      'action':[(fc.data_path,fc.array_index,[(list(k.co),list(k.handle_left),list(k.handle_right),k.interpolation) for k in fc.keyframe_points]) for fc in rig.animation_data.action.fcurves]}
    reference=rest if label=='R8C' else arrays['R8C']['rest']
    x,y,z=reference.T
    hip=(x>.20)&(x<1.40)&(z>1.10)&(z<2.10)&~((x>1.07)&(z>1.78-.75*(x-1.12)))
    he=edges[np.all(hip[edges],axis=1)];ht=tris[np.all(hip[tris],axis=1)]
    contact_tris=tris[np.any(hip[tris],axis=1)]
    tri_list=tris.tolist(); sets=[set(t) for t in tri_list]
    den=base(rest,edges,tris);hden=base(rest,he,ht)
    bm=bmesh.new();bm.from_mesh(m)
    topology={'vertices':len(m.vertices),'edges':len(m.edges),'polygons':len(m.polygons),'triangles':len(tris),
      'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
      'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)};bm.free()
    others=[]
    for ob in objects:
        if ob==body:continue
        p=np.array([list(ob.matrix_world@v.co) for v in ob.data.vertices]);lo,hi=p.min(axis=0),p.max(axis=0)
        if hi[0]<.18 or lo[0]>1.4 or hi[2]<1.1 or lo[2]>2.12:continue
        ob.data.calc_loop_triangles();others.append((ob,[t.vertices[:] for t in ob.data.loop_triangles]))
    frames=[]
    for time in np.linspace(1,24,93):
        f=int(time);sc.frame_set(f,subframe=float(time-f));bpy.context.view_layer.update()
        p=eval_points(body)
        tree=BVHTree.FromPolygons(p.tolist(),tri_list,all_triangles=True,epsilon=0.)
        pairs=sorted({tuple(sorted((i,j))) for i,j in tree.overlap(tree) if i!=j and not sets[i]&sets[j]})
        localtree=BVHTree.FromPolygons(p.tolist(),contact_tris.tolist(),all_triangles=True,epsilon=0.)
        contacts={}
        for ob,ot in others:
            q=[list(ob.matrix_world@Vector(v)) for v in eval_points(ob)]
            other=BVHTree.FromPolygons(q,ot,all_triangles=True,epsilon=0.)
            overlap=localtree.overlap(other)
            if overlap:contacts[ob.name]=len(overlap)
        frames.append({'time':float(time),'whole_body':metric(p,edges,tris,den),'hip':metric(p,he,ht,hden),
          'fixed_vertex_animation_displacement':float(np.linalg.norm(p[weights[:,0]==1]-rest[weights[:,0]==1],axis=1).max()),
          'contacts':{'whole_body_nonadjacent_triangle_BVH':len(pairs),'candidate_self_pairs':pairs,'hip_to_other_mesh_BVH':contacts}})
        if f in [1,6,12,18,24] and time==f:print('SWEEP',label,time,frames[-1]['whole_body']['edge_max'],frames[-1]['whole_body']['area_min'],len(pairs),flush=True)
    arrays[label]={'rest':rest,'edges':edges,'tris':tris,'weights':weights,'actual_tris':actual_tris}
    records[label]={'source':str(source.relative_to(ROOT)),'sha256':sha,'topology':topology,'frames':frames,
      'actual_tessellation_matches_common':bool(np.array_equal(actual_tris,tris)),'contact_other_objects':[o.name for o,t in others]}
    assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
assert protections['R8C']==protections['R9A'] and rigs['R8C']==rigs['R9A']
assert mesh_faces['R8C']==mesh_faces['R9A']
assert np.array_equal(arrays['R8C']['weights'],arrays['R9A']['weights'])
assert np.array_equal(arrays['R8C']['edges'],arrays['R9A']['edges'])
d=arrays['R9A']['rest']-arrays['R8C']['rest'];shift=np.linalg.norm(d,axis=1);changed=shift>0
static=metric(arrays['R9A']['rest'],arrays['R8C']['edges'],arrays['R8C']['tris'],base(arrays['R8C']['rest'],arrays['R8C']['edges'],arrays['R8C']['tris']))
comparisons=[]
for a,b in zip(records['R8C']['frames'],records['R9A']['frames']):
    comparisons.append({'time':a['time'],'max_edge_delta':b['whole_body']['edge_max']-a['whole_body']['edge_max'],
      'min_area_delta':b['whole_body']['area_min']-a['whole_body']['area_min'],
      'new_self_pairs':[p for p in b['contacts']['candidate_self_pairs'] if p not in a['contacts']['candidate_self_pairs']],
      'new_contact_objects':sorted(set(b['contacts']['hip_to_other_mesh_BVH'])-set(a['contacts']['hip_to_other_mesh_BVH']))})
projection={}
for view in ['SIDE','FRONT','FRONT34','REAR34','BACK']:
    cam=bpy.data.objects['CAM_'+view];rot=np.array(cam.matrix_world.to_quaternion().inverted().to_matrix())
    scr=d@rot.T
    projection[view]={'max_displacement_at_128px_vertical':float(np.linalg.norm(scr[:,:2],axis=1).max()*128/cam.data.ortho_scale)}
report={'blender':bpy.app.version_string,'variant':VARIANT,'independent_process':True,'records':records,'same_body_topology':True,
 'protected_other_meshes_exact':len(protections['R8C']),'weights_bones_keyframes_exact':True,'static_vs_R8C':static,
 'moved_vertices':int(changed.sum()),'max_displacement':float(shift.max()),
 'moved_bounds':[arrays['R9A']['rest'][changed].min(axis=0).tolist(),arrays['R9A']['rest'][changed].max(axis=0).tolist()],
 'unchanged_body_vertices':int((~changed).sum()),'per_time_comparison':comparisons,'camera_projection_bounds':projection,
 'limitations':'93 finite samples of the inherited hip-only test. No running gait/foot-contact or PC/mobile runtime acceptance. Reference-normal signs and triangle BVH overlaps are diagnostics.'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('AUDIT_COMPLETE',{'edge_worsen_max':max(x['max_edge_delta'] for x in comparisons),'area_worsen_min':min(x['min_area_delta'] for x in comparisons),
 'new_self_pairs':sum(len(x['new_self_pairs']) for x in comparisons),'new_contact_objects':sum(len(x['new_contact_objects']) for x in comparisons)},flush=True)
