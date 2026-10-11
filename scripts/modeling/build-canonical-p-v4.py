"""Canonical P study. Blender 4.3+: blender -b -t 4 --python scripts/modeling/build-canonical-p.py
Source is deliberately deterministic/editable; no donor model or image-to-3D service.
Coordinates: Blender +Z up, -X forward, metres. glTF export converts to +Y up.
"""
import bpy, math, json, sys, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'public/models/evowild-p'
EVIDENCE = ROOT / 'docs/evidence/p-canonical-3d-v4-20261011'
OFFLINE = ROOT / 'work/p-canonical-v4/blender-renders'
OFFLINE.mkdir(parents=True,exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
parts = []
def material(name, rgb, roughness=.6, metal=0, emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*rgb,1)
    bs.inputs['Roughness'].default_value=roughness; bs.inputs['Metallic'].default_value=metal
    if emission:
        bs.inputs['Emission Color'].default_value=(*rgb,1); bs.inputs['Emission Strength'].default_value=emission
    return m
# Linear colours: muted oxblood against cool charcoal, as in P.webp.
red=material('P • oxblood dorsal integument',(.22,.024,.024),.63)
redlight=material('P • warm ridge planes',(.31,.041,.032),.57)
reddark=material('P • deep red transitions',(.17,.022,.024),.7)
skin=material('P • charcoal connective body',(.026,.034,.046),.72)
slate=material('P • slate ventral planes',(.075,.095,.125),.68)
edge=material('P • dark anatomical seams',(.023,.029,.035),.69)
horn=material('P • graphite crest and claws',(.045,.052,.061),.5)
ridge=material('P • pale crest edges',(.25,.28,.29),.56)
cyan=material('P • restrained cyan eye and cue',(.14,.74,.80),.32,0,1.3)
parts=[]
def finish(obj,name,mat,bone='body',sub=0,smooth=True):
    obj.name=name; obj.data.materials.append(mat)
    for p in obj.data.polygons: p.use_smooth=smooth
    if sub:
        mod=obj.modifiers.new('Sculpt surface continuity','SUBSURF'); mod.levels=sub
        bpy.context.view_layer.objects.active=obj; bpy.ops.object.modifier_apply(modifier=mod.name)
    obj['anatomy']=bone; parts.append(obj)
    return obj

def mesh(name,verts,faces,mat,bone='body',sub=1):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    obj=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(obj)
    # Recalculate consistently; loft orientation is independent of path direction.
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT');obj.select_set(False)
    return finish(obj,name,mat,bone,sub)

def loft(name,sections,mat,bone='body',n=16,sub=2):
    """A sequence of (x,y,z,lateral radius,vertical radius) cross sections.
    Rings follow the XZ tangent, permitting sculpted bends and anisotropic taper.
    """
    verts=[]
    for i,s in enumerate(sections):
        c=Vector(s[:3]); a=Vector(sections[max(0,i-1)][:3]); b=Vector(sections[min(len(sections)-1,i+1)][:3])
        tangent=(b-a).normalized(); u=Vector((0,1,0)); v=tangent.cross(u).normalized()
        for j in range(n):
            t=2*math.pi*j/n
            verts.append(tuple(c+u*(math.cos(t)*s[3])+v*(math.sin(t)*s[4])))
    faces=[tuple(reversed(range(n)))]
    for i in range(len(sections)-1):
        for j in range(n): faces.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    faces.append(tuple((len(sections)-1)*n+j for j in range(n)))
    return mesh(name,verts,faces,mat,bone,sub)

def lobe(name,center,scale,mat,bone='body',angle=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=center)
    o=bpy.context.object;o.scale=scale;o.rotation_euler.y=angle
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,bone)

