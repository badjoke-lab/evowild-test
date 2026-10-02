"""Gate B v2: append a compact shared crest saddle while preserving every existing coordinate."""
import bpy,bmesh,os,json,hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateB-v1.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
crest=bpy.data.objects['S_rebuild_crest_low_fan_group']

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
old_crest_coords=source_coords[crest.name]
old_crest_faces=source_topology[crest.name]
old_count=len(old_crest_coords)

# Rebuild only the crest mesh: old vertices/faces first, then append a small shared saddle.
verts=list(old_crest_coords)
faces=list(old_crest_faces)

def add_rect_section(y,z,w,t):
    base=len(verts)
    verts.extend([
      (-w,y,z+t),
      ( w,y,z+t),
      ( w,y,z-t),
      (-w,y,z-t),
    ])
    return [base+i for i in range(4)]

sections=[
    add_rect_section(-.675,1.295,.060,.022),
    add_rect_section(-.595,1.307,.075,.030),
    add_rect_section(-.515,1.296,.058,.020),
]
for s in range(2):
    a=sections[s]; b=sections[s+1]
    for j in range(4):
        faces.append((a[j],b[j],b[(j+1)%4],a[(j+1)%4]))
faces.append(tuple(reversed(sections[0])))
faces.append(tuple(sections[-1]))

newm=bpy.data.meshes.new('S_gateB_v2_crest_cage')
newm.from_pydata(verts,[],faces); newm.update()
oldm=crest.data
crest.data=newm
for i,p in enumerate(newm.polygons):
    # Preserve the faceted laminae; saddle also remains low-complexity.
    p.use_smooth=False
bpy.data.meshes.remove(oldm)

bm=bmesh.new(); bm.from_mesh(newm); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(newm); bm.free()

# Hard locks: old crest coordinates exact, all other mesh coordinates exact.
assert len(crest.data.vertices)==old_count+12
for i,co in enumerate(old_crest_coords):
    assert tuple(crest.data.vertices[i].co)==co, f'old crest vertex changed {i}'
for o in cage.objects:
    if o.type!='MESH' or o.name==crest.name:
        continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name], o.name+' changed'
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateB-v2.blend'),compress=True)
report={
 'gate':'B','pass':'v2','status':'REVIEW_PENDING','source':'S-gateB-v1.blend',
 'scope':'crest topology addition only',
 'source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'all_existing_coordinates_unchanged':True,
 'old_crest_vertex_count':old_count,
 'new_crest_vertex_count':len(crest.data.vertices),
 'added_saddle_vertices':12,
 'all_noncrest_meshes_unchanged':True,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':['Appended a compact three-section shared saddle mass to the crest mesh','Embedded blade roots visually inside one shared skull-root mass without moving any existing vertex'],
 'limitations':['Gate B v2 review pending','Production welding/retopology remains Gate C work']
}
json.dump(report,open(os.path.join(OUT,'S-gateB-v2.json'),'w'),indent=2)
print('GATE_B_V2_SAVED',json.dumps(report))
