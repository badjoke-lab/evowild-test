"""Reference-anchored polygon retopology in the existing editable v6 workspace.

Blender 4.3.2: blender -b -t 4 --python scripts/modeling/sculpt-canonical-p-v7.py
This is a STATIC anatomical candidate. No inherited rig or run is exported.
The half-body cage has apertures whose boundary vertices are shared by the
pectoral/scapular surface and the extruded limbs. No muscle shells, spheres,
radius lofts, voxel seed, Gaussian displacement, or v4 construction are used.
"""
import bpy, bmesh, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'art/p-creature/workspaces/P-v7-reference-retopology.blend'
GLB=ROOT/'public/models/evowild-p/p-canonical-v7.glb'
E=ROOT/'docs/evidence/p-canonical-3d-v7-20261012'
E.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'art/p-creature/workspaces/P-v6-canonical-sculpt-review.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
ref=bpy.data.objects['CANONICAL_P_IMAGE__DO_NOT_MODIFY']
canonical=hashlib.sha256((ROOT/'public/concept/P.webp').read_bytes()).hexdigest()
assert hashlib.sha256(bytes(ref.data.packed_file.data)).hexdigest()==canonical

# Retain and directly edit only the existing head/Cue Band/digits. Delete the
# v6 continuous anatomy and its separate spherical carpal caps in this NEW file.
old=bpy.data.objects['P_Canonical_Surface']
old.modifiers.clear();old.parent=None;old.animation_data_clear()
keep=set()
for v in old.data.vertices:
    names=[old.vertex_groups[g.group].name for g in v.groups if g.weight>.99]
    if 'head' in names or any(n.endswith('_foot') for n in names):keep.add(v.index)
bm=bmesh.new();bm.from_mesh(old.data);bm.verts.ensure_lookup_table()
remove=[v for v in bm.verts if v.index not in keep]
bmesh.ops.delete(bm,geom=remove,context='VERTS')
bm.to_mesh(old.data);bm.free()
old.name='P_v7_edited_v6_head_cue_digits'
for v in old.data.vertices:
    names=[old.vertex_groups[g.group].name for g in v.groups if g.weight>.99]
    if 'head' in names:
        # Lift the cranial base relative to the withers; shorten the wedge and
        # compress its depth. The crest is edited with the skull, not replaced.
        v.co.x=-1.42+(v.co.x+1.42)*.94
        v.co.y*=.91
        v.co.z=2.78+(v.co.z-2.40)*.86
    else:
        fore=any(n.startswith('F') for n in names)
        v.co.x+=.12 if fore else -.08
        v.co.y+=(-1 if v.co.y<0 else 1)*(.18 if fore else .04)
        # Flatten the spherical wrist cap into a sloping carpal attachment.
        if v.co.z>.18:v.co.z=.18+(v.co.z-.18)*.52
old.vertex_groups.clear()
for o in list(bpy.data.objects):
    if o.type=='ARMATURE' or (o.type=='MESH' and o!=old):bpy.data.objects.remove(o,do_unlink=True)

def material(name,c):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.72
    return m
mats=[material('v7 oxblood muscle planes',(.24,.040,.035)),
      material('v7 shaded red muscle planes',(.145,.026,.025)),
      material('v7 slate pectoral and tendon planes',(.085,.111,.145)),
      material('v7 charcoal intermuscular folds',(.025,.035,.049)),
      material('v7 red ridge plane',(.29,.058,.046))]
verts=[];faces=[];materials=[];labels=[]
def vert(p):verts.append(tuple(p));return len(verts)-1
def face(ids,mat=0,label=''):
    ids=list(dict.fromkeys(ids))
    if len(ids)>=3:faces.append(tuple(ids));materials.append(mat);labels.append(label)