def panel(name,outline,bulge,mat,bone='body'):
    """Sculpted shell from anatomical contour, not an accessory plate.
    Outline is a rim on the existing body. bulge gives the outer muscle apex.
    """
    c=Vector(bulge); pts=[Vector(p) for p in outline]; n=len(pts)
    verts=[tuple(p) for p in pts]
    verts.extend(tuple(p*.52+c*.48) for p in pts)
    verts.append(tuple(c)); faces=[]
    for j in range(n): faces += [(j,(j+1)%n,n+(j+1)%n,n+j),(n+j,n+(j+1)%n,2*n)]
    # Shell is closed inward and smoothed, keeping integrated, rooted borders.
    inner=sum(pts,Vector())/n;inner.y*=.93
    verts.append(tuple(inner));faces += [(j,2*n+1,(j+1)%n) for j in range(n)]
    return mesh(name,verts,faces,mat,bone,2)

def stroke(name,coords,radius,mat,bone='body'):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=radius;cu.bevel_resolution=2
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(coords)-1)
    for p,co in zip(sp.bezier_points,coords):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
    return finish(o,name,mat,bone)

# Continuous heavy chest, arched shoulder, compact waist and substantial pelvis.
loft('P continuous thorax',[
(-1.38,0,2.04,.14,.25),(-1.2,0,2.04,.39,.48),(-.91,0,2.02,.58,.65),
(-.54,0,1.97,.65,.73),(-.12,0,1.88,.54,.60),(.29,0,1.74,.44,.47),
(.66,0,1.60,.45,.46),(.98,0,1.57,.39,.38),(1.22,0,1.51,.24,.25),(1.34,0,1.47,.05,.09)],skin)
loft('Short thick rising neck',[
(-1.02,0,2.11,.36,.37),(-1.28,0,2.26,.35,.34),(-1.53,0,2.36,.27,.28),(-1.72,0,2.38,.23,.22)],skin,'neck')
loft('Dorsal oxblood mantle',[
(-1.22,0,2.29,.22,.19),(-.98,0,2.49,.36,.23),(-.67,0,2.55,.43,.20),
(-.37,0,2.48,.40,.15),(-.10,0,2.33,.34,.15),(.20,0,2.14,.30,.15),(.54,0,1.92,.29,.12),(.92,0,1.77,.22,.12)],red)
for side in [-1,1]:
    S=lambda x,y,z:(x,side*y,z)
    # Soft convex lobes with dark channels between them reproduce the large painted masses.
    panel('Scapular red muscle '+str(side),[S(-1.11,.29,2.45),S(-.82,.44,2.65),S(-.51,.52,2.57),S(-.24,.52,2.34),S(-.18,.51,1.97),S(-.41,.56,1.77),S(-.68,.57,1.73),S(-.96,.47,2.08)],S(-.58,.61,2.21),red)
    panel('Shoulder ridge highlight '+str(side),[S(-.89,.44,2.55),S(-.65,.51,2.61),S(-.32,.55,2.4),S(-.20,.58,2.14),S(-.35,.65,2.28)],S(-.49,.68,2.48),redlight)
    panel('Rear chest lobe '+str(side),[S(-.11,.47,2.31),S(.20,.43,2.12),S(.37,.45,1.75),S(.20,.50,1.51),S(-.04,.57,1.64),S(-.21,.60,1.97)],S(.08,.62,1.93),reddark)
    panel('Pelvic red muscle '+str(side),[S(.39,.32,2.00),S(.71,.38,1.93),S(1.08,.32,1.70),S(1.07,.44,1.36),S(.83,.50,1.27),S(.55,.53,1.51)],S(.80,.57,1.66),red)
    panel('Pectoral slate keel '+str(side),[S(-1.18,.23,1.91),S(-.91,.51,1.89),S(-.54,.58,1.62),S(-.28,.39,1.38),S(-.53,.08,1.24),S(-.95,.08,1.40)],S(-.81,.44,1.50),slate)
    panel('Thoracic ventral plane '+str(side),[S(-.35,.43,1.58),S(.10,.44,1.52),S(.39,.30,1.35),S(.04,.12,1.22),S(-.34,.08,1.22)],S(-.02,.39,1.32),slate)
    panel('Neck red sweep '+str(side),[S(-1.69,.19,2.51),S(-1.38,.27,2.55),S(-1.10,.35,2.42),S(-1.09,.36,2.13),S(-1.31,.29,2.17)],S(-1.36,.39,2.40),reddark,'neck')

