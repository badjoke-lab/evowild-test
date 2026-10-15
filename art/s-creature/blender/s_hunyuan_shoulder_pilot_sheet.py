"""One deliberate connected surface cut/inset/extrusion, not a displacement search."""
import bpy,bmesh,json
from mathutils import Vector
pilot=bpy.app.driver_namespace['shoulder_pilot'];body=pilot['body'];OUT=pilot['OUT']
assert body.mode=='OBJECT'
bm=bmesh.new();bm.from_mesh(body.data)
# Anatomical base: narrow the right broad slab, leave centre chest/arm untouched.
# A compact piecewise cubic taper avoids a hard ROI seam.
def ramp(a,b,t):
    q=max(0,min(1,(t-a)/(b-a)));return q*q*(3-2*q)
changed=0
for v in bm.verts:
    x,y,z=v.co
    w=ramp(.035,.105,x)*ramp(-.51,-.43,y)*(1-ramp(-.25,-.17,y))*ramp(-.21,-.12,z)*(1-ramp(.105,.17,z))
    if w:
        v.co.x-=.018*w
        changed+=1
# Cut a clean oblique leaf perimeter through existing triangles.
leaf=[(-.422,.002),(-.377,.076),(-.286,.125),(-.246,.087),(-.283,.012),(-.349,-.085),(-.393,-.051)]
def inside(y,z):
    c=False
    for i,(a,b) in enumerate(leaf):
        d,e=leaf[(i+1)%len(leaf)]
        if (b>z)!=(e>z) and y<(d-a)*(z-b)/(e-b)+a:c=not c
    return c
for i,(y,z) in enumerate(leaf):
    yy,zz=leaf[(i+1)%len(leaf)]
    faces=[f for f in bm.faces if all(v.co.x>.072 for v in f.verts) and -.47<f.calc_center_median().y<-.20 and -.13<f.calc_center_median().z<.155]
    geom=set(faces)
    for f in faces:geom.update(f.edges);geom.update(f.verts)
    bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=Vector((0,y,z)),plane_no=Vector((0,zz-z,y-yy)),clear_inner=False,clear_outer=False)
faces=[f for f in bm.faces if all(v.co.x>.072 for v in f.verts) and inside(f.calc_center_median().y,f.calc_center_median().z)]
assert faces
# Inset face region and lift its interior sideways. Exterior cut loop is retained.
result=bmesh.ops.inset_region(bm,faces=faces,thickness=.0045,depth=0,use_even_offset=True,use_boundary=True)
bevel=set(result['faces'])
cap=set(faces)-bevel
cap={f for f in cap if f.is_valid}
# Distinguish new strip vertices from the unchanged perimeter.
capverts={v for f in cap for v in f.verts}
for v in capverts:
    # Upper sheet is a gently folded oblique plane with an anterior ridge.
    y,z=v.co.y,v.co.z
    root=-.423+.52*z
    taper=ramp(0,.095,y-root)
    v.co.x+=.017*taper
    v.co.z+=.008*ramp(.01,.10,z)*taper
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
for f in bm.faces:f.select_set(False)
bm.to_mesh(body.data);bm.free();body.data.update()
pilot['sheet_precheck']=body.data.copy()
(OUT/'04_SHEET_OPERATION.json').write_text(json.dumps({'operation':'one-side base narrowing .018, planar knife boundaries, face-region inset .0045, sheet lift tapered from blended anterior root to .017 posterior edge','base_vertices_shaped':changed,'sheet_cap_vertices':len(capverts),'vertices':len(body.data.vertices),'faces':len(body.data.polygons),'leaf_yz':leaf,'topology_preserved':False},indent=2))
pilot['view']('SIDE','04_TAPERED_SHEET')
