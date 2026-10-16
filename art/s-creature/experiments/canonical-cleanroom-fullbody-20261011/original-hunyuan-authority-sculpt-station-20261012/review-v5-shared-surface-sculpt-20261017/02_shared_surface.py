"""A single branching control surface. No independent solids; no source topology edit."""
import bpy,bmesh,json,math
from mathutils import Vector
s=bpy.app.driver_namespace['shared_sculpt'];body=s['body'];out=s['out'];bvh=s['bvh']
assert not bpy.data.objects.get('S_RIGHT_SHARED_CHEST_SHOULDER_ARM')
assert s['fingerprint'](body.data)==s['before_fingerprint']
# Transverse thoracic rails, dorsal -> lateral -> ventral. Internal rails are
# individually authored asymmetric sections; outer rails lie on the reference.
ys=[-.53,-.485,-.445,-.405,-.365,-.325,-.285,-.235,-.19]
# The bulge is rounded anteriorly, narrower inferiorly, oblique at its crown.
xs=[
 [.025,.040,.045,.045,.043,.038,.030,.023,.012],
 [.024,.047,.066,.077,.085,.082,.067,.043,.017],
 [.025,.060,.095,.124,.137,.127,.100,.063,.018],
 [.026,.074,.118,.148,.159,.147,.117,.069,.018],
 [.027,.084,.130,.158,.164,.145,.110,.065,.019],
 [.028,.085,.126,.148,.145,.118,.082,.048,.020],
 [.028,.073,.106,.127,.122,.095,.066,.040,.020],
 [.026,.062,.091,.103,.100,.086,.063,.040,.018],
 [.024,.054,.075,.083,.081,.073,.055,.034,.015]]
zs=[
 [.198,.170,.133,.094,.058,.024,.000,-.018,-.028],
 [.172,.146,.112,.073,.030,-.008,-.050,-.075,-.088],
 [.150,.132,.105,.065,.019,-.032,-.080,-.113,-.128],
 [.145,.132,.104,.058,.009,-.045,-.097,-.132,-.148],
 [.153,.143,.115,.067,.013,-.041,-.094,-.130,-.148],
 [.158,.148,.122,.076,.022,-.027,-.073,-.110,-.129],
 [.153,.140,.115,.073,.022,-.022,-.062,-.094,-.110],
 [.148,.130,.099,.053,.004,-.038,-.075,-.098,-.110],
 [.142,.119,.085,.043,-.001,-.042,-.074,-.096,-.105]]
verts=[];faces=[]
for r,y in enumerate(ys):
 for c in range(9):
  p=Vector((xs[r][c],y,zs[r][c]))
  if r in (0,8) or c in (0,8):
   centre=Vector((0,y,.045 if r<2 else .005));direction=(p-centre).normalized()
   hit=bvh.ray_cast(centre+direction*.8,-direction)
   if hit[0] and hit[0].x>0:p=hit[0]
  verts.append(tuple(p))
def ix(r,c):return r*9+c
# Remove four *new control* faces to grow the arm out of their shared perimeter.
for r in range(8):
 for c in range(8):
  if r in (3,4) and c in (5,6):continue
  faces.append((ix(r,c),ix(r,c+1),ix(r+1,c+1),ix(r+1,c)))
root=[ix(3,5),ix(4,5),ix(5,5),ix(5,6),ix(5,7),ix(4,7),ix(3,7),ix(3,6)]
root_centre=sum((Vector(verts[i]) for i in root),Vector())/len(root)
centres=[root_centre,Vector((.120,-.329,-.148)),Vector((.135,-.290,-.192)),Vector((.127,-.251,-.240)),Vector((.107,-.252,-.283)),Vector((.095,-.275,-.318))]
radii=[(.040,.046),(.039,.049),(.031,.037),(.024,.028),(.022,.024)]
# Root correspondence follows the actual socket plane; frames turn along the arm.
t0=(centres[1]-centres[0]).normalized();u0=Vector((1,0,0));u0=(u0-t0*u0.dot(t0)).normalized();v0=t0.cross(u0).normalized()
angles=[math.atan2((Vector(verts[i])-root_centre).dot(v0),(Vector(verts[i])-root_centre).dot(u0)) for i in root]
prev=root
for k,centre in enumerate(centres[1:],1):
 tangent=(centres[min(k+1,len(centres)-1)]-centres[k-1]).normalized()
 u=Vector((1,0,0));u=(u-tangent*u.dot(tangent)).normalized();v=tangent.cross(u).normalized();rx,rv=radii[k-1]
 curr=[]
 for a in angles:
  # Non-circular arm cross-section: broad exterior belly, flatter inner return.
  xfactor=1.0 if math.cos(a)>=0 else .84
  p=centre+u*(rx*math.cos(a)*xfactor)+v*(rv*math.sin(a))
  curr.append(len(verts));verts.append(tuple(p))
 for j in range(8):faces.append((prev[j],prev[(j+1)%8],curr[(j+1)%8],curr[j]))
 prev=curr
# Compact unused grid point within socket. The surface is one welded component.
used=sorted({i for f in faces for i in f});remap={i:j for j,i in enumerate(used)}
mesh=bpy.data.meshes.new('RIGHT_SHARED_SURFACE_CONTROL');mesh.from_pydata([verts[i] for i in used],[],[tuple(remap[i] for i in f) for f in faces]);mesh.update()
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
ob=bpy.data.objects.new('S_RIGHT_SHARED_CHEST_SHOULDER_ARM',mesh);bpy.context.collection.objects.link(ob)
for p in mesh.polygons:p.use_smooth=True
# Display subdivision only, kept low: un-applied 400 quad preview from 100 controls.
mod=ob.modifiers.new('ONE_LEVEL_FORM_PREVIEW','SUBSURF');mod.levels=1;mod.render_levels=1
# This mask only affects display of the intact reference mesh, never its vertices.
g=body.vertex_groups.new(name='SHARED_SURFACE_PREVIEW_RETAIN')
keep=[v.index for v in body.data.vertices if not (v.co.x>.016 and -.495<v.co.y<-.22 and -.32<v.co.z<.145)]
g.add(keep,1.,'REPLACE');mask=body.modifiers.new('SHARED_SURFACE_DISPLAY_ONLY','MASK');mask.vertex_group=g.name
for o in bpy.context.selected_objects:o.select_set(False)
ob.select_set(True);bpy.context.view_layer.objects.active=ob
s['control']=ob;s['mask']=mask;s['mask_group']=g;s['control_grid_map']=remap
s['arm_centres']=[tuple(c) for c in centres]
assert s['fingerprint'](body.data)==s['before_fingerprint']
info={'method':'Single shared thoracic surface with arm extruded from a welded 8-vertex socket; frames follow curved centreline','vertices':len(mesh.vertices),'faces':len(mesh.polygons),'arm_centres':s['arm_centres'],'arm_radii':radii,'source_geometry_unchanged':True,'source_topology_deleted':0,'final_body_connection':False,'preview_subdivision_level':1}
(out/'01_SHARED_CORE_BUILD.json').write_text(json.dumps(info,indent=2))
(out/'01_SHARED_CORE_GEOMETRY.json').write_text(json.dumps({'vertices':[list(v.co) for v in mesh.vertices],'faces':[list(p.vertices) for p in mesh.polygons]},indent=2))
s['view']('SIDE','01_SHARED_CORE')
print(json.dumps(info))
