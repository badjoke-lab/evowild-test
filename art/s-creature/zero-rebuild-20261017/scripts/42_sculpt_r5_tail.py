"""Tail-only R5 sculpt, executed in live Blender through MCP.

Edit R4's continuous-tail vertices and remesh its existing 39 tail objects in
place. No whole-body generator, asset import, image synthesis or donor. Every
trial starts from the byte-identical protected R4 working copy.
"""
import bpy, bmesh, hashlib, json, math, os
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
TRIAL = os.environ.get('EVOWILD_R5_TRIAL', 'A')
assert TRIAL in ['A','B','C']
DEST = ROOT / ('verification/S_ZERO_R5_TRIAL_' + TRIAL + '.blend')
REPORT = ROOT / ('evidence/SCULPT_R5_TRIAL_' + TRIAL + '.json')
assert bpy.app.version == (4, 3, 2)
assert not DEST.exists() and not REPORT.exists()
assert Path(bpy.data.filepath).name in ['S_ZERO_R5_WORKING_COPY.blend',
                                      'S_ZERO_R5_TRIAL_A.blend','S_ZERO_R5_TRIAL_B.blend']
assert not bpy.data.is_dirty, 'Save any unrelated live work before trial'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'verification/S_ZERO_R5_WORKING_COPY.blend'), load_ui=False)
before_names = set(bpy.data.objects.keys())
body = bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
old_body = [v.co.copy() for v in body.data.vertices]

def lerp_rows(rows, x):
    if x <= rows[0][0]: return rows[0][1:]
    for a, b in zip(rows, rows[1:]):
        if x <= b[0]:
            t = (x-a[0])/(b[0]-a[0])
            return tuple(u+(v-u)*t for u, v in zip(a[1:], b[1:]))
    return rows[-1][1:]

def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t*t*(3-2*t)

# R4's round axial highlight is lowered and flattened inside the layered tail.
# Only the isolated tail region, above the hind limb, is eligible. The root
# deformation fades to zero before the pelvis. Topology remains unchanged.
spine = [(1.05,1.89),(1.20,1.89),(1.40,1.845),(1.60,1.75),
         (1.80,1.615),(2.0,1.425),(2.15,1.24),(2.28,1.10)]
changed_body = []
for v in body.data.vertices:
    x,y,z = v.co
    if x <= 1.07 or z <= 1.78-.75*(x-1.12): continue
    w = smoothstep((x-1.07)/.21)
    center = lerp_rows(spine,x)[0]
    v.co.y = y*(1+.12*w)
    v.co.z = center + (z-center)*(1-.43*w) - .018*w
    changed_body.append(v.index)
body.data.update()

def write_mesh(ob, verts, faces, smooth=False):
    # Preserve object, mesh datablock, transforms, material slots and parenting.
    me = ob.data
    me.clear_geometry()
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges), ob.name
    assert all(f.calc_area()>1e-12 for f in bm.faces), ob.name
    volume = abs(bm.calc_volume(signed=True))
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = smooth
    if smooth:
        bm=bmesh.new();bm.from_mesh(me)
        for edge in bm.edges:
            edge.smooth = len(edge.link_faces)==2 and edge.calc_face_angle()<math.radians(42)
        bm.to_mesh(me);bm.free()
    return volume

# Individually placed transitions follow the reference's rearward flow. These
# are seven existing layer pairs, not extra fins. Root-to-tip directions and
# widths vary; the original overall tail reach is kept.
specs = [
    # root x,z ; tip x,z ; width, thickness ; terminal lateral offset
    (.96,1.905, 1.49,1.730, .105,.036,.145),
    (1.105,1.912, 1.77,1.605, .119,.038,.175),
    (1.300,1.867, 1.98,1.405, .120,.036,.172),
    (1.495,1.780, 2.17,1.205, .108,.032,.145),
    (1.705,1.647, 2.34,1.015, .092,.028,.112),
    (1.895,1.468, 2.435,.865, .070,.023,.080),
    (2.065,1.285, 2.475,.765, .049,.018,.038),
]
if TRIAL in ['B','C']:
    # Alternate upper streamlining layers with deeper lower exits, as in the
    # canonical SIDE tail. A's common tangent collapsed into one long blade.
    specs = [
        (.96,1.905,1.39,1.710,.075,.032,.125),
        (1.02,1.920,1.80,1.780,.092,.034,.132),
        (1.18,1.885,1.78,1.490,.115,.044,.165),
        (1.31,1.850,2.08,1.470,.102,.037,.170),
        (1.50,1.750,2.12,1.100,.128,.043,.145),
        (1.70,1.590,2.39,1.020,.088,.034,.105),
        (1.93,1.430,2.48,.760,.070,.030,.038),
    ]
    if TRIAL == 'C':
        # B's distal two root pairs sit outside the deformed core. Raise only
        # their embedded origins; retain their lateral reach and terminal tips.
        specs[5]=(1.70,1.650,2.39,1.020,.088,.034,.105)
        specs[6]=(1.93,1.475,2.48,.760,.070,.030,.038)
