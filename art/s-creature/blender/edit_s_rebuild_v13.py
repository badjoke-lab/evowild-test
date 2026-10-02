"""Gate A v13: separate crest blade trajectories in side silhouette. All non-crest geometry locked."""
import bpy,bmesh,os,json,hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v12.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']

def digest():
    return hashlib.sha256(b''.join(
        repr(tuple(v.co)).encode()
        for o in sorted(cage.objects,key=lambda o:o.name)
        if o.type=='MESH'
        for v in o.data.vertices)).hexdigest()

source_hash=digest()
locked={o.name:[tuple(v.co) for v in o.data.vertices]
        for o in cage.objects if o.type=='MESH' and o.name!='S_rebuild_crest_staggered_group'}

old=bpy.data.objects.get('S_rebuild_crest_staggered_group')
assert old is not None
bpy.data.objects.remove(old,do_unlink=True)

cv=[]; cf=[]
def add_plate(cx,root_y,root_z,mid_y,mid_z,tip_y,tip_z,root_w,mid_w,tip_w,thick):
    base=len(cv)
    sections=[
      (cx,root_y,root_z,root_w,thick),
      (cx*.92,mid_y,mid_z,mid_w,thick*.78),
      (cx*.82,tip_y,tip_z,tip_w,thick*.56)]
    for x,y,z,w,t in sections:
        cv.extend([(x-w,y,z+t),(x+w,y,z+t),(x+w,y,z-t),(x-w,y,z-t)])
    for s in range(2):
        a=base+s*4; b=base+(s+1)*4
        for j in range(4):
            cf.append((a+j,b+j,b+(j+1)%4,a+(j+1)%4))
    cf.append(tuple(reversed(range(base,base+4))))
    cf.append(tuple(range(base+8,base+12)))

# Distinct rear-upward fan trajectories. Overall X envelope remains narrow.
add_plate( .000,-.63,1.315,-.31,1.405,.12,1.505,.034,.027,.018,.020)
add_plate(-.026,-.62,1.305,-.27,1.365,.19,1.455,.032,.026,.017,.019)
add_plate( .028,-.60,1.296,-.23,1.335,.24,1.415,.031,.025,.017,.019)
add_plate(-.050,-.58,1.286,-.19,1.312,.28,1.375,.029,.024,.016,.018)
add_plate( .050,-.56,1.280,-.15,1.298,.31,1.342,.028,.023,.016,.018)

cm=bpy.data.meshes.new('S_rebuild_v13_crest_cage')
cm.from_pydata(cv,[],cf); cm.update()
crest=bpy.data.objects.new('S_rebuild_crest_fan_group',cm)
cage.objects.link(crest)
for p in cm.polygons:p.use_smooth=False
bm=bmesh.new(); bm.from_mesh(cm); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(cm); bm.free()

for name,coords in locked.items():
    o=bpy.data.objects[name]
    assert [tuple(v.co) for v in o.data.vertices]==coords, name+' changed'
assert len(bpy.data.materials)==0 and len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v13.blend'),compress=True)
report={
 'gate':'A','status':'REVIEW_PENDING','source':'S-rebuild-v12.blend',
 'scope':'crest object only','source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'all_noncrest_meshes_unchanged':True,'v12_crest_removed':True,'fan_plates':5,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':['Separated five plate trajectories by rise and rearward reach','Kept narrow lateral envelope and nonzero tip widths'],
 'limitations':['Gate A review pending; no PASS claimed','Production crest-root welding deferred']
}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v13-gate-A.json'),'w'),indent=2)
print('V13_SAVED',json.dumps(report))