# Restrained, forward wedge head. Jaw, cheek and brow have independent planes.
loft('Directional skull',[
(-2.32,0,2.23,.055,.050),(-2.25,0,2.29,.115,.092),(-2.09,0,2.35,.19,.145),
(-1.93,0,2.43,.245,.19),(-1.75,0,2.45,.245,.18),(-1.56,0,2.42,.12,.11)],skin,'head',8,0)
loft('Lower jaw',[
(-2.31,0,2.174,.052,.032),(-2.20,0,2.176,.125,.065),(-2.02,0,2.205,.18,.085),(-1.85,0,2.24,.20,.105),(-1.70,0,2.34,.14,.09)],slate,'head',8,0)
for side in [-1,1]:
    S=lambda x,y,z:(x,side*y,z)
    panel('Angular cheek '+str(side),[S(-2.13,.18,2.25),S(-1.95,.285,2.41),S(-1.62,.22,2.47),S(-1.72,.28,2.23),S(-1.94,.25,2.16)],S(-1.88,.33,2.31),skin,'head')
    panel('Red brow '+str(side),[S(-2.25,.14,2.35),S(-2.03,.24,2.53),S(-1.78,.23,2.62),S(-1.64,.25,2.52),S(-1.99,.28,2.39)],S(-1.99,.30,2.52),red,'head')
    stroke('Mouth seam '+str(side),[S(-2.31,.10,2.20),S(-2.13,.18,2.22),S(-1.97,.263,2.22),S(-1.83,.273,2.28)],.014,edge,'head')
    lobe('Eye socket '+str(side),S(-1.999,.262,2.436),(.082,.018,.041),edge,'head',-.3)
    lobe('Cyan eye slit '+str(side),S(-2.009,.287,2.443),(.043,.012,.018),cyan,'head',-.3)
    lobe('Nostril '+str(side),S(-2.257,.146,2.305),(.036,.015,.021),edge,'head',-.25)
    # Two rooted swept cranial blades, matching the narrow backward rake in the reference.
    loft('Swept crest '+str(side),[S(-2.03,.13,2.50)+(.043,.055),S(-1.87,.16,2.59)+(.044,.083),S(-1.54,.19,2.73)+(.040,.076),S(-1.14,.22,2.86)+(.020,.045),S(-.86,.23,2.90)+(.003,.004)],horn,'head',10,1)
    loft('Crest red ridge '+str(side),[S(-1.99,.13,2.535)+(.026,.030),S(-1.72,.175,2.70)+(.022,.030),S(-1.29,.214,2.85)+(.014,.023),S(-.87,.227,2.897)+(.002,.003)],redlight,'head',8,1)
    stroke('Crest edge '+str(side),[S(-1.91,.20,2.62),S(-1.59,.231,2.76),S(-1.15,.243,2.86),S(-.86,.232,2.90)],.012,ridge,'head')
    loft('Lateral swept cheek crest '+str(side),[S(-1.71,.19,2.46)+(.056,.070),S(-1.44,.225,2.55)+(.058,.053),S(-1.14,.255,2.64)+(.002,.004)],horn,'head',8,1)
    # A fitted graphite cue frame, smaller than the brow/crest; it does not determine head shape.
    stroke('Cue band arm '+str(side),[S(-1.77,.21,2.59),S(-1.72,.285,2.51),S(-1.70,.293,2.39)],.024,horn,'head')
    lobe('Cue side housing '+str(side),S(-1.70,.306,2.40),(.066,.028,.047),horn,'head')
    lobe('Cue signal '+str(side),S(-1.706,.332,2.406),(.028,.008,.012),cyan,'head')
stroke('Fitted cue bridge',[(-1.77,-.21,2.59),(-1.73,0,2.64),(-1.77,.21,2.59)],.023,horn,'head')

