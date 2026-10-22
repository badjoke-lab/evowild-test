"""Independent saved-file sweep; exact protection checks and MCP screenshots.

93 quarter-frame samples for strain; all 24 integer frames for surface contacts.
BVH counts are numerical diagnostics, not a proof of collision-free motion.
"""
import bpy,bmesh,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/INDEPENDENT_R6_R7_SWEEP.json';assert not OUT.exists()
sources={'R6':ROOT/'protected/S_ZERO_R6_RIG_PROTECTED.blend','R7':ROOT/'verification/S_ZERO_R7_HIP_TRIAL_A.blend'}

def signature(o):
    return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],
     [(tuple(p.vertices),p.material_index,p.use_smooth) for p in o.data.polygons],
     [(a.name,a.domain,a.data_type,[tuple(d.color) for d in a.data]) for a in o.data.color_attributes],
     [list(r) for r in o.matrix_world],[mat.name if mat else None for mat in o.data.materials])).encode()).hexdigest()

def weight_array(ob):
    w=np.zeros((len(ob.data.vertices),len(ob.vertex_groups)))
    for v in ob.data.vertices:
        for g in v.groups:w[v.index,g.group]=g.weight
    return w

def eval_points(ob):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    p=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();return p

def metric(rest,p,e,t):
    length=np.linalg.norm(rest[e[:,1]]-rest[e[:,0]],axis=1)
    er=np.linalg.norm(p[e[:,1]]-p[e[:,0]],axis=1)/length
    before=np.cross(rest[t[:,1]]-rest[t[:,0]],rest[t[:,2]]-rest[t[:,0]])
    after=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]])
    ar=np.linalg.norm(after,axis=1)/np.linalg.norm(before,axis=1)
    return {'edge_max':float(er.max()),'edge_min':float(er.min()),'edge_p99':float(np.quantile(er,.99)),
     'area_min':float(ar.min()),'area_max':float(ar.max()),'area_p01':float(np.quantile(ar,.01)),
     'edges_over_1_5':int((er>1.5).sum()),'triangles_below_0_35':int((ar<.35).sum()),
     'triangles_below_0_6':int((ar<.6).sum()),'triangles_above_2':int((ar>2).sum()),
     'rest_normal_dot_negative':int((np.sum(before*after,axis=1)<0).sum())}