# The points are anatomical cage landmarks, not centres/radii of primitives.
# Columns: cranial neck / clavicular breast / scapula / caudal shoulder /
# lifted flank / pelvis / tail root. Rows: dorsal seam to ventral seam.
# The image itself is the sole authority; unseen cross-sectional depth is inferred.
patch=[
 [(-1.46,0,2.85),(-1.44,-.18,2.78),(-1.49,-.25,2.61),(-1.36,-.18,2.48),(-1.28,0,2.43)],
 [(-1.03,0,2.79),(-1.00,-.38,2.66),(-1.24,-.60,2.24),(-1.08,-.53,1.73),(-.91,0,1.56)],
 [(-.52,0,2.87),(-.55,-.48,2.76),(-.48,-.66,2.35),(-.46,-.48,1.57),(-.44,0,1.50)],
 [(-.08,0,2.67),(-.09,-.39,2.52),(.02,-.44,2.13),(.03,-.28,1.78),(.00,0,1.73)],
 [(.33,0,2.34),(.36,-.31,2.19),(.33,-.35,1.90),(.39,-.23,1.60),(.34,0,1.58)],
 [(.76,0,2.05),(.77,-.34,1.96),(.85,-.39,1.70),(.85,-.27,1.46),(.80,0,1.45)],
 [(1.04,0,1.84),(1.06,-.20,1.80),(1.11,-.24,1.63),(1.09,-.15,1.47),(1.02,0,1.48)]
]
grid=[[vert(p) for p in col] for col in patch]
for c in range(6):
    for r in range(4):
        if (c in (1,2,4,5)) and r in (1,2):continue
        mat=0 if r==0 else (2 if r>=2 else 1)
        face((grid[c][r],grid[c+1][r],grid[c+1][r+1],grid[c][r+1]),mat,'thoracic plane')
# Close front and rear on the symmetry plane. The mirror weld is the sternum.
for c in (0,6):
    mids=[vert((patch[c][r][0],0,patch[c][r][2])) for r in (1,2,3)]
    centre=[grid[c][0],*mids,grid[c][4]]
    for r in range(4):face((grid[c][r],centre[r],centre[r+1],grid[c][r+1]),2 if c==0 else 1,'neck/root closure')

def aperture(c):
    return [grid[c][1],grid[c+1][1],grid[c+2][1],grid[c+2][2],grid[c+2][3],grid[c+1][3],grid[c][3],grid[c][2]]
def extend(boundary,points,mats8,label):
    new=[vert(p) for p in points]
    for i in range(8):face((boundary[i],boundary[(i+1)%8],new[(i+1)%8],new[i]),mats8[i],label)
    return new

# Shoulder socket is a hole in the chest surface, not an intersecting object.
# Its eight edges flow through deltoid, oblique triceps, elbow and carpal tendon.
b=aperture(1)
b=extend(b,[(-.96,-.75,2.46),(-.64,-1.00,2.62),(-.23,-.94,2.40),(-.03,-.85,2.04),(-.23,-.56,1.68),(-.62,-.43,1.60),(-.97,-.49,1.81),(-1.11,-.72,2.14)],[0,4,0,1,2,2,2,1],'pectoral into deltoid')
b=extend(b,[(-.65,-.87,1.87),(-.39,-1.00,1.94),(-.12,-.93,1.84),(-.07,-.74,1.62),(-.18,-.51,1.55),(-.42,-.44,1.51),(-.65,-.48,1.54),(-.78,-.67,1.70)],[0,0,1,1,3,2,2,2],'oblique upper arm')
b=extend(b,[(-.49,-.83,1.27),(-.33,-.88,1.32),(-.16,-.83,1.26),(-.12,-.71,1.21),(-.19,-.59,1.19),(-.34,-.56,1.17),(-.50,-.60,1.20),(-.55,-.72,1.23)],[1,1,3,3,2,2,2,3],'elbow fold')
b=extend(b,[(-.62,-.87,1.02),(-.44,-.91,1.07),(-.27,-.86,1.04),(-.22,-.74,.95),(-.30,-.61,.91),(-.47,-.59,.89),(-.64,-.65,.92),(-.69,-.76,.96)],[2,2,2,3,3,3,2,2],'forearm planes')
b=extend(b,[(-.80,-.86,.41),(-.70,-.90,.44),(-.59,-.85,.42),(-.57,-.75,.39),(-.62,-.66,.37),(-.72,-.65,.36),(-.82,-.69,.37),(-.85,-.77,.39)],[2,2,3,3,3,2,2,2],'wrist tendon')
b=extend(b,[(-.91,-.89,.19),(-.77,-.94,.21),(-.66,-.89,.21),(-.64,-.75,.20),(-.69,-.62,.19),(-.84,-.61,.17),(-.98,-.67,.17),(-1.02,-.77,.18)],[0,0,1,1,3,0,0,1],'integrated carpus')
face(b,3,'palm closure')

