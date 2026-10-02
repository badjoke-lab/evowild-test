"""Gate A v8: integrate limb roots and taper distal segments from v7. Core body/crest/neck/tail and toes stay locked."""
import bpy,bmesh,math,os,json,hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v7.blend'))
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
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}
counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}

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
            mesh.vertices[i*sides+k].co=c+lat*(wx*math.cos(a))+sag*(wy*math.sin(a))

# Roots move slightly inboard and deeper into body overlap, then taper progressively.
# Frontal-plane rhythm from v7 is preserved and strengthened without moving toes.
for sign,label in [(-1,'L'),(1,'R')]:
    fore=[
      ((sign*.112,-.020,1.025),.098,.126),
      ((sign*.142,.020,.930),.086,.104),
      ((sign*.176,.090,.820),.068,.082),
      ((sign*.190,.155,.715),.055,.064),
      ((sign*.166,.035,.575),.042,.050),
      ((sign*.143,-.105,.410),.033,.039),
      ((sign*.126,-.215,.245),.025,.031),
      ((sign*.136,-.255,.125),.020,.025),
      ((sign*.150,-.270,.058),.030,.029)]
    hind=[
      ((sign*.104,.705,1.020),.108,.136),
      ((sign*.142,.610,.940),.098,.126),
      ((sign*.184,.500,.850),.081,.098),
      ((sign*.207,.395,.755),.064,.076),
      ((sign*.188,.575,.605),.050,.059),
      ((sign*.164,.775,.455),.039,.048),
      ((sign*.140,.955,.315),.031,.039),
      ((sign*.142,1.000,.205),.022,.028),
      ((sign*.150,.900,.060),.030,.029)]
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

# Hard locks: core body/head/crest/neck/tail and toe geometry exact from v7.
assert [tuple(v.co) for v in core.data.vertices]==source_coords[core.name], 'Core geometry changed'
for o in cage.objects:
    if o.type=='MESH' and '_toe_' in o.name:
        assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name], o.name+' changed'
assert all(
    [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name]
    for o in cage.objects if o.type=='MESH'
), 'Topology changed'
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v8.blend'),compress=True)
report={
  'gate':'A',
  'status':'REVIEW_PENDING',
  'source':'S-rebuild-v7.blend',
  'scope':'limb-root integration + distal taper only',
  'source_geometry_sha256':source_hash,
  'geometry_sha256':digest(),
  'total_cage_vertices':sum(counts.values()),
  'topology_preserved':True,
  'core_geometry_unchanged':True,
  'toe_geometry_unchanged':True,
  'no_materials':True,
  'no_animation':True,
  'no_armature':True,
  'changes':[
    'Moved first fore/hind limb rings slightly inboard and increased root cross-sections to overlap body masses more gradually',
    'Introduced progressive proximal-to-distal cross-section taper instead of near-uniform tubes',
    'Preserved v7 fore/hind frontal-plane joint rhythm and exact toe endpoints'
  ],
  'limitations':['Gate A review pending; no PASS claimed','No Gate B welding or anatomical surface refinement']
}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v8-gate-A.json'),'w'),indent=2)
print('V8_SAVED',json.dumps(report))
