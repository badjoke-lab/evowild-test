"""Editable anatomical S study. Blender 4.3: blender -b --python scripts/s-form/build.py.

All sections are authored against the SHA-locked drawing, in its side-view
pixel coordinates. X points towards the tail, Y is drawing-down, W is width.
No previous creature mesh or voxel is used as geometry input.
"""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'public/s-form'
ART = ROOT/'art/s-creature/studies/s-form-20261128'
REF = ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
assert hashlib.sha256(REF.read_bytes()).hexdigest() == '93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
OLD = json.loads((ROOT/'public/s-pixel-lab/v3/assets/voxels/index.json').read_text())
PAL = OLD['palette'][1:]
V=[]; F=[]; C=[]; TAG=[]; PARTS=[]

def vertex(p,tag):
    V.append(tuple(p)); TAG.append(tag); return len(V)-1
def face(indices,mat):
    F.append(tuple(indices)); C.append(mat)
def add_rings(name,rings,colors,tag='body',n=12):
    """Cross sections (x, drawing-y, lateral, vertical radius, width radius)."""
    # A midpoint section rounds transitions without changing authored extremes.
    if len(rings)>4:
        source=rings;rings=[]
        for i in range(len(source)-1):
            rings.append(source[i]);p0=source[max(0,i-1)];p1=source[i];p2=source[i+1];p3=source[min(len(source)-1,i+2)]
            rings.append(tuple((-.0625*p0[k]+.5625*p1[k]+.5625*p2[k]-.0625*p3[k]) for k in range(5)))
        rings.append(source[-1])
    start=len(V)
    for k,(x,y,w,ry,rw) in enumerate(rings):
        for j in range(n):
            a=j*math.tau/n
            vertex((x,y-ry*math.cos(a),w+rw*math.sin(a)),tag)
    for k in range(len(rings)-1):
        for j in range(n):
            a=start+k*n+j; b=start+k*n+(j+1)%n; c=b+n; d=a+n
            ink=colors(k,j,n) if callable(colors) else colors
            # Alternating anatomical facets, no noise texture or stochastic color.
            if (k+j)%2: face((a,b,d),ink);face((b,c,d),min(ink+1,9) if 5<=ink<=8 and j%3==1 else ink)
            else: face((a,b,c),ink);face((a,c,d),min(ink+1,9) if 5<=ink<=8 and j%3==1 else ink)
    face(tuple(start+j for j in range(n-1,-1,-1)),colors(0,0,n) if callable(colors) else colors)
    face(tuple(start+(len(rings)-1)*n+j for j in range(n)),colors(len(rings)-2,0,n) if callable(colors) else colors)
    PARTS.append({'name':name,'first':start,'count':len(V)-start,'tag':tag})

def patch(name,outline,center,tag='body',inks=(7,8,9,7,6,7,8,9)):
    """An anatomical surface with a raised ridge and softened, attached rim.
    Vertices follow the visible borders of white/blue planes in the drawing.
    The edge is on the muscle volume. It is not a floating armor polygon.
    """
    start=len(V);n=len(outline)
    for p in outline:vertex(p,tag)
    for i,p in enumerate(outline):
        q=lerp(p,center,.54)
        vertex(q,tag)
    c=vertex(center,tag)
    for i in range(n):
        j=(i+1)%n;ink=inks[i%len(inks)]
        face((start+i,start+j,start+n+j),max(4,ink-1))
        face((start+i,start+n+j,start+n+i),ink)
        face((start+n+i,start+n+j,c),ink)
    # Closed backing stays inside the base anatomy.
    face(tuple(start+i for i in range(n-1,-1,-1)),3)
    PARTS.append({'name':name,'first':start,'count':len(V)-start,'tag':tag})

def lerp(a,b,t):return tuple(a[i]*(1-t)+b[i]*t for i in range(3))