# Rear limb branches from the pelvic patch of the same surface.
b=aperture(4)
b=extend(b,[(.63,-.49,1.62),(.79,-.65,1.72),(1.00,-.65,1.60),(1.13,-.56,1.39),(1.07,-.36,1.28),(.86,-.28,1.25),(.63,-.31,1.28),(.49,-.42,1.42)],[0,0,1,1,3,2,2,1],'pelvic to thigh')
b=extend(b,[(.88,-.59,1.02),(.99,-.66,1.05),(1.13,-.60,1.03),(1.19,-.48,1.00),(1.13,-.37,.98),(1.00,-.32,.97),(.88,-.37,.97),(.82,-.49,1.00)],[1,1,3,3,2,2,2,2],'rear knee')
b=extend(b,[(1.03,-.61,.58),(1.15,-.64,.62),(1.27,-.59,.61),(1.30,-.49,.57),(1.24,-.38,.55),(1.14,-.35,.53),(1.02,-.40,.53),(.99,-.50,.56)],[2,2,3,3,3,2,2,2],'angled rear shin')
b=extend(b,[(.98,-.63,.21),(1.12,-.68,.24),(1.23,-.61,.24),(1.26,-.50,.21),(1.21,-.38,.20),(1.07,-.35,.19),(.94,-.39,.18),(.91,-.52,.20)],[0,0,1,1,3,0,0,1],'rear carpus')
face(b,3,'rear palm closure')

# Refine the chest/arm junction as shared quad patches. New plane-control
# points give the pectoral its forward keel and the deltoid/triceps their
# opposing diagonal faces; edge midpoints remain common to adjacent regions.
oldfaces,oldmaterials,oldlabels=faces,materials,labels
faces=[];materials=[];labels=[];midpoints={}
for ids,mat,label in zip(oldfaces,oldmaterials,oldlabels):
    centre=sum((Vector(verts[i]) for i in ids),Vector())/len(ids)
    if label=='pectoral into deltoid':
        if centre.x<-.72 and centre.z<2.35:
            centre.x-=.20;centre.y-=.07;centre.z-=.04
        elif centre.z>2.4:
            centre.y-=.09;centre.z+=.025
    if label=='oblique upper arm' and centre.y<-.74:
        centre.y-=.105
    if label=='thoracic plane' and centre.x<-.6 and centre.z<1.9:
        centre.x-=.14;centre.z-=.03
    ci=vert(centre);mids=[]
    for a,b in zip(ids,ids[1:]+ids[:1]):
        key=tuple(sorted((a,b)))
        if key not in midpoints:midpoints[key]=vert((Vector(verts[a])+Vector(verts[b]))*.5)
        mids.append(midpoints[key])
    for i,a in enumerate(ids):face((a,mids[i],ci,mids[i-1]),mat,label)