# Explicit joint locations retained as the rig contract.
limbs={}
for side in [-1,1]:
    for fore in [True,False]:
        tag=('F' if fore else 'H')+('L' if side<0 else 'R')
        y=side*(.53 if fore else .43)
        if fore:
            hip=Vector((-.76,y,1.98));knee=Vector((-.60,y*1.10,1.16));ankle=Vector((-.94,y*1.10,.30));toe=Vector((-1.11,y*1.1,.16))
        else:
            hip=Vector((.83,y,1.57));knee=Vector((1.13,y*1.18,1.02));ankle=Vector((1.43,y*1.22,.32));toe=Vector((1.22,y*1.24,.15))
        limbs[tag]=[hip,knee,ankle,toe]
        u=tag+'_upper';l=tag+'_lower';f=tag+'_foot'
        if fore:
            # Eight graded contour rings replace the box-like 5-ring v3 column.
            # Root disappears into the shoulder mass; the deltoid fans out
            # then narrows organically into the elbow without a flat cap.
            loft('Integrated forelimb muscle '+tag,[
                (-.79,y*.97,2.025,.12,.15),
                (-.79,y*1.055,1.975,.23,.25),
                (-.75,y*1.12,1.900,.315,.33),
                (-.69,y*1.17,1.790,.36,.34),
                (-.635,y*1.17,1.655,.335,.325),
                (-.59,y*1.14,1.510,.27,.275),
                (-.58,y*1.12,1.355,.21,.215),
                (-.595,y*1.10,1.235,.15,.16),
                (-.60,y*1.10,1.16,.085,.10)
            ],skin,u,16,2)
            # This muscle has a continuous vertex-painted skin, not a separate red panel.
            loft('Tapered forearm '+tag,[tuple(knee)+(.17,.20),(-.64,y*1.1,.99,.17,.22),(-.83,y*1.1,.63,.13,.17),tuple(ankle)+(.105,.14)],slate,l,12,2)
            panel('Forearm dark facing '+tag,[(-.50,y*1.1,.97),(-.64,y*1.1+side*.15,1.11),(-.81,y*1.1+side*.14,.77),(-1.00,y*1.1,.39),(-.80,y*1.1,.56)],(-.73,y*1.1+side*.18,.78),skin,l)
        else:
            loft('Heavy haunch '+tag,[tuple(hip)+(.32,.32),(1.00,y*1.13,1.38,.31,.29),tuple(knee)+(.19,.22)],skin,u)
            panel('Haunch red sweep '+tag,[(.63,y,1.82),(.84,y+side*.25,1.83),(1.20,y+side*.18,1.50),(1.26,y+side*.14,1.18),(.99,y+side*.22,1.05),(.77,y+side*.28,1.39)],(.97,y+side*.34,1.48),reddark,u)
            loft('Rear shin '+tag,[tuple(knee)+(.18,.20),(1.27,y*1.21,.73,.14,.16),tuple(ankle)+(.10,.13)],slate,l,12,2)
        loft('Articulated joint tendon '+tag,[(knee.x-.08,knee.y,knee.z+.13,.14,.13),(knee.x,knee.y,knee.z+.04,.155,.145),(knee.x+.03,knee.y,knee.z-.09,.125,.12)],skin,l,12,1)
        # Broad weight-bearing digitigrade palm and three separated tapered digits.
        loft('Red carpal transition '+tag,[tuple(ankle)+(.12,.13),(toe.x+.08,toe.y,.22,.18,.14),(toe.x,toe.y,.17,.23,.12)],reddark,f,12,2)
        lobe('Broad palm '+tag,(toe.x,toe.y,.13),(.25,.24,.12),skin,f)
        for j in [-1,0,1]:
            xx=toe.x-(.06 if j==0 else 0);yy=toe.y+j*.145
            loft('Red digit '+tag+str(j),[(xx+.05,yy,.17,.082,.105),(xx-.13,yy,.13,.084,.095),(xx-.24,yy,.09,.062,.056)],red,f,10,1)
            loft('Graphite claw '+tag+str(j),[(xx-.18,yy,.105,.061,.065),(xx-.28,yy,.067,.047,.037),(xx-.36,yy,.045,.004,.006)],horn,f,10,1)
        # Tiny posterior carpal red cap, no invented dewclaw/horn.
        lobe('Carpal cap '+tag,(toe.x+.11,toe.y,.28),(.12,.16,.14),red,f)

