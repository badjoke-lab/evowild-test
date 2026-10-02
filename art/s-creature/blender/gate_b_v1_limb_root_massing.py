"""Gate B v1: proximal limb-root massing only from accepted Gate A v14."""
import bpy,bmesh,os,json,hashlib,math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v14.blend'))
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

limb_names=['S_forelimb_L','S_forelimb_R','S_hindlimb_L','S_hindlimb_R']
for name in limb_names:
    assert name in bpy.data.objects
    assert len(bpy.data.objects[name].data.vertices)==96, (name,len(bpy.data.objects[name].data.vertices))

def ring_centroid(mesh,ring,sides=8):
    pts=[mesh.vertices[ring*sides+k].co for k in range(sides)]
    return sum((p.copy() for p in pts),Vector())/sides

def reshape_ring(mesh,ring,target_x_abs,target_wx,target_sag,sides=8):
    c=ring_centroid(mesh,ring,sides)
    sign=-1.0 if c.x<0 else 1.0
    pts=[mesh.vertices[ring*sides+k].co.copy() for k in range(sides)]
    max_x=max(abs(p.x-c.x) for p in pts)
    max_s=max(math.hypot(p.y-c.y,p.z-c.z) for p in pts)
    assert max_x>1e-8 and max_s>1e-8
    sx=target_wx/max_x
    ss=target_sag/max_s
    nc=c.copy()
    if target_x_abs is not None:
        nc.x=sign*target_x_abs
    for k,p in enumerate(pts):
        d=p-c
        mesh.vertices[ring*sides+k].co=Vector((nc.x+d.x*sx,nc.y+d.y*ss,nc.z+d.z*ss))

# Target widths make the first six rings lose mass gradually rather than as cones.
fore=[
    (0.070,0.118,0.145),
    (0.095,0.114,0.138),
    (0.128,0.104,0.128),
    (None ,0.092,0.115),
    (None ,0.078,0.099),
    (None ,0.066,0.079),
]
hind=[
    (0.065,0.130,0.154),
    (0.092,0.126,0.148),
    (0.128,0.116,0.139),
    (None ,0.104,0.126),
    (None ,0.089,0.110),
    (None ,0.075,0.088),
]

for name in ('S_forelimb_L','S_forelimb_R'):
    m=bpy.data.objects[name].data
    for i,args in enumerate(fore):
        reshape_ring(m,i,*args)
    m.update()

for name in ('S_hindlimb_L','S_hindlimb_R'):
    m=bpy.data.objects[name].data
    for i,args in enumerate(hind):
        reshape_ring(m,i,*args)
    m.update()

for name in limb_names:
    m=bpy.data.objects[name].data
    bm=bmesh.new(); bm.from_mesh(m); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(m); bm.free()

# Hard locks.
for o in cage.objects:
    if o.type!='MESH':
        continue
    if o.name in limb_names:
        # distal rings 6..11 exact
        old=source_coords[o.name]
        for idx in range(6*8,12*8):
            assert tuple(o.data.vertices[idx].co)==old[idx], f'{o.name} distal changed {idx}'
    else:
        assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name], o.name+' changed'

assert all(
    [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name]
    for o in cage.objects if o.type=='MESH'
), 'Topology changed'
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateB-v1.blend'),compress=True)
report={
 'gate':'B','pass':'v1','status':'REVIEW_PENDING','source':'S-rebuild-v14.blend',
 'scope':'proximal six rings of four limb meshes only',
 'source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'all_nonlimb_meshes_unchanged':True,'distal_limb_rings_unchanged':True,'topology_preserved':True,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':['Moved only the first three limb-ring centers slightly inboard for deeper root overlap','Smoothed cross-section falloff across the proximal six rings','Preserved distal rings, toes, core and crest exactly'],
 'limitations':['Gate B v1 review pending','No welding, crest-root refinement, feet refinement or tail-root refinement yet']
}
json.dump(report,open(os.path.join(OUT,'S-gateB-v1.json'),'w'),indent=2)
print('GATE_B_V1_SAVED',json.dumps(report))
