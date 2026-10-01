"""Gate A only: fresh low-complexity S silhouette cage.
No donor geometry is opened. Stop modeling before the separate five-view render.
Coordinates normalize shoulder height to approximately 1.0. Front is -Y.
"""
import bpy,bmesh,math,os,json,hashlib
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
cage=bpy.data.collections.new('S_REBUILD_GATE_A');scene.collection.children.link(cage)
review=bpy.data.collections.new('S_REBUILD_REVIEW');scene.collection.children.link(review)
verts=[];faces=[];smooth=[]
def vertex(p):verts.append(tuple(p));return len(verts)-1
def face(ids,is_smooth=True):faces.append(tuple(ids));smooth.append(is_smooth)
# Core: wedge head first, then neck, thorax/waist/pelvis, then tapered tail.
# Ring values: Y, dorsal Z, ventral Z, lateral half width.
stations=[
 (-1.00,1.380,1.320,.018),(-.94,1.415,1.320,.044),
 (-.83,1.480,1.330,.078),(-.73,1.500,1.340,.085),
 (-.65,1.450,1.280,.082),(-.52,1.340,1.170,.070),
 (-.35,1.220,1.040,.085),(-.18,1.120,.890,.110),
 (-.04,1.110,.760,.145),(.14,1.100,.710,.150),
 (.33,1.075,.780,.119),(.53,1.090,.850,.083),
 (.72,1.120,.850,.108),(.86,1.100,.830,.120),
 (1.02,1.040,.910,.080),(1.15,1.000,.890,.060),
 (1.34,.900,.770,.055),(1.56,.760,.600,.060),
 (1.76,.610,.450,.037),(1.95,.480,.430,.004)]
rings=[]
for y,top,bottom,width in stations:
 ring=[]
 for k in range(8):
  a=k*math.tau/8
  ring.append(vertex((width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a))))
 rings.append(ring)
face(tuple(reversed(rings[0])))
# Each laminar crest grows out of a removed skull side panel, sharing root edges.
# This is not a central sagittal spike or a set of floating antlers.
crest_roots={(2,1),(2,2),(2,0),(2,3),(3,0),(3,3)}
root_quads={}
for r in range(len(rings)-1):
 for k in range(8):
  ids=(rings[r][k],rings[r+1][k],rings[r+1][(k+1)%8],rings[r][(k+1)%8])
  if (r,k) in crest_roots:root_quads[(r,k)]=ids
  else:face(ids)
face(rings[-1])
crest_specs=[]
for sign,ks in [(1,(1,0,0)),(-1,(2,3,3))]:
 for level,(r,k) in enumerate(zip((2,2,3),ks)):
  base=list(root_quads[(r,k)]);prev=base
  if level==0:
   cross=[(.064,-.56,1.595,.017,.055),(.081,-.34,1.690,.010,.040),(.087,-.19,1.755,.001,.001)]
  elif level==1:
   cross=[(.093,-.56,1.470,.018,.043),(.112,-.36,1.550,.010,.029),(.119,-.21,1.590,.001,.001)]
  else:
   cross=[(.095,-.51,1.400,.016,.039),(.112,-.32,1.423,.010,.025),(.116,-.17,1.437,.001,.001)]
  for x,y,z,thickness,depth in cross:
   points=[(sign*(x-thickness),y,z+depth),(sign*(x+thickness),y,z+depth),(sign*(x+thickness),y,z-depth),(sign*(x-thickness),y,z-depth)]
   # Preserve root perimeter order; select the closest cyclic correspondence.
   candidates=[]
   for pp in (points,list(reversed(points))):
    for shift in range(4):
     order=pp[shift:]+pp[:shift]
     cost=sum((Vector(verts[a])-Vector(b)).length_squared for a,b in zip(prev,order))
     candidates.append((cost,order))
   points=min(candidates,key=lambda t:t[0])[1];current=[vertex(p) for p in points]
   for j in range(4):face((prev[j],current[j],current[(j+1)%4],prev[(j+1)%4]),False)
   prev=current
  face(tuple(reversed(prev)),False)
  crest_specs.append({'side':sign,'layer':level,'root_skull_panel':[r,k],'rearward_tip_y':cross[-1][1],'tip_z':cross[-1][2]})
