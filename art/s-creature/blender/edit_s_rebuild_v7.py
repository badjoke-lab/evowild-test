"""Gate A v7: shorten head/neck and add frontal-plane limb articulation from v6."""
import bpy,bmesh,math,os,json,hashlib
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v6.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']; m=core.data
assert len(m.vertices)==224

def digest():
    return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()

source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}
counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}

# Only the first eight core rings (head/neck) move. Ring 8 onward stays exact.
stations=[
 (-.86,1.245,1.205,.018),(-.80,1.285,1.195,.043),
 (-.70,1.335,1.185,.070),(-.61,1.350,1.180,.086),
 (-.53,1.305,1.125,.080),(-.42,1.235,1.045,.078),
 (-.29,1.175,.970,.090),(-.16,1.155,.885,.108)]
for i,(y,top,bottom,width) in enumerate(stations):
    for k in range(8):
        a=k*math.tau/8
        m.vertices[i*8+k].co=(width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a))

# Crest remains identical in shape; translate it rearward with the shortened skull.
for i in range(152,224):
    p=m.vertices[i].co
    p.y += .12

def reposition(name,chain,sides=8):
    mesh=bpy.data.objects[name].data
    assert len(mesh.vertices)==len(chain)*sides
    for i,(center,wx,wy) in enumerate(chain):
        c=Vector(center)
        tan=Vector(chain[min(i+1,len(chain)-1)][0])-Vector(chain[max(i-1,0)][0]); tan.normalize()
        lat=Vector((1,0,0)); lat=(lat-tan*lat.dot(tan)).normalized()
        sag=tan.cross(lat).normalized()
        for k in range(sides):
            a=k*math.tau/sides
            mesh.vertices[i*sides+k].co=c+lat*(wx*math.cos(a))+sag*(wy*math.sin(a))

for sign,label in [(-1,'L'),(1,'R')]:
    fore=[
      ((sign*.128,-.035,1.030),.080,.108),
      ((sign*.154,.020,.930),.076,.092),
      ((sign*.181,.095,.820),.061,.073),
      ((sign*.188,.155,.715),.049,.057),
      ((sign*.164,.035,.575),.036,.044),
      ((sign*.140,-.105,.410),.029,.035),
      ((sign*.126,-.215,.245),.022,.028),
      ((sign*.136,-.255,.125),.019,.024),
      ((sign*.150,-.270,.058),.030,.029)]
    hind=[
      ((sign*.118,.700,1.030),.089,.120),
      ((sign*.155,.610,.945),.086,.111),
      ((sign*.190,.495,.855),.074,.090),
      ((sign*.205,.390,.755),.058,.068),
      ((sign*.188,.575,.605),.046,.055),
      ((sign*.164,.775,.455),.037,.046),
      ((sign*.140,.955,.315),.030,.038),
      ((sign*.142,1.000,.205),.022,.028),
      ((sign*.150,.900,.060),.030,.029)]
    reposition('S_forelimb_'+label,fore)
    reposition('S_hindlimb_'+label,hind)

for o in cage.objects:
    if o.type=='MESH':
        o.data.update()
        bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(o.data); bm.free()

# Locks: torso/pelvis/tail core rings 8..18 and all toe meshes exact. Crest only translated in Y.
for idx in range(8*8,19*8):
    assert tuple(m.vertices[idx].co)==source_coords[core.name][idx], f'locked core changed {idx}'
for o in cage.objects:
    if o.type=='MESH' and '_toe_' in o.name:
        assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name], o.name+' changed'
assert all([tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name] for o in cage.objects if o.type=='MESH')
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert len(bpy.data.materials)==0 and len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v7.blend'),compress=True)
report={
 'gate':'A','status':'REVIEW_PENDING','source':'S-rebuild-v6.blend',
 'scope':'head-neck + limb chains','source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'total_cage_vertices':sum(counts.values()),'topology_preserved':True,
 'crest_shape_unchanged':True,'torso_pelvis_tail_unchanged':True,'toe_geometry_unchanged':True,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':['Shortened head-neck chain by moving only first eight core rings','Translated locked crest rearward with skull without changing crest shape','Added lateral elbow/knee/hock/wrist rhythm so frontal views no longer use parallel limb axes'],
 'limitations':['Gate A review pending; no PASS claimed']
}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v7-gate-A.json'),'w'),indent=2)
print('V7_SAVED',json.dumps(report))