def tube(name,points,radii,inks,tag,n=10):
    start=len(V)
    for i,p in enumerate(points):
        prev=Vector(points[max(0,i-1)]); nex=Vector(points[min(len(points)-1,i+1)])
        tangent=(nex-prev).normalized(); across=Vector((0,0,1))
        up=tangent.cross(across).normalized()
        for j in range(n):
            a=j*math.tau/n
            q=Vector(p)+up*(radii[i][0]*math.cos(a))+across*(radii[i][1]*math.sin(a))
            vertex(q,tag)
    for i in range(len(points)-1):
        for j in range(n):
            a=start+i*n+j;b=start+i*n+(j+1)%n;c=b+n;d=a+n
            ink=inks(i,j,n) if callable(inks) else inks
            face((a,b,c),ink);face((a,c,d),ink)
    face(tuple(start+j for j in range(n-1,-1,-1)),2)
    face(tuple(start+(len(points)-1)*n+j for j in range(n)),2)
    PARTS.append({'name':name,'first':start,'count':len(V)-start,'tag':tag})

def blade(name,points,widths,thickness,tag,blue=False,bank=0):
    # Closed diamond cross-sections; each blade has a true ridge and a thin edge.
    start=len(V)
    for i,p in enumerate(points):
        d=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        normal=Vector((-d.y,d.x,0)).normalized()
        across=Vector((0,0,1))
        q=(normal*math.cos(bank)+across*math.sin(bank))*widths[i]
        ridge=(-normal*math.sin(bank)+across*math.cos(bank))*thickness[i]
        pp=Vector(p)
        for v in (pp+q,pp+ridge,pp-q,pp-ridge):vertex(v,tag)
    for i in range(len(points)-1):
        for j in range(4):
            ink=([2,3,1,4] if not blue else [11,12,2,13])[j]
            face((start+i*4+j,start+i*4+(j+1)%4,start+(i+1)*4+(j+1)%4),ink)
            face((start+i*4+j,start+(i+1)*4+(j+1)%4,start+(i+1)*4+j),ink)
    face(tuple(start+j for j in (3,2,1,0)),2)
    face(tuple(start+(len(points)-1)*4+j for j in range(4)),2)
    PARTS.append({'name':name,'first':start,'count':len(V)-start,'tag':tag})

# Thorax -> rib cage -> contracted waist -> sacrum. Measured against the side
# drawing, with actual chest/hip width derived from front/back, not extrusion.
add_rings('Thorax_Ribcage_Waist_Sacrum',[
 (256,280,0,29,21),(278,275,0,46,35),(303,274,0,48,39),
 (335,271,0,43,35),(366,267,0,36,30),(400,260,0,28,24),
 (431,252,0,24,20),(461,250,0,29,24),(491,258,0,37,32),
 (519,253,0,32,31),(541,242,0,19,21),(549,235,0,11,9)],
 lambda k,j,n: (7 if math.cos(j*math.tau/n)>.82 else 2 if math.cos(j*math.tau/n)<-.1 else 3),n=16)
for side in (-1,1):
    patch('Ribcage_WhitePlane_'+str(side),[(325,241,side*26),(351,229,side*23),(383,234,side*25),
      (412,243,side*26),(434,256,side*23),(413,278,side*25),(382,294,side*29),
      (354,307,side*30),(332,292,side*33),(322,268,side*36)],(365,261,side*39))
    patch('Lumbar_WhitePlane_'+str(side),[(395,235,side*15),(433,230,side*13),(468,222,side*18),
      (483,234,side*27),(461,252,side*27),(436,270,side*20),(414,277,side*24),
      (428,252,side*24)],(449,239,side*28),inks=(8,9,8,7,6,7,8,8))

# Neck has a narrow throat and a wider insertion into the thorax.
tube('Cervical_Throat',[(142,213,0),(168,228,0),(194,249,0),(225,273,0),(262,293,0),(281,292,0)],
 [(12,13),(17,17),(20,20),(23,24),(24,27),(10,17)],
 lambda i,j,n: 3 if j in (0,1,9) else (1 if j in (4,5,6) else 2),'head',12)
# White dorsal cervical tendon follows the upper surface, not a detached plate.
blade('Cervical_Dorsal_Plane',[(156,208,0),(202,227,0),(243,238,0),(280,239,0)],
 [2,4,6,2],[7,9,12,6],'head')
for i in range(len(C)-24,len(C)): C[i]=7 if i%3 else 5

