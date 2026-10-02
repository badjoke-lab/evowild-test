"""Gate A v9: rebuild only the four limb cages with denser transition rings. Core and toes stay exact from v8."""
import bpy,bmesh,math,os,json,hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v8.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']

def digest():
    return hashlib.sha256(b''.join(
        repr(tuple(v.co)).encode()
        for o in sorted(cage.objects,key=lambda o:o.name)
        if o.type=='MESH'
        for v in o.data.vertices
    )).hexdigest()

source_hash=digest()
core_coords=[tuple(v.co) for v in core.data.vertices]
toe_coords={
    o.name:[tuple(v.co) for v in o.data.vertices]
    for o in cage.objects if o.type=='MESH' and '_toe_' in o.name
}
old_counts={
    o.name:len(o.data.vertices)
    for o in cage.objects if o.type=='MESH' and (o.name.startswith('S_forelimb_') or o.name.startswith('S_hindlimb_'))
}

def remove_obj(name):
    o=bpy.data.objects.get(name)
    assert o is not None
    bpy.data.objects.remove(o,do_unlink=True)

for name in ('S_forelimb_L','S_forelimb_R','S_hindlimb_L','S_hindlimb_R'):
    remove_obj(name)

def loft(name,chain,sides=8):
    vs=[]; fs=[]
    for i,(center,wx,wy) in enumerate(chain):
        c=Vector(center)
        tangent=Vector(chain[min(i+1,len(chain)-1)][0])-Vector(chain[max(i-1,0)][0])
        tangent.normalize()
        lateral=Vector((1,0,0))
        lateral=(lateral-tangent*lateral.dot(tangent)).normalized()
        sagittal=tangent.cross(lateral).normalized()
        for k in range(sides):
            a=k*math.tau/sides
            vs.append(tuple(c+lateral*(wx*math.cos(a))+sagittal*(wy*math.sin(a))))
    for i in range(len(chain)-1):
        for k in range(sides):
            fs.append((i*sides+k,(i+1)*sides+k,(i+1)*sides+(k+1)%sides,i*sides+(k+1)%sides))
    fs.append(tuple(reversed(range(sides))))
    fs.append(tuple((len(chain)-1)*sides+k for k in range(sides)))
    m=bpy.data.meshes.new(name+'_cage')
    m.from_pydata(vs,[],fs);m.update()
    o=bpy.data.objects.new(name,m);cage.objects.link(o)
    for p in m.polygons:p.use_smooth=True
    bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
    return o

for sign,label in [(-1,'L'),(1,'R')]:
    fore=[
      ((sign*.086,-.010,1.020),.118,.138),
      ((sign*.112,.000,.985),.108,.126),
      ((sign*.142,.025,.925),.091,.108),
      ((sign*.168,.070,.850),.075,.089),
      ((sign*.190,.125,.765),.060,.070),
      ((sign*.198,.155,.710),.052,.060),
      ((sign*.181,.070,.620),.044,.051),
      ((sign*.158,-.040,.510),.037,.043),
      ((sign*.139,-.135,.380),.031,.036),
      ((sign*.127,-.210,.255),.026,.031),
      ((sign*.132,-.250,.145),.022,.026),
      ((sign*.150,-.270,.060),.024,.024)]
    hind=[
      ((sign*.080,.715,1.015),.128,.150),
      ((sign*.106,.690,.985),.116,.138),
      ((sign*.142,.625,.930),.101,.120),
      ((sign*.176,.545,.865),.086,.101),
      ((sign*.205,.455,.790),.070,.082),
      ((sign*.218,.395,.750),.061,.071),
      ((sign*.204,.515,.650),.052,.061),
      ((sign*.181,.665,.545),.044,.052),
      ((sign*.158,.815,.425),.037,.044),
      ((sign*.139,.930,.315),.031,.037),
      ((sign*.136,.990,.205),.025,.030),
      ((sign*.150,.900,.062),.024,.024)]
    loft('S_forelimb_'+label,fore)
    loft('S_hindlimb_'+label,hind)

# Recalculate and verify hard locks.
for o in cage.objects:
    if o.type=='MESH':
        o.data.update()

assert [tuple(v.co) for v in core.data.vertices]==core_coords, 'Core changed'
for name,coords in toe_coords.items():
    o=bpy.data.objects[name]
    assert [tuple(v.co) for v in o.data.vertices]==coords, name+' changed'
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

new_counts={
    o.name:len(o.data.vertices)
    for o in cage.objects if o.type=='MESH' and (o.name.startswith('S_forelimb_') or o.name.startswith('S_hindlimb_'))
}
assert all(new_counts[k]>old_counts[k] for k in old_counts)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v9.blend'),compress=True)
report={
  'gate':'A',
  'status':'REVIEW_PENDING',
  'source':'S-rebuild-v8.blend',
  'scope':'four limb mesh topology rebuild only',
  'source_geometry_sha256':source_hash,
  'geometry_sha256':digest(),
  'core_geometry_unchanged':True,
  'toe_geometry_unchanged':True,
  'old_limb_vertex_counts':old_counts,
  'new_limb_vertex_counts':new_counts,
  'no_materials':True,
  'no_animation':True,
  'no_armature':True,
  'changes':[
    'Rebuilt each limb with 12 cross-section rings instead of sparse v8 chains',
    'Added buried root and transition rings to make shoulder/pelvis connections gradual in silhouette',
    'Added explicit elbow/knee/hock transition rings and progressive distal taper',
    'Kept v8 frontal-plane asymmetry and exact toe meshes'
  ],
  'limitations':['Gate A silhouette review pending; no PASS claimed','No production welding or anatomical surface refinement']
}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v9-gate-A.json'),'w'),indent=2)
print('V9_SAVED',json.dumps(report))
