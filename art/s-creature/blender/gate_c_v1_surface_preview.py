"""Gate C v1: non-destructive one-level Catmull-Clark surface-continuity preview."""
import bpy,os,json,hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateB-v4.blend'))
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

targets=[
 'S_rebuild_core_head_crest_neck_torso_tail',
 'S_forelimb_L','S_forelimb_R','S_hindlimb_L','S_hindlimb_R'
]
for name in targets:
    o=bpy.data.objects.get(name)
    assert o is not None and o.type=='MESH',name
    assert not any(m.type=='SUBSURF' for m in o.modifiers),name+' already has subsurf'
    mod=o.modifiers.new('S_C1_SUBSURF','SUBSURF')
    mod.subdivision_type='CATMULL_CLARK'
    mod.levels=1
    mod.render_levels=1
    for p in o.data.polygons:
        p.use_smooth=True

# Crest and toes stay modifier-free.
for o in cage.objects:
    if o.type!='MESH':
        continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' base coords changed'
    assert [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name],o.name+' topology changed'
    if o.name not in targets:
        assert not any(m.type=='SUBSURF' for m in o.modifiers),o.name+' unexpected subsurf'

assert digest()==source_hash
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v1.blend'),compress=True)
report={
 'gate':'C','pass':'v1','status':'REVIEW_PENDING','source':'S-gateB-v4.blend',
 'scope':'non-destructive one-level Catmull-Clark preview on core + four limb meshes',
 'source_geometry_sha256':source_hash,'base_geometry_sha256':digest(),
 'base_coordinates_unchanged':True,'base_topology_unchanged':True,
 'subsurf_targets':targets,'subsurf_level':1,
 'crest_modifier_free':True,'toes_modifier_free':True,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':['Added one-level Catmull-Clark modifiers to core and four limb meshes','Enabled smooth shading on those five source meshes'],
 'limitations':['Gate C v1 visual review pending','No destructive retopology, welding, materials, rigging or Cue Band yet']
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v1.json'),'w'),indent=2)
print('GATE_C_V1_SAVED',json.dumps(report))
