"""Apply S_REBUILD_V2_TASK.md only to the saved v1 cage; Gate A only."""
import bpy, bmesh, math, os, json, hashlib
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v1.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
def digest():
 return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()
source_hash=digest(); counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']; m=core.data
assert len(m.vertices)==232
# Same 20 section rings. Head carriage moves towards shoulder and down;
# base width and depth grow 18%; torso span contracts 10%; tail contracts 15%.
stations=[
 (-.935,1.310,1.250,.018),(-.875,1.345,1.250,.044),
 (-.765,1.410,1.260,.083),(-.665,1.430,1.270,.094),
 (-.585,1.380,1.210,.091),(-.455,1.300,1.100,.082),
 (-.285,1.205,.975,.105),(-.150,1.170,.850,.130),
 (-.040,1.155,.742,.171),(.122,1.145,.685,.157),
 (.293,1.115,.830,.115),(.473,1.115,.900,.083),
 (.644,1.155,.900,.106),(.770,1.140,.870,.116),
 (.914,1.080,.950,.074),(1.0245,1.035,.940,.055),
 (1.186, .945,.860,.042),(1.373, .825,.705,.038),
 (1.543, .6975,.6025,.034),(1.7045,.590,.580,.002)]
for i,(y,top,bottom,width) in enumerate(stations):
 for k in range(8):
  a=k*math.tau/8;m.vertices[i*8+k].co=(width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a))
# Six skull-panel rooted plates, three overlapping layers on each side.
# Low, broad laminar cross sections prevent front/back upright prongs.
# Primary root-to-tip axes ~26 deg; primary length reduced ~25% with medially converging broad tips.
old_cross=[[(.064,-.56,1.595,.017,.055),(.081,-.34,1.690,.010,.040),(.087,-.19,1.755,.001,.001)],[(.093,-.56,1.470,.018,.043),(.112,-.36,1.550,.010,.029),(.119,-.21,1.590,.001,.001)],[(.095,-.51,1.400,.016,.039),(.112,-.32,1.423,.010,.025),(.116,-.17,1.437,.001,.001)]]
new_cross=[[(.065,-.630,1.424,.032,.038),(.048,-.420,1.519,.030,.027),(.022,-.265,1.590,.022,.003)],[(.088,-.620,1.362,.031,.040),(.078,-.430,1.438,.027,.028),(.060,-.310,1.498,.022,.003)],[(.095,-.565,1.292,.028,.033),(.090,-.415,1.365,.024,.024),(.080,-.325,1.412,.020,.003)]]
for si,sign in enumerate((1,-1)):
 for level in range(3):
  for ci,(old,new) in enumerate(zip(old_cross[level],new_cross[level])):
   x,y,z,t,d=old;nx,ny,nz,nt,nd=new
   for j in range(4):
    v=m.vertices[160+si*36+level*12+ci*4+j];p=v.co.copy()
    v.co=(sign*(nx+((sign*p.x-x)/t)*nt),ny,nz+((p.z-z)/d)*nd)
# Reshape existing limb rings, retain count/connectivity and toes.
def reposition(name,chain,sides=8):
 mesh=bpy.data.objects[name].data
 assert len(mesh.vertices)==len(chain)*sides
 for i,(center,wx,wy) in enumerate(chain):
  c=Vector(center);tan=Vector(chain[min(i+1,len(chain)-1)][0])-Vector(chain[max(i-1,0)][0]);tan.normalize()
  lat=Vector((1,0,0));lat=(lat-tan*lat.dot(tan)).normalized();sag=tan.cross(lat).normalized()
  for k in range(sides):
   a=k*math.tau/sides;mesh.vertices[i*sides+k].co=c+lat*(wx*math.cos(a))+sag*(wy*math.sin(a))
for sign,label in ((-1,'L'),(1,'R')):
 fore=[((sign*.130,-.035,1.015),.080,.115),((sign*.170,.025,.860),.073,.094),((sign*.174,.140,.705),.052,.060),((sign*.167,.005,.555),.031,.040),((sign*.150,-.220,.230),.018,.024),((sign*.150,-.255,.105),.024,.022),((sign*.150,-.268,.056),.031,.030)]
 hind=[((sign*.112,.730,1.017),.090,.135),((sign*.158,.640,.877),.089,.124),((sign*.179,.490,.745),.053,.064),((sign*.170,.690,.600),.037,.053),((sign*.160,.990,.340),.029,.043),((sign*.153,.990,.230),.019,.025),((sign*.150,.900,.087),.025,.023),((sign*.150,.885,.053),.031,.030)]
 reposition('S_forelimb_'+label,fore);reposition('S_hindlimb_'+label,hind)
 for o in cage.objects:
  if o.type=='MESH' and o.name.startswith('S_hind_toe_'+label):
   for v in o.data.vertices:v.co.y-=.085
for o in cage.objects:
 if o.type=='MESH':
  o.data.update();bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert len(bpy.data.materials)==0 and len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)
# Preserve the v1 review camera settings for direct comparison.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v2.blend'),compress=True)
report={'gate':'A','status':'REVIEW_PENDING','source':'S-rebuild-v1.blend','base_remote_commit':'d43db097d9263eb45feda275ae74430589d67808','v12_geometry_used':False,'total_cage_vertices':sum(counts.values()),'topology_preserved':True,'source_geometry_sha256':source_hash,'geometry_sha256':digest(),'no_materials':True,'no_animation':True,'no_armature':True,'final_retopology':False,'changes':['Six lower overlapping skull-rooted rear-swept plates; broader posterior cranium, muzzle retained','Shorter lower head/neck carriage; neck base width and depth increased ~18%','Torso length -10%, anterior thorax depth increased, ventral waist raised, light pelvis elevated','Compact fore elbow and long light distal segment; stronger hind thigh, forward knee and rearward hock','Tail length -15%, continuous taper and restrained terminal lamina'],'measurements':{'neck_length_before':math.hypot(.69,.485),'neck_length_after':math.hypot(.625,.3715),'torso_length_ratio':.9,'neck_base_width_ratio':1.18,'neck_base_depth_ratio':1.18,'tail_length_ratio':.85},'limitations':['Gate A silhouette cage only; user acceptance pending','Separate overlapping limb/toe roots retained; no welding or anatomical refinement']}
json.dump(report,open(os.path.join(OUT,'S-rebuild-v2-gate-A.json'),'w'),indent=2)
print('V2_SAVED',json.dumps(report))
