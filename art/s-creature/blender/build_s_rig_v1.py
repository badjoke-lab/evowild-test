"""S rig v1: one shared armature, deterministic weights, rigid detail/toe parenting."""
import bpy,os,json,hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v9.blend'))

cage=bpy.data.collections['S_REBUILD_GATE_A']
detail=bpy.data.collections.get('S_PRODUCTION_DETAIL')
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
crest=bpy.data.objects['S_rebuild_crest_low_fan_group']
limb_names=['S_forelimb_L','S_forelimb_R','S_hindlimb_L','S_hindlimb_R']

def digest():
    return hashlib.sha256(b''.join(
        repr(tuple(v.co)).encode()
        for o in sorted(cage.objects,key=lambda o:o.name)
        if o.type=='MESH'
        for v in o.data.vertices)).hexdigest()

source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}
source_mats={o.name:[m.name for m in o.data.materials] for o in cage.objects if o.type=='MESH'}
source_mods={o.name:[(m.name,m.type) for m in o.modifiers] for o in cage.objects if o.type=='MESH'}
detail_world={o.name:o.matrix_world.copy() for o in detail.objects} if detail else {}
crest_world=crest.matrix_world.copy()

def ring_centroid(obj,ring,sides=8):
    pts=[obj.data.vertices[ring*sides+k].co for k in range(sides)]
    return sum((p.copy() for p in pts),Vector())/sides

# Core ring centroids: 19 rings x 8.
assert len(core.data.vertices)==152
cp=[ring_centroid(core,i) for i in range(19)]

# Create isolated rig collection + armature.
rigcol=bpy.data.collections.get('S_RIG')
if rigcol is None:
    rigcol=bpy.data.collections.new('S_RIG')
    bpy.context.scene.collection.children.link(rigcol)

bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
arm=bpy.context.object
arm.name='S_RIG'
arm.data.name='S_RIG_DATA'
for c in list(arm.users_collection):
    c.objects.unlink(arm)
rigcol.objects.link(arm)
arm.hide_render=True

# Remove default bone.
for b in list(arm.data.edit_bones):
    arm.data.edit_bones.remove(b)

bones={}
def add_bone(name,head,tail,parent=None):
    b=arm.data.edit_bones.new(name)
    b.head=head
    b.tail=tail
    if (b.tail-b.head).length<1e-4:
        b.tail=b.head+Vector((0,0,.05))
    if parent:
        b.parent=bones[parent]
        b.use_connect=False
    bones[name]=b
    return b

pelvis_c=cp[13]
add_bone('root',(0,pelvis_c.y,.62),(0,pelvis_c.y,.82))
add_bone('pelvis',cp[13],cp[11],'root')
add_bone('spine',cp[11],cp[10],'pelvis')
add_bone('chest',cp[10],cp[8],'spine')
add_bone('neck',cp[8],cp[5],'chest')
add_bone('head',cp[5],cp[2],'neck')
add_bone('tail.01',cp[13],cp[15],'pelvis')
add_bone('tail.02',cp[15],cp[17],'tail.01')
add_bone('tail.03',cp[17],cp[18],'tail.02')

limb_joint_centers={}
for side,label in [('L','L'),('R','R')]:
    f=bpy.data.objects['S_forelimb_'+side]
    h=bpy.data.objects['S_hindlimb_'+side]
    fc=[ring_centroid(f,i) for i in range(12)]
    hc=[ring_centroid(h,i) for i in range(12)]
    limb_joint_centers['S_forelimb_'+side]=[[float(v.x),float(v.y),float(v.z)] for v in fc]
    limb_joint_centers['S_hindlimb_'+side]=[[float(v.x),float(v.y),float(v.z)] for v in hc]
    add_bone('fore_upper.'+side,fc[0],fc[5],'chest')
    add_bone('fore_lower.'+side,fc[5],fc[10],'fore_upper.'+side)
    add_bone('fore_foot.'+side,fc[10],fc[11],'fore_lower.'+side)
    add_bone('hind_upper.'+side,hc[0],hc[5],'pelvis')
    add_bone('hind_lower.'+side,hc[5],hc[9],'hind_upper.'+side)
    add_bone('hind_foot.'+side,hc[9],hc[11],'hind_lower.'+side)

bpy.ops.object.mode_set(mode='OBJECT')

def clear_groups(obj):
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)

def group(obj,name):
    return obj.vertex_groups.new(name=name)

def assign_ring(obj,ring,weights,sides=8):
    ids=[ring*sides+k for k in range(sides)]
    for name,w in weights.items():
        obj.vertex_groups[name].add(ids,w,'REPLACE')

def add_armature_modifier(obj):
    m=obj.modifiers.new('S_ARMATURE','ARMATURE')
    m.object=arm
    obj.modifiers.move(len(obj.modifiers)-1,0)