add_rings('Skull_Muzzle_Jaw',[(71,237,0,4,5),(86,226,0,9,9),(105,214,0,12,14),
 (123,207,0,15,19),(141,206,0,15,20),(155,211,0,9,13)],
 lambda k,j,n: 7 if j in (0,1,11) else (5 if j in (2,10) else 2 if j in (5,6,7) else 4),'head')
for side in (-1,1):
    w=side*16
    blade('Crest_'+str(side),[(126,197,w),(152,170,side*20),(201,141,side*24),(267,111,side*23),(386,74,side*18)],
          [3,7,8,5,0.15],[3,4,3,2,.15],'head')
    blade('Crest_Blue_Inner_'+str(side),[(143,192,w),(179,174,side*21),(233,147,side*24),(303,116,side*23)],
          [2,5,4,0.1],[1.5,2,1.5,.1],'head',True)
    blade('Ear_'+str(side),[(144,199,side*21),(164,190,side*27),(189,183,side*29)],
          [4,7,.2],[3,4,.2],'head')
    # Compact elongated Cue Band, nested in the head contour.
    add_rings('CueHousing_'+str(side),[(111,199,side*21,5,2),(124,197,side*23,8,3),(141,196,side*22,6,2),(148,198,side*20,2,1)],2,'head',10)
    add_rings('CueGold_'+str(side),[(119,197,side*26,4,1),(123,197,side*27,5,1),(128,197,side*26,4,1)],15,'head',10)
    add_rings('CueSignal_'+str(side),[(130,196,side*25,2,1),(137,195,side*26,3,1),(143,196,side*25,2,1)],14,'head',8)
    add_rings('EyeSocket_'+str(side),[(99,214,side*12,2,1),(105,212,side*15,3.5,1.5),(112,211,side*16,1.8,1)],0,'head',8)
    add_rings('Eye_'+str(side),[(103,212,side*16,1.2,.5),(107,211,side*17,1.6,.5),(109,211,side*16,1,.3)],13,'head',8)

# Only the three swept dorsal forms explicitly present in the concept sheet.
for i,outline in enumerate([
 [(217,234,0),(243,227,0),(262,213,0),(254,229,0),(239,241,0)],
 [(256,239,0),(282,215,0),(311,198,0),(297,216,0),(284,240,0)],
 [(299,241,0),(321,213,0),(350,187,0),(402,183,0),(365,195,0),(345,219,0),(331,239,0)]]):
    c=(sum(p[0] for p in outline)/len(outline),sum(p[1] for p in outline)/len(outline),5)
    patch('Dorsal_Ridge_'+str(i),outline,c,inks=(3,4,5,3,2,3,4))

REST={
 'nearF':[(286,277,34),(326,329,38),(367,450,28),(353,502,28)],
 'farF':[(278,277,-34),(279,337,-38),(242,453,-28),(221,502,-28)],
 'nearH':[(510,255,31),(551,335,37),(632,379,43),(673,454,45),(655,502,45)],
 'farH':[(499,256,-31),(488,337,-37),(548,382,-43),(514,459,-45),(481,502,-45)]}

