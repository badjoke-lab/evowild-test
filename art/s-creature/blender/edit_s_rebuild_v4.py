"""Execute S_REBUILD_V4_TASK.md: one structural Gate A silhouette pass from v3."""
import bpy, bmesh, math, os, json, hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v3.blend'))
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
counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}

core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
m=core.data
assert len(m.vertices)==232

# Keep the small wedge head, but lower/compact the neck and thorax read.
# Tail vertices 112:160 are deliberately untouched.
stations=[
 (-.905,1.245,1.190,.018),(-.845,1.280,1.190,.044),
 (-.735,1.335,1.195,.100),(-.635,1.350,1.205,.116),
 (-.555,1.305,1.145,.108),(-.425,1.255,1.045,.100),
 (-.275,1.205,.930,.126),(-.150,1.185,.835,.152),
 (-.040,1.180,.770,.185),(.122,1.155,.755,.170),
 (.293,1.105,.845,.116),(.473,1.095,.890,.082),
 (.644,1.125,.900,.106),(.770,1.110,.885,.112)]
for i,(y,top,bottom,width) in enumerate(stations):
    for k in range(8):
        a=k*math.tau/8
        m.vertices[i*8+k].co=(
            width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a)
        )

# Re-shape the already-connected crest plates so the first laminar sections
# emerge broadly from the posterior cranium, then sweep rearward/outward.
v3_cross=[
 [(.100,-.645,1.330,.030,.035),(.156,-.395,1.367,.030,.022),(.195,-.185,1.390,.008,.002)],
 [(.124,-.610,1.281,.035,.040),(.194,-.365,1.308,.029,.025),(.235,-.210,1.325,.008,.002)],
 [(.130,-.540,1.236,.032,.033),(.209,-.340,1.253,.027,.021),(.254,-.220,1.264,.008,.002)]]
v4_cross=[
 [(.103,-.680,1.315,.043,.047),(.152,-.455,1.338,.035,.028),(.202,-.235,1.350,.009,.003)],
 [(.122,-.655,1.270,.046,.047),(.188,-.440,1.287,.035,.029),(.243,-.255,1.296,.009,.003)],
 [(.128,-.600,1.235,.042,.040),(.205,-.420,1.244,.032,.026),(.262,-.280,1.248,.009,.003)]]
for si,sign in enumerate((1,-1)):
    for level in range(3):
        for ci,(old,new) in enumerate(zip(v3_cross[level],v4_cross[level])):
            x,y,z,t,d=old
            nx,ny,nz,nt,nd=new
            for j in range(4):
                v=m.vertices[160+si*36+level*12+ci*4+j]
                p=v.co.copy()
                sx=sign*p.x
                rx=0.0 if t==0 else (sx-x)/t
                rz=0.0 if d==0 else (p.z-z)/d
                v.co=(sign*(nx+rx*nt),ny,nz+rz*nd)

# Structural massing only: preserve chain count/connectivity and toe meshes,
# but use visibly different fore/hind joint envelopes instead of rods.
def reposition(name,chain,sides=8):
    mesh=bpy.data.objects[name].data
    assert len(mesh.vertices)==len(chain)*sides
    for i,(center,wx,wy) in enumerate(chain):
        c=Vector(center)
        tan=Vector(chain[min(i+1,len(chain)-1)][0])-Vector(chain[max(i-1,0)][0])
        tan.normalize()
        lat=Vector((1,0,0))
        lat=(lat-tan*lat.dot(tan)).normalized()
        sag=tan.cross(lat).normalized()
        for k in range(sides):
            a=k*math.tau/sides
            mesh.vertices[i*sides+k].co=(
                c+lat*(wx*math.cos(a))+sag*(wy*math.sin(a))
            )

for sign,label in ((-1,'L'),(1,'R')):
    fore=[
      ((sign*.143,-.040,1.020),.091,.126),
      ((sign*.185,.030,.895),.082,.098),
      ((sign*.188,.150,.755),.061,.073),
      ((sign*.170,-.020,.585),.040,.052),
      ((sign*.151,-.205,.300),.028,.036),
      ((sign*.148,-.252,.140),.022,.028),
      ((sign*.150,-.268,.056),.031,.030)]
    hind=[
      ((sign*.116,.720,1.010),.094,.132),
      ((sign*.160,.575,.900),.091,.124),
      ((sign*.183,.400,.765),.064,.078),
      ((sign*.174,.690,.550),.047,.060),
      ((sign*.160,1.020,.315),.034,.046),
      ((sign*.154,1.000,.205),.024,.031),
      ((sign*.150,.900,.087),.025,.023),
      ((sign*.150,.885,.053),.031,.030)]
    reposition('S_forelimb_'+label,fore)
    reposition('S_hindlimb_'+label,hind)

for o in cage.objects:
    if o.type=='MESH':
        o.data.update()
        bm=bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(o.data)
        bm.free()

# Hard scope checks.
assert all(tuple(m.vertices[i].co)==source_coords[core.name][i] for i in range(112,160)), 'Tail changed'
assert all(
    [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name]
    for o in cage.objects if o.type=='MESH'
), 'Topology changed'
assert all(
    [tuple(v.co) for v in o.data.vertices]==source_coords[o.name]
    for o in cage.objects if o.type=='MESH' and '_toe_' in o.name
), 'Toe geometry changed'
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v4.blend'),compress=True)

crest=[v.co for v in m.vertices[160:]]
report={
  'gate':'A',
  'status':'REVIEW_PENDING',
  'source':'S-rebuild-v3.blend',
  'base_remote_commit':'6aecdd8ed117cbbea368ae58d5b1ca2eb248de97',
  'v12_geometry_used':False,
  'total_cage_vertices':sum(counts.values()),
  'topology_preserved':True,
  'source_geometry_sha256':source_hash,
  'geometry_sha256':digest(),
  'no_materials':True,
  'no_animation':True,
  'no_armature':True,
  'final_retopology':False,
  'tail_unchanged':True,
  'toes_unchanged':True,
  'structural_changes':[
    'Broadened and lowered the first crest lamina sections so all six plates emerge from the posterior cranium before sweeping rearward',
    'Reduced thorax depth and compacted the neck/thorax silhouette without changing the small wedge-head direction',
    'Rebuilt forelimb ring envelopes into shoulder/upper/elbow/distal masses instead of uniform rods',
    'Rebuilt hindlimb ring envelopes into thigh/knee/lower/hock masses with a rhythm distinct from the forelimbs',
    'Kept tail and all toe geometry exact from v3'
  ],
  'crest_max_z':max(v.z for v in crest),
  'limitations':[
    'Gate A low-complexity cage only; no Gate B anatomical/surface refinement',
    'Limb and toe root cages may still overlap; production welding remains deferred',
    'No Gate A acceptance claimed'
  ]
}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v4-gate-A.json'),'w'),indent=2)
print('V4_SAVED',json.dumps(report))