# Core deterministic weights.
clear_groups(core)
for n in ('pelvis','spine','chest','neck','head','tail.01','tail.02','tail.03'):
    group(core,n)
core_weights={
 0:{'head':1},1:{'head':1},2:{'head':1},3:{'head':1},
 4:{'head':.65,'neck':.35},5:{'neck':1},6:{'neck':1},
 7:{'neck':.45,'chest':.55},8:{'chest':1},9:{'chest':1},
 10:{'chest':.45,'spine':.55},11:{'spine':1},
 12:{'spine':.45,'pelvis':.55},13:{'pelvis':1},
 14:{'pelvis':.45,'tail.01':.55},15:{'tail.01':1},
 16:{'tail.01':.35,'tail.02':.65},17:{'tail.02':.45,'tail.03':.55},18:{'tail.03':1}
}
for r,w in core_weights.items(): assign_ring(core,r,w)
add_armature_modifier(core)

# Limb deterministic weights.
for side in ('L','R'):
    for prefix,objname in [('fore','S_forelimb_'+side),('hind','S_hindlimb_'+side)]:
        obj=bpy.data.objects[objname]
        clear_groups(obj)
        upper=prefix+'_upper.'+side; lower=prefix+'_lower.'+side; foot=prefix+'_foot.'+side
        for n in (upper,lower,foot): group(obj,n)
        for r in range(12):
            if r<=4: w={upper:1}
            elif r==5: w={upper:.5,lower:.5}
            elif r<=9: w={lower:1}
            elif r==10: w={lower:.45,foot:.55}
            else: w={foot:1}
            assign_ring(obj,r,w)
        add_armature_modifier(obj)

# Rigid-parent helper preserving world transform.
def bone_parent(obj,bone):
    mw=obj.matrix_world.copy()
    obj.parent=arm
    obj.parent_type='BONE'
    obj.parent_bone=bone
    obj.matrix_world=mw

bone_parent(crest,'head')

# Twelve toes rigid-parent to matching foot bone.
toe_parent_map={}
for o in cage.objects:
    if o.type!='MESH' or '_toe_' not in o.name: continue
    if o.name.startswith('S_fore_toe_'):
        side='L' if '_L_' in o.name else 'R'
        bn='fore_foot.'+side
    else:
        side='L' if '_L_' in o.name else 'R'
        bn='hind_foot.'+side
    bone_parent(o,bn)
    toe_parent_map[o.name]=bn

# Eyes and Cue Band follow head rigidly.
detail_parent_map={}
if detail:
    for o in detail.objects:
        bone_parent(o,'head')
        detail_parent_map[o.name]='head'

# Hard validation: no base cage coordinates/topology/materials changed.
for o in cage.objects:
    if o.type!='MESH': continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' coords changed'
    assert [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name],o.name+' topology changed'
    assert [m.name for m in o.data.materials]==source_mats[o.name],o.name+' materials changed'
assert digest()==source_hash
assert len(bpy.data.actions)==0

# Existing modifiers remain; core/limbs gain S_ARMATURE at index 0.
for o in cage.objects:
    if o.type!='MESH': continue
    if o.name==core.name or o.name in limb_names:
        assert o.modifiers[0].name=='S_ARMATURE' and o.modifiers[0].type=='ARMATURE'
        existing=[(m.name,m.type) for m in list(o.modifiers)[1:]]
        assert existing==source_mods[o.name],(o.name,existing,source_mods[o.name])
    else:
        assert [(m.name,m.type) for m in o.modifiers]==source_mods[o.name],o.name+' modifier stack changed'

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rig-v1.blend'),compress=True)

report={
 'stage':'rig','pass':'v1','status':'REVIEW_PENDING','source':'S-gateC-v9.blend',
 'source_geometry_sha256':source_hash,'base_geometry_sha256':digest(),
 'strategy':'KEEP_MULTI_OBJECT_SHARED_ARMATURE',
 'armature':'S_RIG','bone_count':len(arm.data.bones),
 'bones':[b.name for b in arm.data.bones],
 'skinned_meshes':[core.name]+limb_names,
 'rigid_crest_parent':'head',
 'toe_parent_map':toe_parent_map,
 'detail_parent_map':detail_parent_map,
 'base_coordinates_unchanged':True,'base_topology_unchanged':True,'materials_unchanged':True,
 'existing_modifiers_preserved':True,'armature_modifier_before_subsurf':True,
 'actions':[],
 'limb_joint_centers':limb_joint_centers,
 'limitations':['Rest-pose rig source only; deformation pose test pending','Weights are deterministic first-pass skinning, not final animation weights']
}
json.dump(report,open(os.path.join(OUT,'S-rig-v1.json'),'w'),indent=2)
print('S_RIG_V1_SAVED',json.dumps({'bone_count':report['bone_count'],'skinned_meshes':report['skinned_meshes'],'toe_count':len(toe_parent_map),'detail_count':len(detail_parent_map)}))