# Compact segmented tail with the hooked, heavy end visible in canonical P.
tailpath=[(1.13,0,1.63,.18,.18),(1.39,0,1.46,.17,.17),(1.60,0,1.39,.15,.14),(1.80,0,1.47,.12,.12),(2.00,0,1.43,.075,.084),(2.14,0,1.30,.007,.012)]
loft('Heavy short tail',tailpath,skin,'tail',14,2)
loft('Tail oxblood top',[(1.26,0,1.70,.12,.075),(1.47,0,1.54,.15,.075),(1.66,0,1.57,.12,.07),(1.83,0,1.59,.105,.055),(2.02,0,1.47,.055,.043),(2.14,0,1.30,.003,.004)],red,'tail',12,1)
for i in range(3):
    x=1.41+i*.19;z=[1.52,1.46,1.52][i]
    for side in [-1,1]:
        panel('Tail folded surface '+str(i)+str(side),[(x-.08,side*.10,z+.09),(x+.07,side*.15,z+.06),(x+.17,side*.14,z-.07),(x+.05,side*.18,z-.10)],(x+.04,side*.22,z+.005),red if i!=1 else reddark,'tail')

# Vertex-painted colour transitions wrap the continuous anatomy instead of stepping
# at polygon borders. Other components receive neutral white vertex colour on join.
paint=material('P • painted anatomical transitions',(1,1,1),.67)
bs=paint.node_tree.nodes.get('Principled BSDF'); vc=paint.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='P_color'
paint.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color'])
for obj in parts:
    obj.data.update()
    attr=obj.data.color_attributes.new(name='P_color',type='FLOAT_COLOR',domain='CORNER')
    painted=obj.name.startswith(('P continuous thorax','Short thick rising neck','Integrated forelimb muscle','Heavy haunch','Swept crest'))
    if painted:
        obj.data.materials.clear();obj.data.materials.append(paint)
        for p in obj.data.polygons:p.material_index=0
    for loop in obj.data.loops:
        rgb=(1,1,1)
        if painted:
            c=obj.matrix_world @ obj.data.vertices[loop.vertex_index].co
            if obj.name.startswith('P continuous thorax'):
                d=c.z-(1.95-.26*(c.x+.55))
            elif obj.name.startswith('Short thick'):
                d=c.z-2.36
            elif obj.name.startswith('Integrated forelimb'):
                d=min((c.z-1.29)*.78,(abs(c.y)-.49)*2.1)
            elif obj.name.startswith('Heavy'):
                d=min(c.z-1.18,(abs(c.y)-.42)*2)
            else:
                d=min((.24-abs(c.y))*2,c.z-2.59)
            t=max(0,min(1,(d+.055)/.11));t=t*t*(3-2*t)
            rgb=tuple(s*(1-t)+r*t for s,r in zip(skin.diffuse_color[:3],red.diffuse_color[:3]))
        attr.data[loop.index].color=(*rgb,1)
    if obj.name.startswith(('Directional skull','Lower jaw')):
        for p in obj.data.polygons:p.use_smooth=False
# Eliminate the disconnected shoulder ridge: the large scapular contour carries the highlight.
for obj in list(parts):
    if obj.name.startswith('Shoulder ridge highlight'):
        parts.remove(obj);bpy.data.objects.remove(obj,do_unlink=True)
# Chest planes sit on the hull and form the reference's split grey ventral structure.
for obj in parts:
    if obj.name.startswith('Pectoral slate keel'):
        for v in obj.data.vertices:
            v.co.x-=.14
            v.co.y*=1.14
    if obj.name.startswith('Forearm dark facing'):
        for v in obj.data.vertices: v.co.y*=1.08

# V3: correct the too-long v2 silhouette without stretching height.
# Keep world-space vertex and skeleton X coordinates in exact correspondence.
X_COMPACT=0.875
bpy.context.view_layer.update()
for obj in parts:
    obj.data.transform(obj.matrix_world)
    obj.matrix_world=Matrix.Identity(4)
    for vertex in obj.data.vertices: vertex.co.x*=X_COMPACT
    obj.data.update()
