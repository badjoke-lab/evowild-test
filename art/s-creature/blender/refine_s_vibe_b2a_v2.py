"""Experimental Vibe Gate B2a-v2: locally refined proximal forelimb root.

Source: S-vibe-b1c-v2.blend.

Single hypothesis:
B2a-v1 showed the accepted A3a station0->station1 elliptical guide is valid,
but the existing root topology does not have enough degrees of freedom.
Subdivide only fully-contained same-side station0->station1 faces once, then
apply the same tapered elliptical guide on that refined local patch.

No object-wide remesh. B2b remains blocked.
"""
import bpy, bmesh, os, json, hashlib, math
from collections import Counter
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

# Accepted A3a station0 -> station1 landmarks.
S0_X,S0_Y,S0_Z=0.115,-0.030,0.985
S0_LR,S0_SR=0.068,0.095
S1_X,S1_Y,S1_Z=0.148,0.035,0.845
S1_LR,S1_SR=0.056,0.070

# B2a root support.
XMIN,XMAX=0.055,0.215
YMIN,YMAX=-0.075,0.085
ZMIN,ZMAX=0.780,1.060
SUPPORT_EPS=1e-5

Q_ERROR_THRESHOLD=0.10
Q_MIN=0.45
Q_MAX=1.90
GAIN=0.30
MAX_LOCAL_DISP=0.0040
MAX_EXTENT_DRIFT=0.002
MIN_NEW_VERTS=20
MAX_NEW_VERTS=500
MAX_CANDIDATES=500

src_vert_count=len(mesh.vertices)
src_poly_count=len(mesh.polygons)
src_edge_count=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def side_segment(co):
    sign=1.0 if co.x>=0 else -1.0
    s0=Vector((sign*S0_X,S0_Y,S0_Z))
    s1=Vector((sign*S1_X,S1_Y,S1_Z))
    axis=s1-s0
    denom=axis.length_squared
    assert denom>0
    t=(co-s0).dot(axis)/denom
    return sign,s0,s1,axis,t

def inside_box(co,eps=0.0):
    ax=abs(co.x)
    return (XMIN-eps)<=ax<=(XMAX+eps) and (YMIN-eps)<=co.y<=(YMAX+eps) and (ZMIN-eps)<=co.z<=(ZMAX+eps)

def inside_local(co,eps=0.0):
    if not inside_box(co,eps):
        return False
    _,_,_,_,t=side_segment(co)
    return -eps<=t<=1.0+eps

def guide_metrics(co):
    sign,s0,s1,axis,t=side_segment(co)
    center=s0+axis*t
    tangent=axis.normalized()
    lateral=Vector((1.0,0.0,0.0))
    lateral=lateral-tangent*lateral.dot(tangent)
    assert lateral.length>1e-12
    lateral.normalize()
    sagittal=tangent.cross(lateral)
    assert sagittal.length>1e-12
    sagittal.normalize()
    lr=S0_LR+(S1_LR-S0_LR)*t
    sr=S0_SR+(S1_SR-S0_SR)*t
    d=co-center
    u=d.dot(lateral)
    v=d.dot(sagittal)
    q=math.sqrt((u/lr)**2+(v/sr)**2)
    return t,center,tangent,lateral,sagittal,lr,sr,u,v,q

bm=bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()

orig_verts=list(bm.verts)
orig_coords={v:v.co.copy() for v in orig_verts}
source_outside_counter=Counter(tuple(v.co) for v in orig_verts if not inside_local(v.co,SUPPORT_EPS))
assert any(inside_local(v.co) for v in orig_verts), 'no source B2a-v2 local vertices'

eligible=[]
affected_source_faces=set()
for e in list(bm.edges):
    v0,v1=e.verts
    if not (inside_local(v0.co) and inside_local(v1.co)):
        continue
    if v0.co.x*v1.co.x<=0:
        continue
    if not e.link_faces:
        continue
    sign=1.0 if v0.co.x>0 else -1.0
    fully_local=True
    for f in e.link_faces:
        for v in f.verts:
            if not inside_local(v.co) or v.co.x*sign<=0:
                fully_local=False
                break
        if not fully_local:
            break
    if fully_local:
        eligible.append(e)
        affected_source_faces.update(e.link_faces)