stations = [0,.12,.28,.46,.65,.82,.94,1]
widths = [(.0,.26),(.12,.75),(.28,1),(.46,.91),(.65,.64),(.82,.32),(.94,.09),(1,.008)]
depths = [(.0,.46),(.12,.85),(.28,1),(.46,.91),(.65,.65),(.82,.34),(.94,.12),(1,.008)]

def shape(i,s,t):
    rx,rz,tx,tz,wide,deep,tipy = specs[i]
    # Center moves out of a buried, medial root and returns to a slender tip.
    y0 = .024 if i<3 else .018
    yy = y0*(1-t)+tipy*t + (.035 if i<4 else .016)*math.sin(math.pi*t)
    p = Vector((rx+(tx-rx)*t, s*yy,
                rz+(tz-rz)*t+.025*math.sin(math.pi*t)))
    tangent = Vector((tx-rx,0,tz-rz+.025*math.pi*math.cos(math.pi*t))).normalized()
    up = tangent.cross(Vector((0,1,0))).normalized()
    across = Vector((0,s*.65,0))-up*.7599342077
    normal = up*.65+Vector((0,s*.7599342077,0))
    return p, across, normal, wide*lerp_rows(widths,t)[0], deep*lerp_rows(depths,t)[0]

def ring(i,s,t):
    p,w,n,wide,deep = shape(i,s,t)
    return [p+w*(wide*math.cos(k*math.pi/4))+n*(deep*math.sin(k*math.pi/4)) for k in range(8)]

def surface(i,s,t,q):
    # Barycentric interpolation on the exact triangles of the main upper face.
    j = next((j for j in range(len(stations)-1) if t<=stations[j+1]),len(stations)-2)
    a,b=stations[j:j+2]; u=(t-a)/(b-a)
    qa=[1,math.sqrt(.5),0,-math.sqrt(.5),-1]
    k=next(k for k in range(4) if q>=qa[k+1])
    v=(qa[k]-q)/(qa[k]-qa[k+1])
    ra,rb=ring(i,s,a),ring(i,s,b)
    if u>=v: p=ra[k]*(1-u)+rb[k]*(u-v)+rb[k+1]*v
    else: p=ra[k]*(1-v)+rb[k+1]*u+ra[k+1]*(v-u)
    return p,shape(i,s,t)[2]

def panel(ob,i,s,start,end,qcenter,width):
    # Thin closed color inlay resting on the dark volume, with no upright cap.
    ts=[start+(end-start)*t for t in [0,.12,.30,.50,.70,.88,1]]
    vf=[]
    for offset in [.0018,-.0015]:
        for j,t in enumerate(ts):
            wid=width*[.025,.70,1,.88,.59,.27,.012][j]
            for q in [qcenter-wid,qcenter,qcenter+wid]:
                p,n=surface(i,s,t,q);vf.append(tuple(p+n*offset))
    count=len(ts)*3; fs=[]
    for j in range(len(ts)-1):
        for k in range(2):
            a=j*3+k;b=a+3
            fs.extend([(a,b,b+1),(a,b+1,a+1),
                       (count+a,count+b+1,count+b),(count+a,count+a+1,count+b+1)])
    boundary=[j*3 for j in range(len(ts))]+[count-2,count-1]+[j*3+2 for j in reversed(range(len(ts)-1))]+[1]
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):fs.append((a,b,b+count,a+count))
    return write_mesh(ob,vf,fs)

