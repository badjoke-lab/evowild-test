"""Gate C v2: compensate Catmull-Clark shrink at proximal limb roots only."""
import bpy,bmesh,os,json,hashlib,math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v1.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']

def digest():
    return hashlib.sha256(b''.join(
        repr(tuple(v.co)).encode()
        for o in sorted(cage.objects,key=lambda o:o.name)
        if o.type=='MESH'
        for v in o.data.vertices
    )).hexdigest()

source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}

limbs=['S_forelimb_L','S_forelimb_R','S_hindlimb_L','S_hindlimb_R']

def centroid(mesh,ring,sides=8):
    pts=[mesh.vertices[ring*sides+k].co for k in range(sides)]
    return sum((p.copy() for p in pts),Vector())/sides

def expand_ring(mesh,ring,scale,inboard,sides=8):
    c=centroid(mesh,ring,sides)
    sign=-1.0 if c.x<0 else 1.0
    pts=[mesh.vertices[ring*sides+k].co.copy() for k in range(sides)]
    nc=c.copy()
    nc.x=c.x-sign*inboard
    for k,p in enumerate(pts):
        d=p-c
        mesh.vertices[ring*sides+k].co=nc+d*scale

for name in limbs:
    o=bpy.data.objects[name]
    m=o.data
    assert len(m.vertices)==96,(name,len(m.vertices))
    is_fore='forelimb' in name
    expand_ring(m,0,1.08,0.010 if is_fore else 0.012)
    expand_ring(m,1,1.045,0.006 if is_fore else 0.007)
    m.update()
    bm=bmesh.new(); bm.from_mesh(m); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(m); bm.free()
    mods=[md for md in o.modifiers if md.type=='SUBSURF']
    assert len(mods)==1 and mods[0].levels==1 and mods[0].render_levels==1

# Hard locks.
for o in cage.objects:
    if o.type!='MESH': continue
    if o.name in limbs:
        old=source_coords[o.name]
        for idx in range(2*8,12*8):
            assert tuple(o.data.vertices[idx].co)==old[idx],f'{o.name} locked ring changed {idx}'
    else:
        assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' changed'
assert all(
    [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name]
    for o in cage.objects if o.type=='MESH'
),'Topology changed'
assert len(bpy.data.materials)==0 and len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v2.blend'),compress=True)
report={
 'gate':'C','pass':'v2','status':'REVIEW_PENDING','source':'S-gateC-v1.blend',
 'scope':'proximal rings 0-1 of four limb meshes only',
 'source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'locked_limb_rings_2_11_unchanged':True,
 'all_nonlimb_meshes_unchanged':True,
 'topology_preserved':True,
 'subsurf_modifiers_preserved':True,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':['Expanded proximal root rings to compensate Catmull-Clark shrink','Moved root centroids slightly inboard for stronger core overlap'],
 'limitations':['Gate C v2 review pending','No destructive welding/retopology yet']
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v2.json'),'w'),indent=2)
print('GATE_C_V2_SAVED',json.dumps(report))
