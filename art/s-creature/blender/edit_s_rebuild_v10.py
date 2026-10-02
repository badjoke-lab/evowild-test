"""Gate A v10: crest-only reference alignment from v9. All non-crest geometry is locked."""
import bpy,bmesh,os,json,hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v9.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
m=core.data
assert len(m.vertices)==224

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
counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}

# v9 inherits v7/v6 crest geometry. v7 translated the v6 laminae +0.12 in Y.
old_cross=[
 [(.052,-.54,1.332,.024,.038),(.060,-.25,1.345,.019,.025),(.068,.12,1.356,.004,.004)],
 [(.070,-.53,1.296,.026,.036),(.076,-.24,1.306,.019,.024),(.081,.13,1.314,.004,.004)],
 [(.082,-.49,1.262,.024,.032),(.086,-.22,1.269,.018,.022),(.089,.14,1.274,.004,.004)]]

# Canonical-aligned v10: narrower lateral centers, modest upward sweep,
# long rearward projection, and tips moving closer to the centerline.
new_cross=[
 [(.050,-.54,1.330,.022,.036),(.043,-.22,1.375,.016,.022),(.026,.13,1.435,.004,.003)],
 [(.061,-.53,1.298,.023,.034),(.052,-.20,1.337,.016,.020),(.031,.14,1.388,.004,.003)],
 [(.070,-.49,1.268,.022,.030),(.060,-.18,1.300,.015,.018),(.036,.15,1.340,.004,.003)]]

# Crest vertices are 152:224, six plates, 12 vertices per plate.
for plate_index in range(6):
    sign=1 if plate_index<3 else -1
    level=plate_index%3
    oldset=old_cross[level]
    newset=new_cross[level]
    plate_base=152+plate_index*12
    for ci,(old,new) in enumerate(zip(oldset,newset)):
        x,y,z,t,d=old
        nx,ny,nz,nt,nd=new
        for j in range(4):
            idx=plate_base+ci*4+j
            p=m.vertices[idx].co.copy()
            sx=sign*p.x
            rx=0.0 if t==0 else (sx-x)/t
            rz=0.0 if d==0 else (p.z-z)/d
            m.vertices[idx].co=(sign*(nx+rx*nt),ny,nz+rz*nd)

m.update()
bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()

# Hard lock: every non-crest vertex in every mesh must remain exact.
assert all(tuple(m.vertices[i].co)==source_coords[core.name][i] for i in range(152)), 'Non-crest core changed'
for o in cage.objects:
    if o.type!='MESH' or o.name==core.name:
        continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name], o.name+' changed'
assert all(
    [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name]
    for o in cage.objects if o.type=='MESH'
), 'Topology changed'
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v10.blend'),compress=True)
crest=[v.co for v in m.vertices[152:]]
report={
  'gate':'A',
  'status':'REVIEW_PENDING',
  'source':'S-rebuild-v9.blend',
  'scope':'crest-only canonical reference alignment',
  'source_geometry_sha256':source_hash,
  'geometry_sha256':digest(),
  'non_crest_geometry_unchanged':True,
  'topology_preserved':True,
  'total_cage_vertices':sum(counts.values()),
  'no_materials':True,
  'no_animation':True,
  'no_armature':True,
  'crest_vertical_min':min(v.z for v in crest),
  'crest_vertical_max':max(v.z for v in crest),
  'crest_vertical_envelope':max(v.z for v in crest)-min(v.z for v in crest),
  'changes':[
    'Raised crest tips into a modest rear-upward canonical S direction line',
    'Narrowed lateral spread through the mid and tip sections',
    'Moved plate tips closer to centerline while retaining six separate skull-rooted laminae',
    'Preserved long rearward reach and all non-crest geometry'
  ],
  'limitations':['Gate A review pending; no PASS claimed']
}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v10-gate-A.json'),'w'),indent=2)
print('V10_SAVED',json.dumps(report))
