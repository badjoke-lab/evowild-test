"""Gate B v4: refine only the 12 toe meshes."""
import bpy,bmesh,os,json,hashlib,re
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateB-v3.blend'))
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

toes=sorted([o for o in cage.objects if o.type=='MESH' and '_toe_' in o.name],key=lambda o:o.name)
assert len(toes)==12,[o.name for o in toes]

def ring_centroid(mesh,ring,sides=6):
    pts=[mesh.vertices[ring*sides+k].co for k in range(sides)]
    return sum((p.copy() for p in pts),Vector())/sides

for o in toes:
    m=o.data
    assert len(m.vertices)==24,(o.name,len(m.vertices))
    match=re.search(r'_(-?1|0)$',o.name)
    assert match,o.name
    toe_index=int(match.group(1))

    # Keep the root centroid fixed; taper later rings and give the fan a restrained spread.
    cents=[ring_centroid(m,r) for r in range(4)]
    scales=[1.08,0.94,0.78,0.62]
    for r in range(4):
        c=cents[r]
        shift=Vector((toe_index*0.0025*r, -0.0020*r, -0.0008*r))
        for k in range(6):
            idx=r*6+k
            p=m.vertices[idx].co.copy()
            d=p-c
            m.vertices[idx].co=c+shift+d*scales[r]
    m.update()
    bm=bmesh.new(); bm.from_mesh(m); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(m); bm.free()

# Hard locks: every non-toe mesh exact; toe topology unchanged.
for o in cage.objects:
    if o.type!='MESH':
        continue
    if o not in toes:
        assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name], o.name+' changed'
assert all(
    [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name]
    for o in cage.objects if o.type=='MESH'
), 'Topology changed'
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateB-v4.blend'),compress=True)
report={
 'gate':'B','pass':'v4','status':'REVIEW_PENDING','source':'S-gateB-v3.blend',
 'scope':'12 toe meshes only',
 'source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'toe_mesh_count':len(toes),
 'all_nontoe_meshes_unchanged':True,
 'toe_topology_preserved':True,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':[
   'Applied progressive root-to-tip taper to all twelve toe meshes',
   'Added restrained lateral fan separation to outer toes',
   'Kept toe roots compact and avoided any paw/hoof mass'
 ],
 'limitations':['Gate B v4 review pending','No production welding/retopology']
}
json.dump(report,open(os.path.join(OUT,'S-gateB-v4.json'),'w'),indent=2)
print('GATE_B_V4_SAVED',json.dumps(report))