def lerp(a,b,t):return tuple(a[i]*(1-t)+b[i]*t for i in range(3))
for leg,joints in REST.items():
    front=leg.endswith('F');side=1 if leg.startswith('near') else -1
    x,y,w=joints[0]
    # Scapula / hip volumes cover the anatomical root, taper into upper limb.
    if front:
        tube(leg+'_ScapularMass',[(x+14,y-45,side*25),(x+3,y-26,side*37),(x-3,y-3,side*43),(x+13,y+23,side*38)],
             [(9,9),(22,16),(26,17),(10,8)],lambda i,j,n: 7+(i%2) if j not in (4,5,6) else 5,leg+'_scapula',12)
        patch(leg+'_ScapularWhite',[(x-4,y-45,side*31),(x+24,y-49,side*29),
          (x+37,y-30,side*38),(x+31,y-7,side*45),(x+17,y+20,side*46),
          (x-6,y+14,side*47),(x-21,y-3,side*40),(x-19,y-22,side*36)],
          (x+4,y-17,side*63),leg+'_scapula',inks=(8,9,8,7,6,7,8,9))
    else:
        tube(leg+'_GlutealMass',[(x-10,y-29,side*22),(x+2,y-8,side*35),(x+15,y+22,side*42),(x+26,y+55,side*39)],
             [(10,10),(28,18),(27,17),(9,8)],lambda i,j,n: 7+(i%2) if j not in (4,5,6) else 4,leg+'_scapula',12)
        patch(leg+'_GlutealWhite',[(x-30,y-29,side*24),(x-13,y-38,side*25),(x+10,y-22,side*39),
          (x+29,y+2,side*47),(x+37,y+29,side*46),(x+42,y+66,side*38),
          (x+17,y+48,side*46),(x-1,y+24,side*51),(x-17,y-2,side*43)],
          (x+9,y+5,side*63),leg+'_scapula',inks=(9,9,8,7,6,7,8,8,9))
    for j in range(len(joints)-2):
        a,b=joints[j:j+2]
        radii=([14,17,13,8] if front and j==0 else [19,23,16,10] if not front and j==0 else [7,8,5,4])
        pts=[a,lerp(a,b,.28),lerp(a,b,.68),b]
        tube(leg+'_Segment'+str(j),pts,[(r,r*.67) for r in radii],
             (lambda i,k,n: 7 if k in (0,1,n-1) else 5 if k in (2,n-2) else 2) if j==0 else
             (lambda i,k,n: 3 if k in (0,1,n-1) else 2 if k in (2,3,n-2) else 1),leg+str(j),10)
    # Short fetlock and two split toes, visibly separate in front and rear.
    for joint in range(1,len(joints)-1):
        jx,jy,jw=joints[joint];radius=7 if joint==1 else 5
        add_rings(leg+'_Joint'+str(joint),[(jx-radius,jy,jw,2,2),(jx-radius*.4,jy,jw,radius,radius*.7),
          (jx+radius*.4,jy,jw,radius,radius*.7),(jx+radius,jy,jw,2,2)],
          lambda i,k,n: 5 if k in (0,1,n-1) else 2,
          leg+str(joint) if joint<len(joints)-2 else leg+'_foot',10)
    a,b=joints[-2:];tag=leg+'_foot'
    tube(leg+'_Pastern',[a,lerp(a,b,.55),lerp(a,b,.9)],[(6,5),(7,6),(10,9)],2,tag,10)
    for toe in (-1,1):
        tx,ty,tw=b
        add_rings(leg+'_Toe'+str(toe),[(tx-12,ty-1,tw+toe*5,1,2),(tx-5,ty-8,tw+toe*5,8,4),
          (tx+5,ty-13,tw+toe*5,12,4),(tx+10,ty-8,tw+toe*5,7,3)],
          lambda i,k,n: 7 if k in (0,1,n-1) else 2,tag,8)
        blade(leg+'_ToeBlue'+str(toe),[(tx-10,ty-2,tw+toe*7),(tx+1,ty-18,tw+toe*7),(tx+4,ty-23,tw+toe*6)],
              [1.5,2,.1],[.5,.7,.1],tag,True)

# Caudal axis and paired swept pennons. Branches attach to this axis, not pelvis.
tail=[(532,224,0),(568,226,0),(606,240,0),(645,263,0),(679,292,0),(710,329,0),(741,393,0)]
tube('Caudal_Stem',tail,[(10,9),(9,8),(7,6),(5,4),(4,3),(2,2),(.2,.2)],3,'tail',10)
for i in range(6):
    root=tail[i];end=tail[min(i+2,6)]
    for side in (-1,1):
        p0=(root[0]+5,root[1]+2,side*4)
        p1=(root[0]+27,root[1]+4,side*(18-i))
        p2=(end[0]+8,min(393,end[1]+(i-1)*6),side*(29-i*3))
        mid=lerp(p1,p2,.5)
        blade('Caudal_Pennon_'+str(i)+'_'+str(side),[p0,p1,mid,p2],[3,11-i*.8,6,.1],[2,3,2,.1],'tail',i%2==0,side*math.pi/3)

def rot(p,angle,origin,target):
    x,y,w=p;c=math.cos(angle);s=math.sin(angle)
    x-=origin[0];y-=origin[1]
    return (target[0]+c*x-s*y,target[1]+s*x+c*y,w)