for key,positions in limbs.items():
    limbs[key]=[Vector((p.x*X_COMPACT,p.y,p.z)) for p in positions]

# Rig and material-batched body. The rest stance is the review authority.
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0))
arm=bpy.context.object;arm.name='P_Canonical_Rig';arm.data.name='P_Canonical_Skeleton';arm.data.edit_bones.remove(arm.data.edit_bones[0])
def bone(name,head,tail,parent=None):
    if name in ('body','neck','head','tail'):
        head=(head[0]*X_COMPACT,head[1],head[2]);tail=(tail[0]*X_COMPACT,tail[1],tail[2])
    b=arm.data.edit_bones.new(name);b.head=head;b.tail=tail
    if parent:b.parent=arm.data.edit_bones[parent]
    return b
bone('root',(0,0,0),(0,0,.3))
bone('body',(0,0,1.60),(-.65,0,2.00),'root')
bone('neck',(-1.06,0,2.19),(-1.64,0,2.39),'body')
bone('head',(-1.64,0,2.39),(-2.10,0,2.36),'neck')
bone('tail',(1.13,0,1.63),(1.86,0,1.52),'body')
for tag,(a,b,c,d) in limbs.items():
    bone(tag+'_upper',a,b,'body');bone(tag+'_lower',b,c,tag+'_upper');bone(tag+'_foot',c,d,tag+'_lower')
bpy.ops.object.mode_set(mode='OBJECT')
for obj in parts:
    group=obj.vertex_groups.new(name=obj['anatomy']);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    mod=obj.modifiers.new('P canonical articulation','ARMATURE');mod.object=arm
    obj.parent=arm
bpy.ops.object.select_all(action='DESELECT')
for obj in parts:obj.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=bpy.context.object;body.name='P_Canonical_Surface'
# A short, explicitly provisional power run study. It does not change the rest mesh.
# Analytic two-link placement keeps the broad palms level; no motion donor appearance.
scene=bpy.context.scene;scene.render.fps=30;scene.frame_start=1;scene.frame_end=25
for pb in arm.pose.bones:pb.rotation_mode='QUATERNION'
def place_bone(name,a,b):
    pb=arm.pose.bones[name];rest=arm.data.bones[name]
    rest_direction=(rest.tail_local-rest.head_local).normalized()
    rotation=rest_direction.rotation_difference((b-a).normalized()).to_matrix().to_4x4()
    m=rotation @ rest.matrix_local;m.translation=a;pb.matrix=m
    bpy.context.view_layer.update()
contact=[]
for frame in range(1,26):
    phase=(frame-1)/24
    bob=-.09+.024*math.cos(4*math.pi*phase)
    delta=Vector((0,0,bob))
    pb=arm.pose.bones['body'];pb.matrix=Matrix.Translation(delta) @ arm.data.bones['body'].matrix_local
    bpy.context.view_layer.update()
    for tag,(hip,knee,ankle,toe) in limbs.items():
        shift={'HL':0,'HR':.12,'FL':.48,'FR':.60}[tag]
        u=(phase+shift)%1;stance=.62;stride=.53 if tag.startswith('F') else .32
        if u<stance:
            offset=-stride/2+stride*u/stance;lift=0
        else:
            t=(u-stance)/(1-stance)
            offset=stride/2-stride*(t*t*(3-2*t));lift=.22*math.sin(math.pi*t)**1.2
        a=hip+delta;c=ankle+Vector((offset-(.08 if tag.startswith('H') else 0),0,lift))
        L1=(knee-hip).length;L2=(ankle-knee).length
        d=c-a;dist=d.length;v=d.normalized()
        along=(L1*L1-L2*L2+dist*dist)/(2*dist)
        height=math.sqrt(max(0,L1*L1-along*along))
        perpendicular=Vector((-v.z,0,v.x)).normalized()
        # The native leg bend is reconstructed on its original side of the chain.
        restv=(ankle-hip).normalized();restperp=Vector((-restv.z,0,restv.x))
        sign=1 if (knee-hip).dot(restperp)>0 else -1
        b=a+v*along+perpendicular*height*sign
        place_bone(tag+'_upper',a,b);place_bone(tag+'_lower',b,c)
        place_bone(tag+'_foot',c,c+(toe-ankle))
        if u<stance:contact.append({'frame':frame,'limb':tag,'ankleZ':round(c.z,6),'clipped':dist>L1+L2})
    arm.pose.bones['neck'].rotation_quaternion=Vector((0,1,0)).rotation_difference(Vector((.014*math.sin(2*math.pi*phase),1,0)).normalized())
    arm.pose.bones['tail'].rotation_quaternion=Vector((0,1,0)).rotation_difference(Vector((.025*math.sin(2*math.pi*phase+.7),1,0)).normalized())
    for pb in arm.pose.bones:
        pb.keyframe_insert(data_path='location',frame=frame,group=pb.name)
        pb.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=pb.name)
        pb.keyframe_insert(data_path='scale',frame=frame,group=pb.name)