mesh=bpy.data.meshes.new('P v7 shared anatomical patch topology');mesh.from_pydata(verts,[],faces);mesh.update()
body=bpy.data.objects.new('P_v7_CONTINUOUS_CHEST_SHOULDER_ARMS_CAGE',mesh);scene.collection.objects.link(body)
for m in mats:mesh.materials.append(m)
for p,mi in zip(mesh.polygons,materials):p.material_index=mi;p.use_smooth=True
bpy.context.view_layer.objects.active=body
# Remove the unused centre points of the branching apertures and degenerate caps.
bm=bmesh.new();bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
mirror=body.modifiers.new('Shared sternum bilateral topology','MIRROR');mirror.use_axis[0]=False;mirror.use_axis[1]=True;mirror.use_clip=True
bpy.ops.object.modifier_apply(modifier=mirror.name)
# All anatomical surfaces are a single closed mesh, including both forearms.
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
topology={'cageVertices':len(bm.verts),'cageFaces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'method':'explicit shared polygon patches, branching limb apertures, mirrored sternum, Catmull-Clark surface','independentMuscleShells':0}
assert topology['nonManifoldEdges']==0,topology
bm.to_mesh(mesh);bm.free()
# Deliberately modest crease weights preserve sloping planes after subdivision.
crease=mesh.attributes.new('crease_edge','FLOAT','EDGE')
edge_faces={}
for p in mesh.polygons:
    for k in p.edge_keys:edge_faces.setdefault(k,[]).append(p.material_index)
for e in mesh.edges:
    mm=edge_faces.get(tuple(sorted(e.vertices)),[])
    if len(set(mm))>1:crease.data[e.index].value=.18
sub=body.modifiers.new('Editable anatomical surface subdivision','SUBSURF');sub.levels=2;sub.render_levels=2
body['method']='Reference anchored continuous polygon retopology; edit cage in Blender'
body['approval']='STATIC_REVIEW_ONLY; no gait approval'

# Keep the coarse shared-edge cage in the source. Sculpt a duplicate surface with
# reference-drawn stroke paths snapped to the mesh, not detached muscle volumes.
cage=body.copy();cage.data=body.data.copy();scene.collection.objects.link(cage)
cage.name='AUTHORING_hidden_shared_edge_cage';cage.hide_render=True;cage.hide_set(True)
body.modifiers[0].levels=2;body.modifiers[0].render_levels=2
bpy.context.view_layer.objects.active=body
bpy.ops.object.modifier_apply(modifier=body.modifiers[0].name)
body.name='P_v7_CONTINUOUS_REFERENCE_SCULPT'
body.data.update()
strokes={
 'scapular fan': [(-1.05,2.62),(-.77,2.68),(-.49,2.63),(-.28,2.48),(-.13,2.22),(-.18,2.02),(-.39,1.92),(-.61,2.01),(-.75,2.20)],
 'pectoral insertion': [(-1.27,2.36),(-1.12,2.15),(-.97,1.97),(-.78,1.80),(-.53,1.72),(-.34,1.74)],
 'deltoid inner edge': [(-.91,2.51),(-.88,2.33),(-.75,2.20),(-.61,2.01)],
 'triceps diagonal': [(-.17,2.01),(-.17,1.82),(-.30,1.66),(-.41,1.49),(-.44,1.31)],
 'elbow tendon': [(-.54,1.26),(-.40,1.20),(-.27,1.24),(-.15,1.30)],
 'flank fold': [(.06,2.41),(.19,2.22),(.28,2.00),(.20,1.81),(.04,1.75)],
 'pelvic sweep': [(.49,2.06),(.73,1.95),(.91,1.75),(1.03,1.48),(.94,1.30)],
 'forearm facing': [(-.34,1.08),(-.48,.83),(-.66,.48)]
}
sampled=[]
for name,path in strokes.items():
    points=[]
    for a,b in zip(path,path[1:]):
        for i in range(12):
            t=i/12;x=a[0]*(1-t)+b[0]*t;z=a[1]*(1-t)+b[1]*t
            hit,co,normal,idx=body.ray_cast(Vector((x,-3,z)),Vector((0,1,0)))
            if hit:points.append(co.copy())
    sampled.append((name,points))
from mathutils.kdtree import KDTree
points=[p for _,ps in sampled for p in ps]
kd=KDTree(len(points))
for i,p in enumerate(points):kd.insert(p,i)
kd.balance()
normals=[v.normal.copy() for v in body.data.vertices]
groove=[]
for v in body.data.vertices:
    p=v.co.copy();p.y=-abs(p.y)
    dist=kd.find(p)[2]
    # Compact smoothstep brush footprint. A small recessed V fold is sculpted
    # into existing surface points, without adding a positive muscle shell.
    t=max(0,1-dist/.065);w=t*t*(3-2*t)
    v.co-=normals[v.index]*(.027*w)
    groove.append(w)
paint=material('v7 continuous reference-painted skin',(1,1,1))
bs=paint.node_tree.nodes.get('Principled BSDF');vc=paint.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='P_v7_color';paint.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color'])
old_mats=list(body.data.materials)
attr=body.data.color_attributes.new(name='P_v7_color',type='FLOAT_COLOR',domain='CORNER')
def inside(x,z,poly):
    odd=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:odd=not odd
    return odd
pec=[(-1.50,2.75),(-1.23,2.43),(-1.07,2.20),(-.87,1.96),(-.62,1.82),(-.32,1.75),(-.28,1.49),(-1.12,1.45),(-1.5,2.0)]
deltoid=[(-1.04,2.67),(-.72,2.77),(-.40,2.65),(-.11,2.30),(-.12,2.03),(-.39,1.93),(-.61,2.02),(-.84,2.36)]
triceps=[(-.40,1.99),(-.13,2.07),(.01,1.79),(-.13,1.38),(-.39,1.26),(-.55,1.52)]
for poly in body.data.polygons:
    for li in poly.loop_indices:
        i=body.data.loops[li].vertex_index;x,y,z=body.data.vertices[i].co
        color=(.029,.041,.058)
        if z>2.39-.66*(x+.60):color=(.17,.025,.023)
        if inside(x,z,pec):color=(.087,.112,.146)
        if inside(x,z,deltoid) and abs(y)>.39:color=(.195,.029,.026)
        if inside(x,z,triceps) and abs(y)>.46:color=(.17,.028,.025)
        if x<0 and z<1.27:color=(.073,.098,.133)
        if x>.46 and z>1.1:color=(.18,.031,.027)
        if x>.50 and z<1.10:color=(.068,.089,.120)
        if z<.35:color=(.18,.027,.024)
        shade=1-.57*groove[i]
        attr.data[li].color=(*(c*shade for c in color),1)
body.data.materials.clear();body.data.materials.append(paint)
for poly in body.data.polygons:poly.material_index=0
topology['sculptStrokePathsXZ']=strokes
topology['evaluatedBodyVertices']=len(body.data.vertices)

# Tail is a single folded blade-like cage, not lobes layered on a tube.
tv=[(.70,0,1.76),(.93,-.20,1.73),(.93,.20,1.73),(1.27,-.22,1.61),(1.27,.22,1.61),(1.43,-.21,1.58),(1.43,.21,1.58),(1.54,-.15,1.69),(1.54,.15,1.69),(1.70,-.13,1.72),(1.70,.13,1.72),(1.88,-.07,1.61),(1.88,.07,1.61),(1.94,0,1.34),(.96,0,1.45),(1.44,0,1.31),(1.70,0,1.40)]
tf=[(0,2,1),(1,2,4,3),(3,4,6,5),(5,6,8,7),(7,8,10,9),(9,10,12,11),(11,12,13),(0,1,3,14),(0,14,4,2),(3,5,15,14),(4,14,15,6),(5,7,9,16,15),(6,15,16,10,8),(9,11,13,16),(10,16,13,12)]
tm=bpy.data.meshes.new('P folded tail cage');tm.from_pydata(tv,[],tf);tm.update();tail=bpy.data.objects.new('P_v7_edited_folded_tail',tm);scene.collection.objects.link(tail)
for m in mats:tm.materials.append(m)
for p in tm.polygons:p.material_index=0 if p.index<7 else 3;p.use_smooth=True
bm=bmesh.new();bm.from_mesh(tm);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(tm);bm.free()
sub=tail.modifiers.new('Tail plane continuity','SUBSURF');sub.levels=1

# Locked traced image landmarks in native source pixels. They are annotations on
# P.webp, not a new reference image or an inferred orthographic ground truth.
landmarks={'muzzle':(5,44),'eye':(29,25),'crest_tip':(78,2),'withers':(86,30),'deltoid':(98,52),'pectoral_low':(65,87),'near_elbow':(118,98),'near_fore_wrist':(109,133),'near_fore_toes':(97,157),'pelvis':(147,92),'tail_tip':(201,96)}
scene['canonical_landmarks_pixels']=json.dumps(landmarks)
scene['canonical_reference_sha256']=canonical
scene['source_workspace']=SOURCE.relative_to(ROOT).as_posix()
scene['static_gate']='PENDING external static review; no rig, animation or production integration'

# Common v6/v7 lighting and camera settings are reused by render-p-v7.py.
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=1100;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.23,.27,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
floor_mat=material('Review neutral floor',(.14,.17,.19))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.01));floor=bpy.context.object;floor.name='REVIEW_floor';floor.data.materials.append(floor_mat)
for name,loc,power,size in [('key',(-4,-5,7),1000,5),('fill',(-1,5,4),700,5),('rim',(4,1,6),1100,4)]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='REVIEW_'+name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
views={'SIDE':(0,-10,2.15),'FRONT':(-10,0,2.15),'FRONT34':(-6,-10,3.4),'REAR34':(6,-10,3.4),'BACK':(10,0,2.15)}
for name,loc in views.items():
    cam=bpy.data.objects['CAM_'+name];cam.location=loc;cam.rotation_euler=(Vector((-.02,0,1.63))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.85
scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.ops.object.select_all(action='DESELECT')
for o in (body,old,tail):o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_yup=True)
scene.name='P v7 reference retopology / STATIC REVIEW / HOLD'
OUT.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
topology.update({'canonicalSHA256':canonical,'bodyObject':body.name,'sourceWorkspace':SOURCE.relative_to(ROOT).as_posix(),'glbSHA256':hashlib.sha256(GLB.read_bytes()).hexdigest(),'blendSHA256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'staticOnly':True,'landmarks':landmarks})
(E/'authoring-check.json').write_text(json.dumps(topology,indent=2)+'\n')
print('V7_AUTHORING',json.dumps(topology))
if '--render-preview' in sys.argv:
    scene.render.resolution_percentage=65;scene.cycles.samples=16
    scene.render.filepath=str(E/'preview-FRONT34.png');bpy.ops.render.render(write_still=True)
