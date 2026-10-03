"""Gate C v3: add a small non-destructive Bevel modifier to the crest only."""
import bpy,os,json,hashlib,math

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v2.blend'))
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
source_mods={o.name:[(m.name,m.type) for m in o.modifiers] for o in cage.objects if o.type=='MESH'}

assert not any(m.type=='BEVEL' for m in crest.modifiers)
bev=crest.modifiers.new('S_C3_CREST_BEVEL','BEVEL')
bev.width=.006
bev.segments=2
bev.limit_method='ANGLE'
bev.angle_limit=math.radians(20.0)

# Keep laminar base faces flat; bevel alone provides the production edge highlight.
for p in crest.data.polygons:
    p.use_smooth=False

# Hard locks: every base vertex and face exact.
for o in cage.objects:
    if o.type!='MESH': continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' coords changed'
    assert [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name],o.name+' topology changed'
    if o.name!=crest.name:
        assert [(m.name,m.type) for m in o.modifiers]==source_mods[o.name],o.name+' modifiers changed'
assert digest()==source_hash
assert len(bpy.data.materials)==0 and len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v3.blend'),compress=True)
report={
 'gate':'C','pass':'v3','status':'REVIEW_PENDING','source':'S-gateC-v2.blend',
 'scope':'crest Bevel modifier only',
 'source_geometry_sha256':source_hash,'base_geometry_sha256':digest(),
 'base_coordinates_unchanged':True,'base_topology_unchanged':True,
 'crest_bevel_width':.006,'crest_bevel_segments':2,'crest_bevel_angle_degrees':20.0,
 'all_other_modifier_stacks_unchanged':True,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':['Added a two-segment angle-limited Bevel modifier to the crest group only'],
 'limitations':['Gate C v3 review pending','No destructive welding/retopology or materials yet']
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v3.json'),'w'),indent=2)
print('GATE_C_V3_SAVED',json.dumps(report))