assert eligible, 'no fully-contained B2a-v2 edges eligible'

bmesh.ops.subdivide_edges(
    bm,
    edges=eligible,
    cuts=1,
    use_grid_fill=True,
    smooth=0.0
)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()

new_vertex_count=len(bm.verts)-src_vert_count
assert MIN_NEW_VERTS<=new_vertex_count<=MAX_NEW_VERTS, (
    f'B2a-v2 new vertex count {new_vertex_count} outside [{MIN_NEW_VERTS},{MAX_NEW_VERTS}]'
)

outside_after_subdivide=Counter(tuple(v.co) for v in bm.verts if not inside_local(v.co,SUPPORT_EPS))
assert outside_after_subdivide==source_outside_counter, 'B2a-v2 subdivision changed coordinates/topology outside local root'

local_verts=[v for v in bm.verts if inside_local(v.co,SUPPORT_EPS)]
initial_local={v:v.co.copy() for v in local_verts}

candidates=[]
metrics={}
for v in local_verts:
    t,center,tangent,lateral,sagittal,lr,sr,u,sv,q=guide_metrics(initial_local[v])
    if not (0.0<=t<=1.0):
        continue
    metrics[v]=(t,center,tangent,lateral,sagittal,lr,sr,u,sv,q)
    if Q_MIN<=q<=Q_MAX and abs(q-1.0)>Q_ERROR_THRESHOLD:
        candidates.append(v)

assert candidates, 'no B2a-v2 guide candidates after local subdivision'
assert len(candidates)<=MAX_CANDIDATES, f'B2a-v2 candidate count {len(candidates)} > {MAX_CANDIDATES}'

q_before=[]
q_after=[]
for v in candidates:
    p=initial_local[v]
    t,center,tangent,lateral,sagittal,lr,sr,u,sv,q=metrics[v]
    if q<=1e-12:
        continue
    target=center+lateral*(u/q)+sagittal*(sv/q)
    proposed=p+(target-p)*GAIN
    delta=proposed-p
    if delta.length>MAX_LOCAL_DISP and delta.length>0:
        proposed=p+delta.normalized()*MAX_LOCAL_DISP

    if p.x>0 and proposed.x<=0: proposed.x=1e-6
    if p.x<0 and proposed.x>=0: proposed.x=-1e-6

    # target and source share the same segment t; remove numerical axial drift.
    axial=(proposed-center).dot(tangent)
    proposed=proposed-tangent*axial

    delta=proposed-p
    if delta.length>MAX_LOCAL_DISP and delta.length>0:
        proposed=p+delta.normalized()*MAX_LOCAL_DISP

    d2=proposed-center
    u2=d2.dot(lateral)
    v2=d2.dot(sagittal)
    q2=math.sqrt((u2/lr)**2+(v2/sr)**2)
    assert abs(q2-1.0)<=abs(q-1.0)+1e-7, 'B2a-v2 ellipse error increased'
    q_before.append(abs(q-1.0))
    q_after.append(abs(q2-1.0))
    v.co=proposed

# Outside local coordinate multiset stays exact.
outside_after_fair=Counter(tuple(v.co) for v in bm.verts if not inside_local(v.co,SUPPORT_EPS))
assert outside_after_fair==source_outside_counter, 'B2a-v2 fairing changed geometry outside local root'

local_disp={v:(v.co-initial_local[v]).length for v in local_verts}
vals=list(local_disp.values())
max_local_disp=max(vals) if vals else 0.0
mean_local_disp=sum(vals)/len(vals) if vals else 0.0
changed_local=sum(1 for d in vals if d>1e-10)
assert max_local_disp<=MAX_LOCAL_DISP+1e-7, f'B2a-v2 max local displacement {max_local_disp}'

nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
assert len(nonmanifold)==0, f'B2a-v2 non-manifold edges {len(nonmanifold)}'

src_ext={
 'x':(min(c.x for c in orig_coords.values()),max(c.x for c in orig_coords.values())),
 'y':(min(c.y for c in orig_coords.values()),max(c.y for c in orig_coords.values())),
 'z':(min(c.z for c in orig_coords.values()),max(c.z for c in orig_coords.values())),
}
dst_ext={
 'x':(min(v.co.x for v in bm.verts),max(v.co.x for v in bm.verts)),
 'y':(min(v.co.y for v in bm.verts),max(v.co.y for v in bm.verts)),
 'z':(min(v.co.z for v in bm.verts),max(v.co.z for v in bm.verts)),
}
extent_drift={}
for ax in ('x','y','z'):
    extent_drift[ax]=max(abs(dst_ext[ax][0]-src_ext[ax][0]),abs(dst_ext[ax][1]-src_ext[ax][1]))
    assert extent_drift[ax]<=MAX_EXTENT_DRIFT+1e-9, f'B2a-v2 {ax} extent drift {extent_drift[ax]}'

for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

bm.to_mesh(mesh)
bm.free()
mesh.update()

def outside_body_coords():
    return sorted(tuple(v.co) for v in mesh.vertices if not inside_local(v.co,SUPPORT_EPS))

def fixed_hash():
    h=hashlib.sha256()
    for co in outside_body_coords():
        h.update(repr(co).encode())
    for name in sorted(preserved_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B2a-v2-local-refined-proximal-forelimb-root',
 'source':'S-vibe-b1c-v2.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'one fully-contained local subdivision + accepted A3a tapered elliptical station0-to-station1 guide',
 'station0':{'abs_x':S0_X,'y':S0_Y,'z':S0_Z,'lateral_radius':S0_LR,'sagittal_radius':S0_SR},
 'station1':{'abs_x':S1_X,'y':S1_Y,'z':S1_Z,'lateral_radius':S1_LR,'sagittal_radius':S1_SR},
 'support':{'abs_x_min':XMIN,'abs_x_max':XMAX,'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX,'station_t':[0,1]},
 'parameters':{'subdivision_cuts':1,'q_error_threshold':Q_ERROR_THRESHOLD,'q_min':Q_MIN,'q_max':Q_MAX,
               'gain':GAIN,'max_local_displacement':MAX_LOCAL_DISP},
 'source_vertex_count':src_vert_count,
 'source_polygon_count':src_poly_count,
 'source_edge_count':src_edge_count,
 'result_vertex_count':len(mesh.vertices),
 'result_polygon_count':len(mesh.polygons),
 'result_edge_count':len(mesh.edges),
 'eligible_subdivided_edge_count':len(eligible),
 'affected_source_face_count':len(affected_source_faces),
 'new_vertex_count':new_vertex_count,
 'local_vertex_count_after_subdivision':len(local_verts),
 'candidate_vertex_count':len(candidates),
 'changed_local_vertex_count':changed_local,
 'max_local_displacement':max_local_disp,
 'mean_local_displacement':mean_local_disp,
 'mean_abs_q_error_before':sum(q_before)/len(q_before),
 'mean_abs_q_error_after':sum(q_after)/len(q_after),
 'whole_body_extent_before':src_ext,
 'whole_body_extent_after':dst_ext,
 'whole_body_extent_drift':extent_drift,
 'non_manifold_edge_count':0,
 'outside_local_vertex_count':len(outside_body_coords()),
 'fixed_geometry_hash':fixed_hash(),
 'outside_local_original_geometry_unchanged':True,
 'preserved_geometry_unchanged':True,
 'topology_change_scope':'fully-contained same-side station0-to-station1 forelimb-root faces only',
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b2a-v2-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b2a-v2.blend'),compress=True)
print('VIBE_B2A_V2_EDIT_COMPLETE',json.dumps(report))