mesh=bpy.data.meshes.new('S_rebuild_v1_core_cage');mesh.from_pydata(verts,[],faces);mesh.update()
core=bpy.data.objects.new('S_rebuild_core_head_crest_neck_torso_tail',mesh);cage.objects.link(core)
for p,v in zip(mesh.polygons,smooth):p.use_smooth=v
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
# Long shaped limb chains: asymmetric sagittal joint rhythms, mirrored across X.
# Separate overlapping root cages are intentional at Gate A; no final welding or retopology.
def loft(name,chain,sides=8):
 vs=[];fs=[]
 for i,(center,wx,wy) in enumerate(chain):
  c=Vector(center)
  tangent=Vector(chain[min(i+1,len(chain)-1)][0])-Vector(chain[max(i-1,0)][0]);tangent.normalize()
  lateral=Vector((1,0,0));lateral=(lateral-tangent*lateral.dot(tangent)).normalized()
  sagittal=tangent.cross(lateral).normalized()
  for k in range(sides):
   a=k*math.tau/sides;vs.append(tuple(c+lateral*(wx*math.cos(a))+sagittal*(wy*math.sin(a))))
 for i in range(len(chain)-1):
  for k in range(sides):fs.append((i*sides+k,(i+1)*sides+k,(i+1)*sides+(k+1)%sides,i*sides+(k+1)%sides))
 fs.append(tuple(reversed(range(sides))));fs.append(tuple((len(chain)-1)*sides+k for k in range(sides)))
 m=bpy.data.meshes.new(name+'_cage');m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);cage.objects.link(o)
 for p in m.polygons:p.use_smooth=True
 bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
 return o
for sign,label in [(-1,'L'),(1,'R')]:
 fore=[((sign*.115,-.030,.985),.083,.120),((sign*.155,.040,.850),.077,.095),((sign*.168,.105,.680),.047,.055),((sign*.163,-.030,.520),.032,.052),((sign*.150,-.220,.230),.021,.028),((sign*.150,-.255,.105),.026,.024),((sign*.150,-.268,.056),.031,.030)]
 hind=[((sign*.109,.815,.982),.084,.130),((sign*.153,.755,.850),.078,.110),((sign*.175,.665,.730),.047,.057),((sign*.169,.820,.568),.040,.065),((sign*.160,1.065,.310),.026,.039),((sign*.153,1.073,.220),.021,.028),((sign*.150,.985,.087),.026,.023),((sign*.150,.970,.053),.031,.030)]
 loft('S_forelimb_'+label,fore);loft('S_hindlimb_'+label,hind)
 # Three small separated racing toes per foot; no hoof/paw mass.
 for front,ybase in [(True,-.268),(False,.970)]:
  for toe in (-1,0,1):
   x=sign*.150+toe*.022;length=.091 if toe==0 else .075
   loft(('S_fore' if front else 'S_hind')+'_toe_'+label+'_'+str(toe),[
    ((x,ybase,.060),.011,.015),((x+toe*.006,ybase-.030,.028),.013,.016),((x+toe*.010,ybase-length,.018),.008,.011),((x+toe*.010,ybase-length-.010,.018),.002,.003)],sides=6)
# No materials, no eyes, Cue Band, textures, rig, animation or donor objects.
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.66,.66,.66)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=False
scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Neutral review world');scene.world.color=(.045,.052,.061)
scene.view_settings.view_transform='Standard'
scene.render.resolution_x=1024;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
# Fixed orthographic review cameras; all five inspect the same cage.
target=Vector((0,.43,.875))
for stem,location in [('side',(6,.43,.875)),('front',(0,-6,.875)),('front34',(4.4,-4.4,2.0)),('rear34',(-4.4,4.4,2.0)),('back',(0,6,.875))]:
 data=bpy.data.cameras.new('S_REBUILD_CAM_'+stem.upper());data.type='ORTHO';data.ortho_scale=3.50 if stem in ('side','front34','rear34') else 2.75
 o=bpy.data.objects.new(data.name,data);review.objects.link(o);o.location=location;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['S_REBUILD_CAM_FRONT34']
bpy.context.view_layer.objects.active=core;core.select_set(True)
counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
report={'gate':'A','status':'REVIEW_PENDING','output':'S-rebuild-v1.blend','built_from':'empty_scene','v12_used_as_geometry_source':False,'source_lock':'S_MODELING_IMAGE_LOCK.md','approved_image':'EvoWild Run S-type Modeling Image v1.0','total_cage_vertices':sum(counts.values()),'mesh_objects':counts,'crest':{'type':'six skull-rooted backward-swept laminar plates','central_sagittal_horn':False,'shared_root_panels':crest_specs},'forelimb_joint_yz':[list(p[0][1:]) for p in fore],'hindlimb_joint_yz':[list(p[0][1:]) for p in hind],'toes_per_foot':3,'no_materials':len(bpy.data.materials)==0,'no_animation':len(bpy.data.actions)==0,'no_armature':not any(o.type=='ARMATURE' for o in bpy.data.objects),'no_cue_band':True,'final_retopology':False,'geometry_sha256':hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest(),'notes':['Low-complexity silhouette cage only; no anatomical or surface refinement.','Limb and toe root cages overlap; production junction welding is deferred.','No gate acceptance claimed. Stop after the five renders.']}
assert report['total_cage_vertices']<2000 and report['no_materials'] and report['no_animation'] and report['no_armature']
with open(os.path.join(OUT,'S-rebuild-v1-gate-A.json'),'w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v1.blend'),compress=True)
print('S_REBUILD_GATE_A',json.dumps(report))
