"""Experimental Vibe Gate B2a-v3: three-station proximal forelimb root.

Source: S-vibe-b1c-v2.blend.

Single hypothesis:
The persistent triangular forelimb root extends proximally onto the thorax side
of A3a station0. Rebuild the local support once, then shape a continuous
station-1 -> station0 -> station1 tapered elliptical root.

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

# Thorax embed station -1.
SM1_X,SM1_Y,SM1_Z=0.088,-0.070,1.035
SM1_LR,SM1_SR=0.086,0.112

# Accepted A3a station0 -> station1.
S0_X,S0_Y,S0_Z=0.115,-0.030,0.985
S0_LR,S0_SR=0.068,0.095
S1_X,S1_Y,S1_Z=0.148,0.035,0.845
S1_LR,S1_SR=0.056,0.070

XMIN,XMAX=0.055,0.215
YMIN,YMAX=-0.075,0.085
ZMIN,ZMAX=0.780,1.060
SUPPORT_EPS=1e-5
SUBDIV_INSET=0.005
MAX_SUBDIV_EDGES=360

Q_ERROR_THRESHOLD=0.10
Q_MIN=0.45
Q_MAX=1.90
GAIN=0.30
MAX_LOCAL_DISP=0.0040
MAX_EXTENT_DRIFT=0.002
MIN_NEW_VERTS=20
MAX_NEW_VERTS=500
MIN_CANDIDATES=20
MAX_CANDIDATES=240
TOP_PER_SIDE=120

src_vert_count=len(mesh.vertices)
src_poly_count=len(mesh.polygons)
src_edge_count=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def station_point(sign, which):
    if which==-1:
        return Vector((sign*SM1_X,SM1_Y,SM1_Z)),SM1_LR,SM1_SR
    if which==0:
        return Vector((sign*S0_X,S0_Y,S0_Z)),S0_LR,S0_SR
    return Vector((sign*S1_X,S1_Y,S1_Z)),S1_LR,S1_SR

def segment_metrics(co, which_a, which_b, eps=0.0):
    sign=1.0 if co.x>=0 else -1.0
    a,lr0,sr0=station_point(sign,which_a)
    b,lr1,sr1=station_point(sign,which_b)
    axis=b-a
    denom=axis.length_squared
    assert denom>0
    t_raw=(co-a).dot(axis)/denom
    if not (-eps<=t_raw<=1.0+eps):
        return None
    t=max(0.0,min(1.0,t_raw))
    center=a+axis*t
    tangent=axis.normalized()
    lateral=Vector((1.0,0.0,0.0))
    lateral=lateral-tangent*lateral.dot(tangent)
    assert lateral.length>1e-12
    lateral.normalize()
    sagittal=tangent.cross(lateral)
    assert sagittal.length>1e-12
    sagittal.normalize()
    lr=lr0+(lr1-lr0)*t
    sr=sr0+(sr1-sr0)*t
    d=co-center
    u=d.dot(lateral)
    v=d.dot(sagittal)
    q=math.sqrt((u/lr)**2+(v/sr)**2)
    radial_dist=math.sqrt(u*u+v*v)
    return {
        'segment':[which_a,which_b],'t':t,'center':center,'tangent':tangent,
        'lateral':lateral,'sagittal':sagittal,'lr':lr,'sr':sr,
        'u':u,'v':v,'q':q,'radial_dist':radial_dist
    }

def guide_metrics(co, eps=0.0):
    ms=[]
    for a,b in ((-1,0),(0,1)):
        m=segment_metrics(co,a,b,eps)
        if m is not None:
            ms.append(m)
    if not ms:
        return None
    return min(ms,key=lambda m:m['radial_dist'])

def inside_box(co,eps=0.0):
    ax=abs(co.x)
    return (XMIN-eps)<=ax<=(XMAX+eps) and (YMIN-eps)<=co.y<=(YMAX+eps) and (ZMIN-eps)<=co.z<=(ZMAX+eps)

def inside_local(co,eps=0.0):
    return inside_box(co,eps) and guide_metrics(co,eps) is not None

def inside_subdiv_core(co):
    ax=abs(co.x)
    if not (
        (XMIN+SUBDIV_INSET)<=ax<=(XMAX-SUBDIV_INSET) and
        (YMIN+SUBDIV_INSET)<=co.y<=(YMAX-SUBDIV_INSET) and
        (ZMIN+SUBDIV_INSET)<=co.z<=(ZMAX-SUBDIV_INSET)
    ):
        return False
    return guide_metrics(co,0.0) is not None

bm=bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()

orig_verts=list(bm.verts)
orig_coords={v:v.co.copy() for v in orig_verts}
source_outside_counter=Counter(tuple(v.co) for v in orig_verts if not inside_local(v.co,SUPPORT_EPS))
assert any(inside_local(v.co) for v in orig_verts), 'no B2a-v3 local source vertices'

eligible_raw=[]
for e in list(bm.edges):
    v0,v1=e.verts
    if not (inside_subdiv_core(v0.co) and inside_subdiv_core(v1.co)):
        continue
    if v0.co.x*v1.co.x<=0:
        continue
    if not e.link_faces:
        continue
    sign=1.0 if v0.co.x>0 else -1.0
    ok=True
    for f in e.link_faces:
        for v in f.verts:
            if not inside_local(v.co) or v.co.x*sign<=0:
                ok=False
                break
        if not ok:
            break
    if ok:
        mid=(v0.co+v1.co)*0.5
        gm=guide_metrics(mid)
        if gm is not None:
            eligible_raw.append((gm['radial_dist'],e))

assert eligible_raw, 'no fully-contained B2a-v3 edges eligible'
eligible_raw.sort(key=lambda x:x[0])
eligible=[e for _,e in eligible_raw[:MAX_SUBDIV_EDGES]]

affected_source_faces=set()
for e in eligible:
    affected_source_faces.update(e.link_faces)

bmesh.ops.subdivide_edges(
    bm,
    edges=eligible,
    cuts=1,
    use_grid_fill=True,
    smooth=0.0
)
bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()

new_vertex_count=len(bm.verts)-src_vert_count
assert MIN_NEW_VERTS<=new_vertex_count<=MAX_NEW_VERTS, (
    f'B2a-v3 new vertex count {new_vertex_count} outside [{MIN_NEW_VERTS},{MAX_NEW_VERTS}]'
)

outside_after_subdivide=Counter(tuple(v.co) for v in bm.verts if not inside_local(v.co,SUPPORT_EPS))
assert outside_after_subdivide==source_outside_counter, 'B2a-v3 subdivision changed outside-local geometry'

local_verts=[v for v in bm.verts if inside_local(v.co,SUPPORT_EPS)]
initial_local={v:v.co.copy() for v in local_verts}

metrics={}
raw_candidates=[]
for v in local_verts:
    m=guide_metrics(initial_local[v])
    if m is None:
        continue
    q=m['q']
    metrics[v]=m
    if Q_MIN<=q<=Q_MAX and abs(q-1.0)>Q_ERROR_THRESHOLD:
        raw_candidates.append(v)

assert raw_candidates, 'no B2a-v3 guide candidates'
pos=sorted([v for v in raw_candidates if initial_local[v].x>=0],key=lambda v:abs(metrics[v]['q']-1.0),reverse=True)[:TOP_PER_SIDE]
neg=sorted([v for v in raw_candidates if initial_local[v].x<0],key=lambda v:abs(metrics[v]['q']-1.0),reverse=True)[:TOP_PER_SIDE]
candidates=pos+neg
assert MIN_CANDIDATES<=len(candidates)<=MAX_CANDIDATES, (
    f'B2a-v3 selected candidate count {len(candidates)} outside [{MIN_CANDIDATES},{MAX_CANDIDATES}]'
)

q_before=[]
q_after=[]
segment_counts={'m1_to_0':0,'0_to_1':0}
skipped_support_exit=0
applied_candidates=[]
for v in candidates:
    p=initial_local[v]
    m=metrics[v]
    q=m['q']
    if q<=1e-12:
        continue
    center=m['center']; tangent=m['tangent']; lateral=m['lateral']; sagittal=m['sagittal']
    u=m['u']; sv=m['v']
    target=center+lateral*(u/q)+sagittal*(sv/q)
    proposed=p+(target-p)*GAIN
    delta=proposed-p
    if delta.length>MAX_LOCAL_DISP and delta.length>0:
        proposed=p+delta.normalized()*MAX_LOCAL_DISP

    if p.x>0 and proposed.x<=0: proposed.x=1e-6
    if p.x<0 and proposed.x>=0: proposed.x=-1e-6

    axial=(proposed-center).dot(tangent)
    proposed=proposed-tangent*axial
    delta=proposed-p
    if delta.length>MAX_LOCAL_DISP and delta.length>0:
        proposed=p+delta.normalized()*MAX_LOCAL_DISP

    # Preserve hard scope membership: a local candidate may not cross the
    # support/segment union after deformation.
    if not inside_local(proposed,SUPPORT_EPS):
        skipped_support_exit+=1
        continue

    d2=proposed-center
    u2=d2.dot(lateral)
    v2=d2.dot(sagittal)
    q2=math.sqrt((u2/m['lr'])**2+(v2/m['sr'])**2)
    assert abs(q2-1.0)<=abs(q-1.0)+1e-7, 'B2a-v3 ellipse error increased'
    q_before.append(abs(q-1.0));q_after.append(abs(q2-1.0))
    if m['segment']==[-1,0]:
        segment_counts['m1_to_0']+=1
    else:
        segment_counts['0_to_1']+=1
    applied_candidates.append(v)
    v.co=proposed

outside_after_fair=Counter(tuple(v.co) for v in bm.verts if not inside_local(v.co,SUPPORT_EPS))
assert outside_after_fair==source_outside_counter, 'B2a-v3 fairing changed outside-local geometry'

local_disp={v:(v.co-initial_local[v]).length for v in local_verts}
vals=list(local_disp.values())
max_local_disp=max(vals) if vals else 0.0
mean_local_disp=sum(vals)/len(vals) if vals else 0.0
changed_local=sum(1 for d in vals if d>1e-10)
assert max_local_disp<=MAX_LOCAL_DISP+1e-7

nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
assert len(nonmanifold)==0, f'B2a-v3 non-manifold edges {len(nonmanifold)}'

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
    assert extent_drift[ax]<=MAX_EXTENT_DRIFT+1e-9

for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

bm.to_mesh(mesh);bm.free();mesh.update()

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
 'gate':'B2a-v3-three-station-proximal-forelimb-root',
 'source':'S-vibe-b1c-v2.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'one local subdivision + piecewise station-1->0->1 signed tapered elliptical guide',
 'station_minus1':{'abs_x':SM1_X,'y':SM1_Y,'z':SM1_Z,'lateral_radius':SM1_LR,'sagittal_radius':SM1_SR},
 'station0':{'abs_x':S0_X,'y':S0_Y,'z':S0_Z,'lateral_radius':S0_LR,'sagittal_radius':S0_SR},
 'station1':{'abs_x':S1_X,'y':S1_Y,'z':S1_Z,'lateral_radius':S1_LR,'sagittal_radius':S1_SR},
 'support':{'abs_x_min':XMIN,'abs_x_max':XMAX,'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX},
 'parameters':{
   'subdivision_cuts':1,'subdivision_inset':SUBDIV_INSET,'max_subdiv_edges':MAX_SUBDIV_EDGES,
   'q_error_threshold':Q_ERROR_THRESHOLD,'q_min':Q_MIN,'q_max':Q_MAX,
   'gain':GAIN,'max_local_displacement':MAX_LOCAL_DISP
 },
 'source_vertex_count':src_vert_count,'source_polygon_count':src_poly_count,'source_edge_count':src_edge_count,
 'result_vertex_count':len(mesh.vertices),'result_polygon_count':len(mesh.polygons),'result_edge_count':len(mesh.edges),
 'eligible_edge_count_raw':len(eligible_raw),'eligible_subdivided_edge_count':len(eligible),
 'affected_source_face_count':len(affected_source_faces),
 'new_vertex_count':new_vertex_count,
 'local_vertex_count_after_subdivision':len(local_verts),
 'raw_candidate_vertex_count':len(raw_candidates),
 'candidate_vertex_count':len(candidates),
 'applied_candidate_count':len(applied_candidates),
 'skipped_support_exit_count':skipped_support_exit,
 'selected_positive_count':len(pos),'selected_negative_count':len(neg),
 'segment_candidate_counts':segment_counts,
 'changed_local_vertex_count':changed_local,
 'max_local_displacement':max_local_disp,'mean_local_displacement':mean_local_disp,
 'mean_abs_q_error_before':sum(q_before)/len(q_before),'mean_abs_q_error_after':sum(q_after)/len(q_after),
 'whole_body_extent_before':src_ext,'whole_body_extent_after':dst_ext,'whole_body_extent_drift':extent_drift,
 'non_manifold_edge_count':0,
 'outside_local_vertex_count':len(outside_body_coords()),
 'fixed_geometry_hash':fixed_hash(),
 'outside_local_original_geometry_unchanged':True,
 'preserved_geometry_unchanged':True,
 'topology_change_scope':'fully-contained same-side three-station proximal forelimb-root faces only',
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b2a-v3-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b2a-v3.blend'),compress=True)
print('VIBE_B2A_V3_EDIT_COMPLETE',json.dumps(report))