records={};arrays={};captures=[];protected={};rig_signature={}
for label,source in sources.items():
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data;sc=bpy.context.scene
    sc.frame_set(1);bpy.context.view_layer.update()
    rest=np.array([v.co[:] for v in m.vertices]);edges=np.array([e.vertices[:] for e in m.edges])
    m.calc_loop_triangles();tris=np.array([t.vertices[:] for t in m.loop_triangles])
    weights=weight_array(b)
    objects=[o for o in bpy.data.collections['S_ZERO_CREATURE'].objects if o.type=='MESH']
    protected[label]={o.name:signature(o) for o in objects if o!=b}
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    rig_signature[label]={'bones':[(bn.name,list(bn.head_local),list(bn.tail_local),[list(r) for r in bn.matrix_local]) for bn in rig.data.bones],
     'action':[(fc.data_path,fc.array_index,[(list(k.co),list(k.handle_left),list(k.handle_right),k.interpolation) for k in fc.keyframe_points]) for fc in rig.animation_data.action.fcurves]}
    x,y,z=rest.T;hip=(x>.20)&(x<1.35)&(z>1.10)&(z<2.10)&~((x>1.07)&(z>1.78-.75*(x-1.12)))
    he=edges[np.all(hip[edges],axis=1)];ht=tris[np.all(hip[tris],axis=1)]
    contact_tris=tris[np.any(hip[tris],axis=1)]
    sets=[set(t) for t in tris.tolist()];tri_list=tris.tolist()
    bm=bmesh.new();bm.from_mesh(m)
    topology={'vertices':len(m.vertices),'edges':len(m.edges),'polygons':len(m.polygons),'triangles':len(tris),
     'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
     'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)};bm.free()
    others=[]
    for ob in objects:
        if ob==b:continue
        coords=np.array([list(ob.matrix_world@v.co) for v in ob.data.vertices])
        low,high=coords.min(axis=0),coords.max(axis=0)
        if high[0]<.18 or low[0]>1.4 or high[2]<1.10 or low[2]>2.12:continue
        ob.data.calc_loop_triangles()
        others.append((ob,[t.vertices[:] for t in ob.data.loop_triangles]))
    frames=[];sampled={}
    for time in np.linspace(1,24,93):
        frame=int(time);sub=float(time-frame);sc.frame_set(frame,subframe=sub);bpy.context.view_layer.update()
        p=eval_points(b)
        r={'time':float(time),'whole_body':metric(rest,p,edges,tris),'hip':metric(rest,p,he,ht),
         'fixed_vertex_max_displacement':float(np.linalg.norm(p[weights[:,0]==1]-rest[weights[:,0]==1],axis=1).max())}
        if sub==0:
            tree=BVHTree.FromPolygons(p.tolist(),tri_list,all_triangles=True,epsilon=0.)
            pairs={tuple(sorted((i,j))) for i,j in tree.overlap(tree) if i!=j and not sets[i]&sets[j]}
            localtree=BVHTree.FromPolygons(p.tolist(),contact_tris.tolist(),all_triangles=True,epsilon=0.)
            contacts={}
            for ob,ot in others:
                q=eval_points(ob)
                q=[list(ob.matrix_world@Vector(v)) for v in q]
                bt=BVHTree.FromPolygons(q,ot,all_triangles=True,epsilon=0.)
                pairs_other=localtree.overlap(bt)
                if pairs_other:contacts[ob.name]=len(pairs_other)
            r['contacts']={'whole_body_nonadjacent_triangle_BVH':len(pairs),'hip_to_other_mesh_BVH':contacts,
              'candidate_self_pairs':sorted(pairs)[:20]}
            sampled[frame]=p
        frames.append(r)
    arrays[label]={'rest':rest,'edges':edges,'tris':tris,'weights':weights,'sampled':sampled}
    records[label]={'source':str(source.relative_to(ROOT)),'source_sha256':sha,'topology':topology,
     'weights_sum_range':[float(weights.sum(axis=1).min()),float(weights.sum(axis=1).max())],
     'contact_other_objects':[o.name for o,t in others],'frames':frames}
    if label=='R7':
        window=bpy.context.window_manager.windows[0];area=next(a for a in window.screen.areas if a.type=='VIEW_3D')
        region=next(r for r in area.regions if r.type=='WINDOW');sp=area.spaces.active
        sp.overlay.show_overlays=False;sp.shading.type='SOLID';sp.shading.color_type='MATERIAL';sp.shading.light='STUDIO'
        sp.shading.show_shadows=True;sp.shading.show_cavity=True
        with bpy.context.temp_override(window=window,area=area,region=region):
            for f in [1,6,12,18,24]:
                sc.frame_set(f)
                for view in ['SIDE','REAR34','BACK']:
                    sp.region_3d.view_perspective='ORTHO';sp.region_3d.view_location=Vector((.80,0,1.52));sp.region_3d.view_distance=2.5
                    sp.region_3d.view_rotation=bpy.data.objects['CAM_'+view].matrix_world.to_quaternion()
                    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)
                    path=ROOT/'viewport'/('R7_F%02d_%s.png'%(f,view));assert not path.exists()
                    result=bpy.types.blendermcp_server.get_viewport_screenshot(max_size=1200,filepath=str(path),format='png')
                    assert result.get('success'),result
                    captures.append({'frame':f,'view':view,'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'result':result})
    assert hashlib.sha256(source.read_bytes()).hexdigest()==sha

r6,r7=arrays['R6'],arrays['R7']
assert np.array_equal(r6['edges'],r7['edges']) and np.array_equal(r6['tris'],r7['tris'])
assert protected['R6']==protected['R7'] and rig_signature['R6']==rig_signature['R7']
delta=np.linalg.norm(r7['rest']-r6['rest'],axis=1)
fixed=np.max(r6['weights'],axis=1)==1
assert np.array_equal(r6['weights'][fixed],r7['weights'][fixed])
assert np.array_equal(r6['rest'][r6['weights'][:,0]==1],r7['rest'][r6['weights'][:,0]==1])
common={}
for f in [1,6,12,18,24]:
    common[str(f)]=metric(r6['rest'],r7['sampled'][f],r6['edges'],r6['tris'])
report={'blender':bpy.app.version_string,'records':records,'same_topology':True,
 'protected_meshes_exact':len(protected['R6']),'rig_bones_action_exact':True,'rigid_weights_exact':True,
 'body_fixed_vertices_exact':int((r6['weights'][:,0]==1).sum()),'moved_rest_vertices':int((delta>0).sum()),
 'max_rest_displacement':float(delta.max()),'R7_using_original_R6_rest_denominators':common,
 'limits':'93 time samples, including all 24 integer frames. No locomotion, ground contact or runtime approval. BVH overlaps and rest-normal dots are diagnostics, not continuous-time collision or inversion proofs.'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
(ROOT/'evidence/MCP_R7_CAPTURES.json').write_text(json.dumps(captures,indent=2)+'\n')
for label,record in records.items():
    print(label,'worst_edge',max(r['whole_body']['edge_max'] for r in record['frames']),
     'worst_area',min(r['whole_body']['area_min'] for r in record['frames']),
     'self_BVH',max(r['contacts']['whole_body_nonadjacent_triangle_BVH'] for r in record['frames'] if 'contacts' in r),
     'other_BVH',[(r['time'],r['contacts']['hip_to_other_mesh_BVH']) for r in record['frames'] if r.get('contacts',{}).get('hip_to_other_mesh_BVH')])
print('R7_INDEPENDENT_SWEEP_AND_MCP_CAPTURES_COMPLETE')