def conforming_panel(ob,i,s,start,end,qcenter,width):
    # Clip a convex inlay footprint against every triangle of the actual dark
    # surface in (t,q). Each resulting triangle lies exactly on that face;
    # unlike A, the inlay cannot bridge the dark mesh's faceted ridge.
    footprint=[(start,qcenter),
        (start+(end-start)*.25,qcenter-width),
        (start+(end-start)*.61,qcenter-width*.65),
        (end,qcenter),
        (start+(end-start)*.61,qcenter+width*.65),
        (start+(end-start)*.25,qcenter+width)]
    def cross(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    def clip(poly,a,b):
        result=[]
        for p,q in zip(poly,poly[1:]+poly[:1]):
            dp,dq=cross(a,b,p),cross(a,b,q)
            if dp>=-1e-10:result.append(p)
            if (dp>1e-10 and dq< -1e-10) or (dp< -1e-10 and dq>1e-10):
                u=dp/(dp-dq);result.append((p[0]+u*(q[0]-p[0]),p[1]+u*(q[1]-p[1])))
        return result
    uv=[];index={};faces=[]
    qa=[1,math.sqrt(.5),0,-math.sqrt(.5),-1]
    for j in range(len(stations)-1):
        for k in range(4):
            a=(stations[j],qa[k]);b=(stations[j+1],qa[k]);c=(stations[j+1],qa[k+1]);d=(stations[j],qa[k+1])
            for tri in [[a,b,c],[a,c,d]]:
                poly=tri
                for p,q in zip(footprint,footprint[1:]+footprint[:1]):
                    poly=clip(poly,p,q)
                    if not poly:break
                ids=[]
                for p in poly:
                    key=tuple(round(v,9) for v in p)
                    if key not in index:index[key]=len(uv);uv.append(p)
                    if not ids or index[key]!=ids[-1]:ids.append(index[key])
                if len(ids)>1 and ids[0]==ids[-1]:ids.pop()
                for n in range(1,len(ids)-1):
                    if abs(cross(uv[ids[0]],uv[ids[n]],uv[ids[n+1]]))>1e-10:
                        faces.append((ids[0],ids[n],ids[n+1]))
    used=sorted({k for f in faces for k in f});mapping={old:new for new,old in enumerate(used)}
    uv=[uv[k] for k in used];faces=[tuple(mapping[k] for k in f) for f in faces]
    verts=[]
    for offset in [.002,-.002]:
        for t,q in uv:
            p,n=surface(i,s,t,q);verts.append(tuple(p+n*offset))
    edges={}
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            key=tuple(sorted((a,b)));edges.setdefault(key,[]).append((a,b))
    count=len(uv);fs=list(faces)+[tuple(k+count for k in reversed(f)) for f in faces]
    for pairs in edges.values():
        if len(pairs)==1:
            a,b=pairs[0];fs.append((a,b,b+count,a+count))
    return write_mesh(ob,verts,fs,smooth=True)

records={}
for i in range(7):
    for s in [-1,1]:
        ob=bpy.data.objects[f'TAIL_BLADE_{i}_{s}']
        verts=[tuple(v) for t in stations for v in ring(i,s,t)]
        fs=[]
        for j in range(len(stations)-1):
            for k in range(8):
                a=j*8+k;d=j*8+(k+1)%8;b=(j+1)*8+k;c=(j+1)*8+(k+1)%8
                fs.extend([(a,b,c),(a,c,d)])
        fs += [tuple(reversed(range(8))),tuple(range(len(verts)-8,len(verts)))]
        records[ob.name]={'volume':write_mesh(ob,verts,fs,smooth=TRIAL in ['B','C']),'root':list(shape(i,s,0)[0]),'tip':list(shape(i,s,1)[0])}
        blue=bpy.data.objects[f'TAIL_BLUE_{i}_{s}']
        inlay=conforming_panel if TRIAL in ['B','C'] else panel
        blue_width=.48 if i in [1,3,5] else .20
        records[blue.name]={'volume':inlay(blue,i,s,.19,.94,-.12,blue_width if TRIAL in ['B','C'] else .43)}
        if i<5:
            ivory=bpy.data.objects[f'TAIL_IVORY_{i}_{s}']
            records[ivory.name]={'volume':inlay(ivory,i,s,.10,.60,-.63,.15 if TRIAL in ['B','C'] else .18)}

# Reshape the existing terminal mesh directly: a flattened lens, with retained
# volume through its midsection and a very small terminal section. No needle
# cylinder is added. The original 112 vertices / 120 faces are retained.
ob=bpy.data.objects['TAIL_TIP']
oldtip=[v.co.copy() for v in ob.data.vertices]
for i in range(11):
    indices=list(range(i*10,(i+1)*10))
    center=sum((oldtip[k] for k in indices),Vector())/10
    t=i/10
    for k in indices:
        delta=oldtip[k]-center
        ob.data.vertices[k].co=center+Vector((delta.x*.68,delta.y*1.38,delta.z*.68))+Vector((-.018*(1-t),0,-.012*(1-t)))
for k in [110,111]:
    t=0 if k==110 else 1
    ob.data.vertices[k].co=oldtip[k]+Vector((-.018*(1-t),0,-.012*(1-t)))
ob.data.update()
records[ob.name]={'vertices_retained':len(oldtip),'faces_retained':len(ob.data.polygons)}
assert set(bpy.data.objects.keys()) == before_names
body_change_set=set(changed_body)
for i,v in enumerate(body.data.vertices):
    if i not in body_change_set: assert v.co==old_body[i]
bpy.context.scene['stage']='R5_TRIAL_'+TRIAL
bpy.context.scene['candidate_status']='REVISE: tail study; pending actual four-view comparison'
bpy.context.scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
REPORT.write_text(json.dumps({'trial':TRIAL,'source':'S_ZERO_CANDIDATE_REVISED_R4.blend',
    'destination':str(DEST.relative_to(ROOT)),'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),
    'scope':'Existing tail objects and isolated tail vertices of continuous body only',
    'body_vertex_indices':changed_body,'body_vertices_unchanged':len(old_body)-len(changed_body),
    'body_topology_preserved':True,'objects_added_or_removed':False,'tail_meshes':records,
    'root_connection':'Volumetric embedding; detail layers are not welded to the continuous body.',
    'reference':'art/s-creature/references/00_s_type_modeling_image_v1.png'},indent=2)+'\n')
print('R5_TAIL_SCULPT_SAVED',DEST.name,len(changed_body),'tail core vertices',len(records),'existing tail meshes')
