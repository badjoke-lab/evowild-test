"""Original S type geometry. Run in an EMPTY Blender scene, via Blender MCP.
No mesh, texture, coordinate or script from an earlier model is loaded.
Coordinates are newly authored from 00_s_type_modeling_image_v1.png.
"""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
import bmesh
ROOT=Path('/Users/lyla/evowild-s-zero-20261017/art/s-creature/zero-rebuild-20261017')
random.seed(17)
assert not any(o.type=='MESH' for o in bpy.context.scene.objects), 'Requires empty scene'
scene=bpy.context.scene
scene.name='S_ZERO_STUDIO'
scene['origin']='Zero geometry; authored from canonical PNG only; no imported mesh'
scene['reference_sha256']='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
scene['stage']='BLOCKOUT'
scene['axis']='X rearward, Y left-right, Z up; ground Z=0'
model=bpy.data.collections.new('S_ZERO_CREATURE'); scene.collection.children.link(model)
root=bpy.data.objects.new('S_ZERO_ROOT',None); model.objects.link(root)
def enum_set(obj,key,value):
    prop=obj.bl_rna.properties[key]
    valid=[i.identifier for i in prop.enum_items]
    if value in valid: setattr(obj,key,value)
    else: raise ValueError((key,value,valid))
def mat(name,c,metal=0.0,rough=.48,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(*c,1)
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    if emission:
        bs.inputs['Emission Color'].default_value=(*c,1);bs.inputs['Emission Strength'].default_value=emission
    return m
DARK=mat('S | graphite dermis',(.035,.046,.067),.12)
RIDGE=mat('S | slate tendons',(.085,.108,.15),.18)
WHITE=mat('S | pearl shell',(.69,.76,.84),.13,.38)
LIGHT=mat('S | ivory facet',(.86,.88,.90),.08,.42)
SHADE=mat('S | blue grey facet',(.34,.43,.57),.15,.44)
BLUE=mat('S | cobalt recess',(.018,.23,.52),.32,.32)
CYAN=mat('S | cue cyan',(.025,.66,.95),.25,.3,.5)
BLACK=mat('S | socket',(.006,.012,.02),.1,.34)
GOLD=mat('S | cue warm alloy',(.52,.35,.13),.7,.28)
MATS=[WHITE,LIGHT,SHADE,BLUE]

def mesh_obj(name,vs,fs,material,collection=model):
    me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(vs,[],fs);me.update()
    ob=bpy.data.objects.new(name,me);collection.objects.link(ob)
    if collection==model: ob.parent=root
    ob.data.materials.append(material);ob['provenance']='New procedural mesh from reference PNG'
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    return ob

def smooth(ob):
    for p in ob.data.polygons:p.use_smooth=True

def active(ob):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob

def sample(rows,steps=4):
    out=[]
    for i in range(len(rows)-1):
        a=rows[max(0,i-1)];b=rows[i];c=rows[i+1];d=rows[min(len(rows)-1,i+2)]
        for k in range(steps):
            t=k/steps
            out.append(tuple(.5*(2*bb+(-aa+cc)*t+(2*aa-5*bb+4*cc-dd)*t*t+(-aa+3*bb-3*cc+dd)*t*t*t) for aa,bb,cc,dd in zip(a,b,c,d)))
    out.append(rows[-1]);return out

def tube(name,rows,material=DARK,sides=16,steps=4):
    # rows x,y,z, lateral radius, sagittal radius
    rows=sample(rows,steps);vs=[];fs=[]
    for i,r in enumerate(rows):
        pos=Vector(r[:3]);a=Vector(rows[max(0,i-1)][:3]);b=Vector(rows[min(len(rows)-1,i+1)][:3])
        t=(b-a).normalized();v=Vector((0,1,0));v=(v-v.dot(t)*t).normalized();u=t.cross(v).normalized()
        for j in range(sides):
            th=2*math.pi*j/sides
            p=pos+v*(max(.002,r[3])*math.cos(th))+u*(max(.002,r[4])*math.sin(th))
            vs.append(tuple(p))
    for i in range(len(rows)-1):
        for j in range(sides):fs.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    vs.extend([tuple(rows[0][:3]),tuple(rows[-1][:3])]);a=len(vs)-2;b=a+1
    for j in range(sides):
        fs.append((a,(j+1)%sides,j));fs.append((b,(len(rows)-1)*sides+j,(len(rows)-1)*sides+(j+1)%sides))
    ob=mesh_obj(name,vs,fs,material);smooth(ob);return ob

def patch(name,outline,bulge,material=WHITE,facets=True,sub=1):
    # Closed curved anatomical shell, domed in 3D, inset backing embedded into dermis.
    pts=[Vector(p) for p in outline];n=len(pts);c=sum(pts,Vector())/n;v=Vector(bulge)
    vs=[tuple(p) for p in pts]
    vs += [tuple(c+(p-c)*.56+v*.83) for p in pts]
    vs += [tuple(c+v),tuple(c-v*.30)]
    fs=[]
    for j in range(n):
        k=(j+1)%n
        fs.extend([(j,k,n+k,n+j),(n+j,n+k,2*n),(k,j,2*n+1)])
    ob=mesh_obj(name,vs,fs,material)
    if facets:
        for m in MATS:
            if m!=material:ob.data.materials.append(m)
        for i,p in enumerate(ob.data.polygons):
            if i%3!=2 and random.random()<.40:p.material_index=random.choice([0,1,2])
    if sub:
        mod=ob.modifiers.new('rounded anatomical volume','SUBSURF');mod.levels=sub;mod.render_levels=sub
        active(ob);bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob

def side_patch(name,coords,y,bulge=.06,material=WHITE,facets=True,sub=1):
    return patch(name,[(x,y,z) for x,z in coords],(0,math.copysign(bulge,y),0),material,facets,sub)

def ell(name,loc,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
    ob=bpy.context.object;ob.name=name;ob.scale=scale
    for coll in list(ob.users_collection):coll.objects.unlink(ob)
    model.objects.link(ob);ob.parent=root;ob.data.materials.append(material)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);smooth(ob);return ob

# Continuous flesh: torso with tucked waist, high diagonal neck, small tapered skull.
core=[]
core.append(tube('core ribcage',[
(-1.10,0,1.66,.12,.17),(-.94,0,1.65,.25,.30),(-.66,0,1.65,.31,.33),(-.32,0,1.70,.27,.26),(.05,0,1.76,.205,.195),(.43,0,1.78,.19,.17),(.72,0,1.75,.25,.24),(.99,0,1.65,.21,.25),(1.11,0,1.64,.08,.12)]))
core.append(tube('core neck',[
(-1.00,0,1.56,.18,.23),(-1.22,0,1.78,.17,.22),(-1.49,0,1.96,.12,.165),(-1.76,0,2.13,.095,.13),(-1.93,0,2.19,.105,.105)]))
core.append(tube('core head',[
(-2.37,0,1.95,.025,.028),(-2.25,0,2.045,.068,.058),(-2.08,0,2.16,.11,.108),(-1.92,0,2.20,.125,.12),(-1.82,0,2.15,.08,.08)],steps=5))

# Staggered stance is visible in the sheet; transverse anatomy inferred bilaterally.
legs={
'FORE_NEAR':[(-.83,-.26,1.69,.20,.24),(-.74,-.31,1.42,.145,.16),(-.52,-.30,1.13,.09,.115),(-.44,-.30,.84,.057,.085),(-.32,-.29,.40,.04,.055),(-.39,-.29,.20,.05,.07),(-.45,-.29,.11,.07,.07)],
'FORE_FAR':[(-.96,.25,1.65,.18,.22),(-.95,.29,1.37,.13,.16),(-1.03,.28,1.08,.08,.1),(-1.19,.28,.74,.05,.075),(-1.37,.28,.37,.039,.05),(-1.46,.28,.14,.055,.065)],
'HIND_NEAR':[(.80,-.235,1.72,.20,.27),(.99,-.27,1.39,.18,.25),(1.17,-.28,1.12,.105,.14),(1.58,-.29,.91,.077,.095),(1.76,-.29,.57,.045,.06),(1.98,-.28,.23,.045,.065),(1.97,-.28,.10,.07,.07)],
'HIND_FAR':[(.67,.235,1.68,.18,.26),(.66,.28,1.37,.15,.21),(.71,.28,1.11,.10,.13),(1.08,.29,.87,.071,.085),(.87,.29,.49,.045,.065),(.73,.28,.22,.045,.06),(.64,.28,.09,.07,.07)]}
for name,rows in legs.items():core.append(tube('core '+name,rows))
core.append(tube('core tail',[(.94,0,1.88,.12,.12),(1.28,0,1.88,.12,.10),(1.63,0,1.73,.08,.08),(1.96,0,1.46,.045,.045),(2.27,0,1.08,.012,.015)],steps=5))
# Voxel-union ONLY these newly authored flesh volumes.
active(core[0])
for o in core:o.select_set(True)
bpy.ops.object.join();body=bpy.context.object;body.name='S_ZERO_BODY_CONTINUOUS'
body.data.remesh_voxel_size=.023
bpy.ops.object.voxel_remesh()
mod=body.modifiers.new('soft tissue transitions','SMOOTH');mod.factor=.65;mod.iterations=4
bpy.ops.object.modifier_apply(modifier=mod.name)
smooth(body);body['construction']='New lofts unioned at 0.023; no prior asset'

# Shell masses are deliberately curved, with distinct scapula/deltoid/upper-arm volumes.
for s,lab in [(-1,'N'),(1,'F')]:
    side_patch('DELTOID_'+lab,[(-1.08,1.77),(-.94,1.94),(-.72,1.92),(-.59,1.78),(-.60,1.55),(-.72,1.40),(-.95,1.50),(-1.09,1.62)],s*.29,.19)
    side_patch('SCAPULA_'+lab,[(-.94,1.92),(-.69,2.02),(-.39,2.02),(-.21,1.96),(-.36,1.80),(-.63,1.73),(-.78,1.79)],s*.235,.12)
    side_patch('RIB_SHELL_'+lab,[(-.44,1.89),(-.17,1.92),(.10,1.87),(.21,1.73),(.05,1.61),(-.18,1.57),(-.38,1.68)],s*.245,.10)
    side_patch('LOWER_RIB_'+lab,[(-.70,1.44),(-.41,1.45),(-.10,1.56),(.18,1.70),(.0,1.46),(-.37,1.32),(-.61,1.34)],s*.19,.045,SHADE,False)
    side_patch('PELVIS_'+lab,[(.47,1.87),(.65,1.99),(.92,1.93),(1.08,1.75),(1.22,1.32),(1.05,1.24),(.86,1.47),(.68,1.77)],s*.245,.14)
    side_patch('THIGH_SHELL_'+lab,[(.83,1.88),(1.01,1.79),(1.18,1.53),(1.26,1.20),(1.07,1.30),(.92,1.55)],s*.32,.06)
    # Small back-of-jaw / nape fins, clearly supported in reference.
    side_patch('NAPE_FIN_'+lab,[(-1.97,2.22),(-1.81,2.30),(-1.60,2.28),(-1.76,2.20)],s*.11,.025,DARK,False,0)
    side_patch('CHEEK_'+lab,[(-2.27,1.99),(-2.14,2.12),(-1.96,2.17),(-1.99,2.04),(-2.17,1.97)],s*.085,.035,WHITE,True,1)
    side_patch('BROW_'+lab,[(-2.30,2.08),(-2.16,2.23),(-1.99,2.29),(-2.02,2.19),(-2.17,2.12)],s*.081,.035,WHITE,True,1)
    side_patch('NECK_TENDON_'+lab,[(-1.92,2.14),(-1.64,2.00),(-1.33,1.76),(-1.08,1.52),(-1.19,1.72),(-1.62,2.10)],s*.095,.035,RIDGE,False,1)
    # Main paired swept crown, solid lens section rather than planes.
    horn=[(-2.19,2.19),(-1.98,2.43),(-1.65,2.64),(-1.18,2.83),(-.62,3.00),(-.08,3.11),(-.70,2.89),(-1.25,2.67),(-1.69,2.42),(-1.98,2.23)]
    side_patch('CROWN_MAIN_'+lab,horn,s*.115,.038,DARK,False,0)
    side_patch('CROWN_IVORY_RIDGE_'+lab,[(-2.19,2.19),(-1.98,2.44),(-1.65,2.65),(-1.18,2.84),(-.62,3.00),(-.10,3.11),(-1.20,2.79),(-1.70,2.56),(-2.03,2.31)],s*.153,.009,WHITE,False,0)
    side_patch('CROWN_BLUE_'+lab,[(-1.97,2.26),(-1.64,2.43),(-1.27,2.54),(-.67,2.82),(-1.23,2.64),(-1.66,2.47)],s*.14,.014,BLUE,False,0)
    # Eyes stay small. Cue band uses domed capsules and metal rim.
    ell('EYE_SOCKET_'+lab,(-2.13,s*.101,2.115),(.071,.022,.033),BLACK)
    ell('EYE_'+lab,(-2.155,s*.123,2.119),(.021,.011,.012),CYAN)
    ell('CUE_FRAME_'+lab,(-1.984,s*.147,2.235),(.156,.034,.073),DARK)
    ell('CUE_RIM_'+lab,(-1.984,s*.173,2.235),(.133,.016,.055),GOLD)
    ell('CUE_FACE_'+lab,(-1.973,s*.186,2.236),(.11,.014,.042),RIDGE)
    ell('CUE_SIGNAL_'+lab,(-1.945,s*.200,2.241),(.066,.007,.015),CYAN)
    ell('CUE_ROUND_'+lab,(-2.043,s*.193,2.229),(.029,.013,.030),GOLD)
    ell('CUE_DOT_'+lab,(-2.044,s*.205,2.23),(.017,.008,.019),CYAN)

# A narrow ivory dorsal mantle follows the neck, back, and pelvic bridge.
tube('DORSAL_MANTLE',[(-1.82,0,2.24,.045,.025),(-1.48,0,2.13,.075,.032),(-1.08,0,1.99,.10,.035),(-.66,0,1.99,.12,.05),(-.23,0,1.98,.13,.028),(.20,0,1.97,.10,.025),(.62,0,1.99,.08,.028),(.92,0,1.93,.07,.025)],WHITE,12,4)
for i,(x,z,h,l) in enumerate([(-1.27,2.03,.07,.18),(-1.01,2.03,.13,.24),(-.76,2.02,.24,.44)]):
    for s in [-1,1]:
        side_patch('DORSAL_CREST_%d_%d'%(i,s),[(x-.12,z-.06),(x+.02,z+h*.65),(x+l,z+h),(x+.19,z+h*.40),(x+.10,z-.06)],s*.09,.025,DARK,False,0)
        side_patch('DORSAL_BLUE_%d_%d'%(i,s),[(x+.02,z+h*.50),(x+l*.83,z+h*.94),(x+.17,z+h*.42)],s*.115,.005,BLUE,False,0)

# Limb surface contours and split racing toes.
for name,rows in legs.items():
    near='NEAR' in name;s=-1 if near else 1
    y=rows[2][1]+s*.04
    if name.startswith('FORE'):
        a,b,c=rows[1],rows[2],rows[3]
        side_patch('BRACHIAL_'+name,[(a[0]-.10,a[2]+.14),(a[0]+.09,a[2]+.08),(b[0]+.075,b[2]+.02),(c[0]+.03,c[2]-.03),(b[0]-.07,b[2]-.04)],y+s*.065,.05,WHITE,True,1)
    hock=rows[-4] if name.startswith('HIND') else rows[2]
    ankle=rows[-2]
    x0,z0=hock[0],hock[2];x1,z1=ankle[0],ankle[2]
    side_patch('CANNON_RIDGE_'+name,[(x0-.055,z0+.07),(x0+.08,z0+.13),(x0+.07,z0-.10),(x1+.025,z1),(x1-.035,z1+.02)],y,.035,RIDGE,False,1)
    side_patch('ANKLE_FIN_'+name,[(x1-.035,z1-.03),(x1+.08,z1+.16),(x1+.10,z1+.05),(x1+.05,z1-.04)],y+s*.01,.018,DARK,False,0)
    foot=rows[-1];fx,fy=foot[0],foot[1]
    for k in [-1,1]:
        yy=fy+k*.045
        toe=tube('TOE_'+name+'_'+str(k),[(fx+.035,yy,.16,.035,.055),(fx-.025,yy,.115,.04,.065),(fx-.12,yy,.045,.037,.04),(fx-.17,yy,.025,.005,.014)],DARK,10,3)
        side_patch('TOE_IVORY_'+name+'_'+str(k),[(fx-.15,.026),(fx-.06,.14),(fx+.005,.14),(fx-.035,.043)],yy+s*.025,.014,WHITE,False,0)
        side_patch('TOE_CYAN_'+name+'_'+str(k),[(fx-.137,.03),(fx-.065,.12),(fx-.049,.12),(fx-.10,.038)],yy+s*.04,.004,BLUE,False,0)

# Tail is a flexible core with tapering overlapping narrow blade shells.
for i in range(7):
    t=i/6
    x=1.02+1.12*t;z=1.91-.62*t*t
    length=.40+.13*t
    for s in [-1,1]:
        yy=s*(.075+.025*math.sin(t*math.pi))
        outline=[(x-.12,yy,z+.015),(x+.06,yy+s*.055,z+.045),(x+length,yy+s*.055*(1-t),z-.12-.20*t),(x+.16,yy+s*.12,z-.13),(x-.03,yy+s*.08,z-.06)]
        ob=patch('TAIL_BLADE_%d_%d'%(i,s),outline,(0,s*.018,.018),DARK,False,0)
        patch('TAIL_BLUE_%d_%d'%(i,s),[outline[0],outline[1],(x+length*.85,yy+s*.053,z-.09-.16*t),(x+.10,yy+s*.065,z-.03)],(0,s*.021,.012),BLUE,False,0)
# slender terminal blade
tube('TAIL_TIP',[(2.08,0,1.37,.042,.06),(2.32,0,1.04,.024,.045),(2.48,0,.73,.002,.002)],DARK,10,5)

# Neutral review studio, authored independently of the model.
studio=bpy.data.collections.new('STUDIO');scene.collection.children.link(studio)
groundmat=mat('Studio matte',(.19,.23,.28),0,.9)
mesh_obj('Ground',[(-200,-200,-.018),(200,-200,-.018),(200,200,-.018),(-200,200,-.018)],[(0,1,2,3)],groundmat,studio)
world=bpy.data.worlds.new('Neutral world');world.use_nodes=True;scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.32,.39,.48,1);bg.inputs[1].default_value=.65
for name,loc,power,size in [('Key',(-3,-4,7),1300,5),('Fill',(-1,4,4),1000,4),('Rim',(4,2,6),1600,3)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    ob=bpy.data.objects.new(name,d);studio.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1.5))-ob.location).to_track_quat('-Z','Y').to_euler()
try:scene.render.engine='BLENDER_EEVEE_NEXT'
except TypeError:raise
scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.render.image_settings.color_mode='RGBA'
# Retain startup color management (dynamic enums are not statically enumerable).
print('Color management:',scene.view_settings.view_transform,scene.view_settings.look)
scene.render.fps=24
for name,direction,scale in [('SIDE',(0,-1,0),5.65),('FRONT',(-1,0,0),4.65),('FRONT34',(-.88,-.48,.06),4.65),('REAR34',(.78,-.63,.07),4.65),('BACK',(1,0,0),4.65)]:
    cd=bpy.data.cameras.new(name);cd.type='ORTHO';cd.ortho_scale=scale
    co=bpy.data.objects.new('CAM_'+name,cd);studio.objects.link(co)
    co.location=Vector((.03,0,1.56))+Vector(direction).normalized()*12
    co.rotation_euler=(Vector((.03,0,1.56))-co.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['CAM_FRONT34']
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.overlay.show_overlays=False
        area.spaces.active.shading.type='MATERIAL'
        area.spaces.active.region_3d.view_perspective='CAMERA'
active(body)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'S_ZERO_BLOCKOUT.blend'),compress=True)
print(json.dumps({'stage':'BLOCKOUT','meshes':sum(o.type=='MESH' for o in model.objects),'body_vertices':len(body.data.vertices),'file':str(ROOT/'S_ZERO_BLOCKOUT.blend')}))
