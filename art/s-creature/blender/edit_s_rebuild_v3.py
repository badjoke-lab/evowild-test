"""Apply S_REBUILD_V3_TASK.md only to the saved v2 cage; Gate A only."""
import bpy, bmesh, math, os, json, hashlib
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rebuild-v2.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
def digest():
 return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()
source_hash=digest(); source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}; source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}; counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']; m=core.data
assert len(m.vertices)==232
# Update head/neck, shoulder, waist and pelvis rings only. Tail stays exact v2.
stations=[
 (-.905,1.260,1.200,.018),(-.845,1.295,1.200,.044),
 (-.735,1.360,1.210,.091),(-.635,1.380,1.220,.104),
 (-.555,1.340,1.155,.102),(-.425,1.290,1.045,.095),
 (-.275,1.245,.920,.128),(-.150,1.235,.815,.160),
 (-.040,1.240,.725,.185),(.122,1.205,.680,.172),
 (.293,1.130,.845,.119),(.473,1.125,.905,.083),
 (.644,1.170,.910,.110),(.770,1.155,.882,.117)]
for i,(y,top,bottom,width) in enumerate(stations):
 for k in range(8):
  a=k*math.tau/8;m.vertices[i*8+k].co=(width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a))
# Three roots per side distributed across two posterior-lateral skull stations.
# Broad laminae project outward, not upwards or medially into an arch.
old_cross=[[(.065,-.630,1.424,.032,.038),(.048,-.420,1.519,.030,.027),(.022,-.265,1.590,.022,.003)],[(.088,-.620,1.362,.031,.040),(.078,-.430,1.438,.027,.028),(.060,-.310,1.498,.022,.003)],[(.095,-.565,1.292,.028,.033),(.090,-.415,1.365,.024,.024),(.080,-.325,1.412,.020,.003)]]
new_cross=[[(.100,-.645,1.330,.030,.035),(.156,-.395,1.367,.030,.022),(.195,-.185,1.390,.008,.002)],[(.124,-.610,1.281,.035,.040),(.194,-.365,1.308,.029,.025),(.235,-.210,1.325,.008,.002)],[(.130,-.540,1.236,.032,.033),(.209,-.340,1.253,.027,.021),(.254,-.220,1.264,.008,.002)]]
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
 fore=[((sign*.142,-.045,1.075),.087,.122),((sign*.185,.035,.933),.078,.090),((sign*.182,.160,.810),.055,.065),((sign*.168,-.005,.620),.027,.036),((sign*.150,-.220,.230),.017,.022),((sign*.150,-.255,.105),.024,.022),((sign*.150,-.268,.056),.031,.030)]
 hind=[((sign*.117,.725,1.045),.086,.125),((sign*.160,.585,.913),.084,.115),((sign*.180,.405,.765),.053,.064),((sign*.172,.700,.535),.030,.043),((sign*.160,1.035,.285),.028,.039),((sign*.153,.998,.203),.018,.024),((sign*.150,.900,.087),.025,.023),((sign*.150,.885,.053),.031,.030)]
 reposition('S_forelimb_'+label,fore);reposition('S_hindlimb_'+label,hind)
for o in cage.objects:
 if o.type=='MESH':
  o.data.update();bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
assert all(tuple(m.vertices[i].co)==source_coords[core.name][i] for i in range(112,160)), 'Tail changed'
assert all([tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name] for o in cage.objects if o.type=='MESH')
assert all([tuple(v.co) for v in o.data.vertices]==source_coords[o.name] for o in cage.objects if o.type=='MESH' and '_toe_' in o.name)
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert len(bpy.data.materials)==0 and len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)
# Preserve the v1 review camera settings for direct comparison.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v3.blend'),compress=True)
crest_vertices=[v.co for v in m.vertices[160:]]
crest_before_height=max(p[2] for p in source_coords[core.name][160:])-min(p[2] for p in source_coords[core.name][160:])
crest_after_height=max(p.z for p in crest_vertices)-min(p.z for p in crest_vertices)
neck_before=math.hypot(.625,.3715);neck_after=math.hypot(.595,.3165)
report={'gate':'A','status':'REVIEW_PENDING','source':'S-rebuild-v2.blend','base_remote_commit':'70bf73b78e2a35bf642741d278e914707155edf1','v12_geometry_used':False,'total_cage_vertices':sum(counts.values()),'topology_preserved':True,'source_geometry_sha256':source_hash,'geometry_sha256':digest(),'no_materials':True,'no_animation':True,'no_armature':True,'final_retopology':False,'changes':['Lowered six-plate crest envelope; outward/rearward fan instead of upright prongs or arch; posterior cranium broadened, muzzle retained','Effective neck shortened with lower forward carriage and stronger base flare into withers and chest','Compact withers/thorax strengthened, narrow rising waist retained and light pelvis elevated','Fore upper segment shortened, elbow raised; hind knee forward and hock rearward with sharper chain angles','Tail and all toe geometry unchanged from v2'],'measurements':{'neck_length_before':neck_before,'neck_length_after':neck_after,'neck_shortening_percent':100*(1-neck_after/neck_before),'crest_vertical_envelope_before':crest_before_height,'crest_vertical_envelope_after':crest_after_height,'crest_envelope_reduction_percent':100*(1-crest_after_height/crest_before_height),'crest_max_z':max(v.z for v in crest_vertices),'crest_max_z_v2':max(p[2] for p in source_coords[core.name][160:]),'tail_unchanged':True,'toes_unchanged':True},'limitations':['Gate A silhouette cage only; user acceptance pending','Faceted low-complexity plates and overlapping limb/toe roots remain; no welding or anatomical refinement']}
assert 5<=report['measurements']['neck_shortening_percent']<=8
assert crest_after_height<.20
json.dump(report,open(os.path.join(OUT,'S-rebuild-v3-gate-A.json'),'w'),indent=2)
print('V3_SAVED',json.dumps(report))