def length(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def solve(a,b,l1,l2,sign):
    dx,dy=b[0]-a[0],b[1]-a[1];d=math.hypot(dx,dy)
    along=(d*d+l1*l1-l2*l2)/(2*d)
    h=math.sqrt(max(0,l1*l1-along*along))
    return (a[0]+dx/d*along-dy/d*h*sign,a[1]+dy/d*along+dx/d*h*sign,a[2])
def transform_between(p,a,b,c,d):
    angle=math.atan2(d[1]-c[1],d[0]-c[0])-math.atan2(b[1]-a[1],b[0]-a[0])
    return rot(p,angle,a,c)

def pose(frame):
    if frame<0:return V[:],{}
    t=frame/24;theta=t*math.tau
    origin=(409,253);target=(409+2*math.sin(theta),248+6*math.cos(2*theta-.6))
    angle=.035*math.sin(theta+.1)
    def body(p):return rot(p,angle,origin,target)
    moved={};feet={}
    for leg,joints in REST.items():
        foot=OLD['poses'][frame+1]['feet'][leg]
        tx,ty=foot['toe'];w=joints[-1][2]
        # Retain contact phase and support velocity, with a shorter stride for
        # the rebuilt limb lengths. The old raster rig stretched its segments.
        center=277 if leg.endswith('F') else 550
        tx=center+(tx-center)*.75
        toe=(tx,ty,w)
        ankle=(tx+(joints[-2][0]-joints[-1][0]),ty+joints[-2][1]-joints[-1][1],w)
        root=body(joints[0]);phase=(t-{'nearF':.46,'farF':.32,'nearH':.06,'farH':.92}[leg])%1
        if leg.endswith('F'):
            l1=length(joints[0],joints[1]);l2=length(joints[1],joints[2])
            reach=length(root,ankle)
            if reach>l1+l2-1:
                d=(reach-(l1+l2-1))/reach
                root=(root[0]+(ankle[0]-root[0])*d,root[1]+(ankle[1]-root[1])*d,root[2])
            elbow=solve(root,ankle,l1,l2,-1)
            posed=[root,elbow,ankle,toe]
        else:
            # Femur rotates forward in recovery. Tibia/hock solve two remaining
            # links, retaining their lengths instead of inheriting voxel bends.
            a=math.radians(90+31*math.sin(math.tau*(phase-.18)))
            femur=length(joints[0],joints[1])
            l1=length(joints[1],joints[2]);l2=length(joints[2],joints[3])
            reach=length(root,ankle)
            if reach>femur+l1+l2-3:
                d=(reach-(femur+l1+l2-3))/reach
                root=(root[0]+(ankle[0]-root[0])*d,root[1]+(ankle[1]-root[1])*d,root[2])
            alternatives=[]
            for step in range(-100,101):
                candidate=a+step*math.pi/180
                k=(root[0]+femur*math.cos(candidate),root[1]+femur*math.sin(candidate),joints[1][2])
                d=length(k,ankle)
                if abs(l1-l2)+1<d<l1+l2-1:alternatives.append((abs(step),k))
            assert alternatives,('unreachable hind limb',leg,frame)
            knee=min(alternatives,key=lambda p:p[0])[1]
            hock=solve(knee,ankle,length(joints[1],joints[2]),length(joints[2],joints[3]),-1)
            posed=[root,knee,hock,ankle,toe]
        moved[leg]=posed;feet[leg]={'toe':toe,'contact':foot['contact'],'joints':posed}
    result=[]
    for p,tag in zip(V,TAG):
        if tag=='body':q=body(p)
        elif tag=='head':q=rot(p,angle-.022*math.sin(theta-.3),(256,250),body((256,250,0)))
        elif tag=='tail':
            # Continuous curved bending of the stem and its attached pennons.
            q=list(body(p));u=max(0,(p[0]-532)/210)
            q[1]+=u*u*8*math.sin(theta-.9);q[2]+=u*u*9*math.sin(theta-.6)
        else:
            leg=next(k for k in REST if tag.startswith(k));j=REST[leg];d=moved[leg]
            if tag.endswith('_scapula'):
                turn=math.atan2(d[1][1]-d[0][1],d[1][0]-d[0][0])-math.atan2(j[1][1]-j[0][1],j[1][0]-j[0][0])
                q=rot(p,angle+.35*turn,j[0],d[0])
            elif tag.endswith('_foot'):q=(p[0]+d[-1][0]-j[-1][0],p[1]+d[-1][1]-j[-1][1],p[2])
            else:
                k=int(tag[-1]);q=transform_between(p,j[k],j[k+1],d[k],d[k+1])
        result.append(q)
    return result,feet

# Flatten the support surface in the editable rest mesh. In particular, the
# oblique rear pastern's circular section must not extend through its sole.
# The same corrected vertices are used by all 24 deformed shapes.
V=[(p[0],min(502,p[1]),p[2]) if tag.endswith('_foot') else p for p,tag in zip(V,TAG)]
def world(p):return ((p[0]-385)/200,-p[2]/200,(502-p[1])/200)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mats=[]
for i,h in enumerate(PAL):
    def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    m=bpy.data.materials.new('S_%02d_%s'%(i,h[1:]));m.diffuse_color=tuple(linear(int(h[k:k+2],16)/255) for k in (1,3,5))+(1,)
    m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Roughness'].default_value=.78
    mats.append(m)
mesh=bpy.data.meshes.new('S_AnatomicalSections');mesh.from_pydata([world(p) for p in V],[],F);mesh.update()
obj=bpy.data.objects.new('S_Form_20261128',mesh);bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
for m in mats:mesh.materials.append(m)
soft=set()
for part in PARTS:
    if any(k in part['name'] for k in ['Thorax_','Cervical_Throat','Skull_','Mass','Segment','Pastern','Joint']):
        soft.update(range(part['first'],part['first']+part['count']))
for poly,ink in zip(mesh.polygons,C):
    poly.material_index=ink;poly.use_smooth=all(v in soft for v in poly.vertices)
# Consistent outward orientation on the authored closed sections.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
for part in PARTS:
    vg=obj.vertex_groups.new(name=part['name']);vg.add(list(range(part['first'],part['first']+part['count'])),1,'REPLACE')
obj.shape_key_add(name='Basis')
poses=[]
for frame in range(24):
    vertices,feet=pose(frame);key=obj.shape_key_add(name='Gallop_%02d'%frame)
    for point,p in zip(key.data,vertices):point.co=world(p)
    poses.append({'frame':frame,'feet':feet})
obj['source_reference']=str(REF.relative_to(ROOT));obj['source_sha256']=OLD['referenceSHA256']
obj['authoring_units']='200 drawing pixels per metre; ground y=502; pivot x=385'
obj['motion_source']='24 phase/contact records only; joint solution is new'
obj['study_verdict']='REVISE pending direct visual review; not a performance acceptance'
scene=bpy.context.scene;scene.render.fps=100;scene.frame_end=72
for frame in range(25):
    for i,key in enumerate(obj.data.shape_keys.key_blocks[1:]):
        key.value=1 if i==frame%24 else 0;key.keyframe_insert('value',frame=frame*3)
if obj.data.shape_keys.animation_data:
    for curve in obj.data.shape_keys.animation_data.action.fcurves:
        for p in curve.keyframe_points:p.interpolation='LINEAR'
scene.frame_set(0)
# Save the editable rest shape with animation and anatomical vertex groups.
for key in obj.data.shape_keys.key_blocks:key.value=0
ART.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'s-form.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'s-form.glb'),export_format='GLB',use_selection=True,
  export_animations=False,export_morph=True,export_morph_normal=True,export_morph_tangent=False,
  export_yup=True,export_materials='EXPORT',export_extras=True)
summary={'reference_sha256':OLD['referenceSHA256'],'source':'hand-authored anatomical cross sections',
 'vertices':len(V),'faces':len(F),'parts':PARTS,'palette':PAL,'period':OLD['period'],'stride':OLD['stride']*.75/200,
 'poses':poses,'rest_joints':REST,'base_head':'a93fa4b65ea398d4e8ec0560c600f0d50abe1e72'}
(OUT/'anatomy.json').write_text(json.dumps(summary,indent=2)+'\n')
print('S_FORM',len(V),len(F),len(PARTS))
