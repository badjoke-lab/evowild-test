"""Clean knife-boundary connected shoulder sheet; no isolated geometry."""
import bpy,bmesh,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt
pilot=bpy.app.driver_namespace['shoulder_pilot'];body=pilot['body'];OUT=pilot['OUT']
SIDE=globals().get('SIDE',1)
STAGE=globals().get('STAGE','07_CURVED_SHEET')
assert body.mode=='OBJECT'
bm=bmesh.new();bm.from_mesh(body.data)
mid=-.03588832542300224
original={v:v.co.copy() for v in bm.verts}
if SIDE==-1:
    for v in bm.verts:v.co.x=2*mid-v.co.x
transformed={v:v.co.copy() for v in bm.verts}
def ramp(a,b,t):
    q=max(0,min(1,(t-a)/(b-a)));return q*q*(3-2*q)
changed=0
for v in bm.verts:
    x,y,z=v.co
    w=ramp(.035,.105,x)*ramp(-.51,-.43,y)*(1-ramp(-.25,-.17,y))*ramp(-.21,-.12,z)*(1-ramp(.105,.17,z))
    if w:v.co.x-=.018*w;changed+=1
bm.normal_update()
tree=BVHTree.FromBMesh(bm)
leaf=[(-.448,-.025),(-.437,.021),(-.409,.063),(-.363,.102),(-.310,.132),(-.280,.137),(-.256,.112),(-.245,.073),(-.257,.022),(-.280,-.043),(-.305,-.101),(-.326,-.139),(-.345,-.142),(-.391,-.108),(-.428,-.065)]
def inside(y,z):
    c=False
    for i,(a,b) in enumerate(leaf):
        d,e=leaf[(i+1)%len(leaf)]
        if (b>z)!=(e>z) and y<(d-a)*(z-b)/(e-b)+a:c=not c
    return c
for i,(y,z) in enumerate(leaf):
    yy,zz=leaf[(i+1)%len(leaf)]
    fs=[f for f in bm.faces if all(v.co.x>.025 for v in f.verts) and -.49<f.calc_center_median().y<-.20 and -.18<f.calc_center_median().z<.17]
    geom=set(fs)
    for f in fs:geom.update(f.edges);geom.update(f.verts)
    bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=Vector((0,y,z)),plane_no=Vector((0,zz-z,y-yy)),clear_inner=False,clear_outer=False)
fs={f for f in bm.faces if all(v.co.x>.025 for v in f.verts) and inside(f.calc_center_median().y,f.calc_center_median().z)}
seed=min(fs,key=lambda f:(f.calc_center_median()-Vector((.12,-.36,-.02))).length)
component={seed};stack=[seed]
while stack:
    f=stack.pop()
    for e in f.edges:
        for other in e.link_faces:
            if other in fs and other not in component:component.add(other);stack.append(other)
fs=component
boundary=[e for e in bm.edges if sum(f in fs for f in e.link_faces)==1]
links={}
for e in boundary:
    for v in e.verts:links.setdefault(v,[]).append(e.other_vert(v))
assert all(len(n)==2 for n in links.values())
start=min(links,key=lambda v:tuple(v.co));ring=[start];prev=None;curr=start
while True:
    nxt=next(n for n in links[curr] if n!=prev)
    if nxt==start:break
    ring.append(nxt);prev,curr=curr,nxt
assert len(ring)==len(links)
interior={v for f in fs for v in f.verts}-set(ring)
removed=len(fs)
bmesh.ops.delete(bm,geom=list(fs),context='FACES_ONLY')
bmesh.ops.delete(bm,geom=list(interior),context='VERTS')
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')

def surface(y,z):
    hit,_,_,_=tree.ray_cast(Vector((1,float(y),float(z))),Vector((-1,0,0)))
    assert hit is not None
    root=-.452+.42*z
    lift=.001+.011*ramp(0,.11,y-root)
    return Vector((hit.x+lift,y,z))

centre=Vector((-.347,-.007))
inner=[]
for v in ring:
    yz=centre+(Vector((v.co.y,v.co.z))-centre)*.945
    inner.append(bm.verts.new(surface(*yz)))
new=[]
for i in range(len(ring)):
    j=(i+1)%len(ring)
    new.append(bm.faces.new((ring[i],ring[j],inner[j],inner[i])))
control=[(-.405,-.025),(-.381,.036),(-.342,.085),(-.292,.102),(-.277,.051),(-.303,.002),(-.337,.026),(-.367,-.022),(-.390,-.068),(-.349,-.080),(-.328,-.109),(-.312,-.049)]
verts=inner+[bm.verts.new(surface(y,z)) for y,z in control]
n=len(inner)
edges=[(i,(i+1)%n) for i in range(n)]
res=delaunay_2d_cdt([Vector((v.co.y,v.co.z)) for v in verts],edges,[list(range(n))],1,1e-8,True)
resolved=[]
for yz,ids in zip(res[0],res[3]):
    resolved.append(verts[ids[0]] if ids else bm.verts.new(surface(*yz)))
for ids in res[2]:new.append(bm.faces.new([resolved[i] for i in ids]))
bmesh.ops.triangulate(bm,faces=new)
if SIDE==-1:
    for v in bm.verts:
        if v in transformed and v.co==transformed[v]:v.co=original[v]
        else:v.co.x=2*mid-v.co.x
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
for f in bm.faces:f.select_set(False)
bm.to_mesh(body.data);bm.free();body.data.update()
pilot['sheet_precheck']=body.data.copy()
(OUT/(STAGE+'_OPERATION.json')).write_text(json.dumps({'operation':'base narrowing .018; curved oblique knife perimeter; anatomical facets and thin connected return .001-.012','side':SIDE,'source_patch_faces_removed':removed,'boundary_vertices':len(ring),'base_vertices_shaped':changed,'vertices':len(body.data.vertices),'faces':len(body.data.polygons),'leaf_yz':leaf,'topology_preserved':False},indent=2))
pilot['view']('SIDE' if SIDE==1 else 'LEFT_SIDE',STAGE)
