"""Gate A v11: replace paired crest topology with a narrow central overlapping crest group. Preserve all non-crest coordinates."""
import bpy,bmesh,math,os,json,hashlib
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v10.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
old_core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']

def digest():
    return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()

source_hash=digest()
body_coords=[tuple(v.co) for v in old_core.data.vertices[:152]]
locked_other={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH' and o.name!=old_core.name}

# Replace core with same 19 body/tail rings and no old crest appendages.
verts=body_coords[:]; faces=[]
def face(ids): faces.append(tuple(ids))
rings=[list(range(i*8,(i+1)*8)) for i in range(19)]
face(tuple(reversed(rings[0])))
for r in range(18):
    for k in range(8):
        face((rings[r][k],rings[r+1][k],rings[r+1][(k+1)%8],rings[r][(k+1)%8]))
face(rings[-1])

bpy.data.objects.remove(old_core,do_unlink=True)
mesh=bpy.data.meshes.new('S_rebuild_v11_core_cage')
mesh.from_pydata(verts,[],faces);mesh.update()
core=bpy.data.objects.new('S_rebuild_core_head_crest_neck_torso_tail',mesh);cage.objects.link(core)
for p in mesh.polygons:p.use_smooth=True
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()

# One crest object with four heavily-overlapping laminae.
# Each plate is a thin prism with 3 sections; roots are embedded inside the posterior skull.
cv=[];cf=[]
def add_plate(cx,root_y,root_z,mid_y,mid_z,tip_y,tip_z,root_w,mid_w,tip_w,thick):
    base=len(cv)
    sections=[
      (cx,root_y,root_z,root_w,thick),
      (cx*.72,mid_y,mid_z,mid_w,thick*.72),
      (cx*.35,tip_y,tip_z,tip_w,thick*.35)]
    for x,y,z,w,t in sections:
        cv.extend([(x-w,y,z+t),(x+w,y,z+t),(x+w,y,z-t),(x-w,y,z-t)])
    for s in range(2):
        a=base+s*4;b=base+(s+1)*4
        for j in range(4):cf.append((a+j,b+j,b+(j+1)%4,a+(j+1)%4))
    cf.append(tuple(reversed(range(base,base+4))))
    cf.append(tuple(range(base+8,base+12)))

add_plate(-.018,-.62,1.305,-.28,1.355,.12,1.430,.050,.034,.006,.024)
add_plate( .018,-.62,1.305,-.25,1.340,.15,1.405,.050,.034,.006,.024)
add_plate(-.008,-.58,1.282,-.22,1.315,.17,1.370,.046,.030,.005,.021)
add_plate( .008,-.56,1.272,-.18,1.300,.19,1.345,.044,.029,.005,.020)

cm=bpy.data.meshes.new('S_rebuild_v11_crest_cage');cm.from_pydata(cv,[],cf);cm.update()
crest=bpy.data.objects.new('S_rebuild_crest_center_group',cm);cage.objects.link(crest)
for p in cm.polygons:p.use_smooth=False
bm=bmesh.new();bm.from_mesh(cm);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cm);bm.free()

# Hard locks.
assert [tuple(v.co) for v in core.data.vertices]==body_coords
for name,coords in locked_other.items():
    o=bpy.data.objects[name]
    assert [tuple(v.co) for v in o.data.vertices]==coords, name+' changed'
assert len(bpy.data.materials)==0 and len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v11.blend'),compress=True)
report={
 'gate':'A','status':'REVIEW_PENDING','source':'S-rebuild-v10.blend',
 'scope':'crest topology reset only','source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'body_coordinates_unchanged':True,'all_noncrest_meshes_unchanged':True,
 'paired_crest_removed':True,'central_crest_group_plates':4,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':['Removed six bilateral paired crest appendages','Closed skull/body core with original non-crest ring coordinates','Added four overlapping narrow rear-upward laminar plates in one central crest group'],
 'limitations':['Gate A review pending; no PASS claimed','Crest root is visually embedded but production welding is deferred']
}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v11-gate-A.json'),'w'),indent=2)
print('V11_SAVED',json.dumps(report))