arm.animation_data.action.name='P_Power_Run_Study_0p8s'
# Clear the evaluated pose for canonical rest renders and bind-pose export.
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
(EVIDENCE/'run-authoring-check.json').write_text(json.dumps({'cycleSeconds':.8,'frames':25,'stanceFraction':.62,'strideMetres':{'fore':.60,'hind':.36},'scope':'minimal in-place review; not a production gait or race-contact pass','ikReachClips':sum(x['clipped'] for x in contact),'stanceSamples':contact},indent=2)+'\n')

# Export uncompressed self-contained GLB; optimization is a separate repeatable step.
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);arm.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'p-canonical-v4.glb'),export_format='GLB',use_selection=True,export_animations=True,export_frame_range=True,export_force_sampling=True,export_yup=True)
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
# Non-shipping source includes camera and light setup so review is repeatable.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False
scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.world.color=(.32,.32,.32)
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
floor=material('Review floor',(.17,.195,.215),.9)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.014));bpy.context.object.name='REVIEW_floor';bpy.context.object.data.materials.append(floor)
def area(name,loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.4))-o.location).to_track_quat('-Z','Y').to_euler()
area('REVIEW_key',(-4,-5,7),1000,5);area('REVIEW_fill',(-1,5,4),700,5);area('REVIEW_rim',(4,1,6),1100,4)
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='REVIEW_camera';camera.data.type='ORTHO';camera.data.ortho_scale=5.9;scene.camera=camera
views={'SIDE':(0,-10,2.1),'FRONT':(-10,0,2.0),'FRONT34':(-7,-10,4.6),'REAR34':(7,-10,4.0),'BACK':(10,0,2.0)}
target=Vector((-.02,0,1.48))
for name,loc in views.items():
    if '--no-render' in sys.argv: continue
    if '--quick' in sys.argv and name!='FRONT34': continue
    camera.location=loc;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OFFLINE/(name+'.png'));bpy.ops.render.render(write_still=True)
# Source .blend is reproducible from this script, kept in work to avoid a large duplicate deliverable.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'work/p-canonical-v4/p-canonical-v4.blend'))
info={'authoring':'Blender 4.3.2 / deterministic contour lofts and anatomical surface panels','reference':['public/concept/P.webp','docs/references/evowild-creature-reference-sheet-20260921.jpg'],'coordinates':'GLB: +Y up, -X forward; origin at ground under torso','asset':'public/models/evowild-p/p-canonical-v4.glb','animation':'P_Power_Run_Study_0p8s','bones':len(arm.data.bones),'triangles':sum(len(p.vertices)-2 for p in body.data.polygons),'materials':len(body.data.materials),'status':'v4 forelimb rounded anatomical study; production HOLD','views':list(views),'reference_uncertainty':'Only one small canonical P three-quarter image; exact frontal/rear topology is inferred, not reference-certified.'}
(OUT/'manifest-v4.json').write_text(json.dumps(info,indent=2)+'\n')
print('CANONICAL_P_COMPLETE',json.dumps(info))
