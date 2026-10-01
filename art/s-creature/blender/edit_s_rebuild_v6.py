"""Crest-only Gate A v6 correction from v5. All non-crest geometry is locked."""
import bpy,bmesh,os,json,hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v5.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
m=core.data
assert len(m.vertices)==224

def digest():
    return hashlib.sha256(b''.join(
      repr(tuple(v.co)).encode()
      for o in sorted(cage.objects,key=lambda o:o.name)
      if o.type=='MESH'
      for v in o.data.vertices)).hexdigest()

source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}
counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}

# v5 core layout: 19 body/tail rings * 8 = 152 vertices, followed by six crest plates.
v5_cross=[
 [(.050,-.66,1.345,.024,.040),(.058,-.40,1.425,.020,.028),(.064,-.10,1.500,.004,.004)],
 [(.070,-.65,1.300,.026,.038),(.075,-.39,1.355,.020,.026),(.079,-.10,1.400,.004,.004)],
 [(.081,-.61,1.260,.024,.034),(.084,-.36,1.295,.019,.024),(.086,-.08,1.320,.004,.004)]]
v6_cross=[
 [(.052,-.66,1.332,.024,.038),(.060,-.37,1.345,.019,.025),(.068,.00,1.356,.004,.004)],
 [(.070,-.65,1.296,.026,.036),(.076,-.36,1.306,.019,.024),(.081,.01,1.314,.004,.004)],
 [(.082,-.61,1.262,.024,.032),(.086,-.34,1.269,.018,.022),(.089,.02,1.274,.004,.004)]]

# Plate order created by v5: + side levels 0..2, then - side levels 0..2.
for plate_index in range(6):
    sign=1 if plate_index<3 else -1
    level=plate_index%3
    oldset=v5_cross[level]
    newset=v6_cross[level]
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
bm=bmesh.new(); bm.from_mesh(m); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(m); bm.free()

# Absolute scope lock: all core vertices before crest and every other mesh stay exact.
assert all(tuple(m.vertices[i].co)==source_coords[core.name][i] for i in range(152)), 'Non-crest core changed'
for o in cage.objects:
    if o.type!='MESH' or o.name==core.name: continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name], o.name+' changed'
assert all([tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name] for o in cage.objects if o.type=='MESH')
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert len(bpy.data.materials)==0 and len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v6.blend'),compress=True)
crest=[v.co for v in m.vertices[152:]]
report={
 'gate':'A','status':'REVIEW_PENDING','source':'S-rebuild-v5.blend',
 'scope':'crest-only','source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'total_cage_vertices':sum(counts.values()),'topology_preserved':True,
 'non_crest_geometry_unchanged':True,'no_materials':True,'no_animation':True,'no_armature':True,
 'crest_vertical_min':min(v.z for v in crest),'crest_vertical_max':max(v.z for v in crest),
 'crest_vertical_envelope':max(v.z for v in crest)-min(v.z for v in crest),
 'changes':['Reduced crest rise drastically while extending plate tips farther rearward','Preserved modest lateral separation and all six skull-rooted laminae'],
 'limitations':['Gate A review pending; no PASS claimed']
}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v6-gate-A.json'),'w'),indent=2)
print('V6_SAVED',json.dumps(report))
