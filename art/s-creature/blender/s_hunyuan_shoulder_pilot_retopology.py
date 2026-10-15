"""Connected right shoulder surgery; run modes through live Blender MCP."""
import bpy, bmesh, json, numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

pilot = bpy.app.driver_namespace['shoulder_pilot']
body = pilot['body']
OUT = pilot['OUT']
outline = [(-.45,-.035),(-.435,.045),(-.35,.13),(-.24,.13),(-.208,.073),(-.26,-.045),(-.303,-.145),(-.39,-.10)]

def inside(y,z):
    hit=False
    for i,(ya,za) in enumerate(outline):
        yb,zb=outline[(i+1)%len(outline)]
        if (za>z)!=(zb>z) and y<(yb-ya)*(z-za)/(zb-za)+ya: hit=not hit
    return hit

if body.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
bm = bmesh.new();bm.from_mesh(body.data)
bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
selected={f for f in bm.faces if all(v.co.x>.075 for v in f.verts) and inside(f.calc_center_median().y,f.calc_center_median().z)}
# Keep only the connected lateral component containing the observed shoulder centre.
seed=min(selected,key=lambda f:(f.calc_center_median()-Vector((.132,-.372,-.018))).length)
component={seed};stack=[seed]
while stack:
    f=stack.pop()
    for e in f.edges:
        for n in e.link_faces:
            if n in selected and n not in component:component.add(n);stack.append(n)
selected=component
for f in bm.faces:f.select_set(f in selected)
boundary=[e for e in bm.edges if sum(f in selected for f in e.link_faces)==1]
print('PATCH',len(selected),'faces',len(boundary),'boundary edges')

if MODE == 'SELECT':
    bm.to_mesh(body.data);bm.free();body.data.update()
    bpy.ops.object.mode_set(mode='EDIT')
    pilot['view']('FRONT34','01_REGION',True)
else:
    assert MODE == 'REBUILD'
    # Order the actual existing boundary. The patch has one closed perimeter.
    links={}
    for e in boundary:
        for v in e.verts:links.setdefault(v,[]).append(e.other_vert(v))
    assert all(len(n)==2 for n in links.values())
    start=next(iter(links));ring=[start];previous=None;current=start
    while True:
        nxt=next(n for n in links[current] if n!=previous)
        if nxt==start:break
        ring.append(nxt);previous,current=current,nxt
    assert len(ring)==len(links)
    # Keep perimeter and all external faces exactly; replace only the patch interior.
    interior={v for f in selected for v in f.verts}-set(ring)
    bmesh.ops.delete(bm,geom=list(selected),context='FACES_ONLY')
    bmesh.ops.delete(bm,geom=list(interior),context='VERTS')
    # Build a small return surface around a clean faceted deltoid. The inner
    # sheet is narrower than Stage1; it will be split/extruded in the next edit.
    centre=Vector((-.347,-.004))
    inner=[]
    for v in ring:
        yz=centre+(Vector((v.co.y,v.co.z))-centre)*.86
        y,z=yz
        # Lower pointed deltoid becomes a rounded set of four intentional planes.
        x=.145-.17*abs(y+.345)-.13*abs(z+.005)
        inner.append(bm.verts.new((x,y,z)))
    newfaces=[]
    for i in range(len(ring)):
        j=(i+1)%len(ring)
        newfaces.append(bm.faces.new((ring[i],ring[j],inner[j],inner[i])))
    # Constrained triangulation: intentional diagonal ridge plus upper/lower
    # plane controls; every cap vertex belongs to the same connected surface.
    controls=[(.147,-.361,.012),(.131,-.319,-.093),(.132,-.407,-.025),(.14,-.295,.073),(.123,-.371,.088),(.133,-.255,.07)]
    verts=inner+[bm.verts.new(p) for p in controls]
    n=len(inner)
    edges=[(i,(i+1)%n) for i in range(n)]+[(n,n+1),(n,n+2),(n,n+3),(n+3,n+4),(n+3,n+5)]
    xy=[Vector((v.co.y,v.co.z)) for v in verts]
    result=delaunay_2d_cdt(xy,edges,[list(range(n))],1,1e-7,True)
    outxy,outedges,outfaces,originals,_,_=result
    resolved=[]
    for q,ids in zip(outxy,originals):
        assert ids, 'Unexpected CDT intersection vertex'
        resolved.append(verts[ids[0]])
    for ids in outfaces:
        newfaces.append(bm.faces.new([resolved[i] for i in ids]))
    bmesh.ops.recalc_face_normals(bm,faces=newfaces)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    for f in bm.faces:f.select_set(False)
    bm.to_mesh(body.data);bm.free();body.data.update()
    pilot['view']('SIDE','02_RETOPOLOGY')
    (OUT/'02_RETOPOLOGY.json').write_text(json.dumps({'operation':'replace lateral face region with connected inset return and constrained faceted deltoid','source_faces_removed':len(selected),'perimeter_vertices_preserved':len(ring),'vertices':len(body.data.vertices),'faces':len(body.data.polygons),'side':'positive X only'},indent=2))
