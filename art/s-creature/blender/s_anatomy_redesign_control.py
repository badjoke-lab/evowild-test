"""One initial low density anatomical blockout; no final topology or save."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
OUT=Path(bpy.data.filepath).parent
assert OUT.name=='review-v5-anatomy-redesign'
assert not bpy.data.objects.get('CONTROL_OBLIQUE_SHOULDER')
body=next(o for o in bpy.data.objects if o.type=='MESH')
# Non-destructive preview mask only; source vertices and faces remain untouched.
g=body.vertex_groups.new(name='CONTROL_PREVIEW_RETAIN')
keep=[v.index for v in body.data.vertices if not (v.co.x>.025 and -.475<v.co.y<-.235 and -.235<v.co.z<.125)]
g.add(keep,1,'REPLACE');m=body.modifiers.new('CONTROL_PREVIEW_MASK','MASK');m.vertex_group=g.name
controls=[]
def loft(name,rings,n=10):
 verts=[];faces=[]
 for x,y,z,rx,ry in rings:
  for i in range(n):
   t=2*math.pi*i/n;verts.append((x+rx*math.cos(t),y+ry*math.sin(t),z))
 for j in range(len(rings)-1):
  for i in range(n):a=j*n+i;b=j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
 faces.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*n+i for i in range(n))])
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
 for p in mesh.polygons:p.use_smooth=True
 controls.append(o);return o
# Integrated design region, separate control volumes remain editable before any connection.
loft('CONTROL_CHEST_TRANSITION',[(.035,-.367,-.215,.026,.035),(.042,-.393,-.14,.039,.053),(.044,-.395,-.06,.046,.061),(.04,-.363,.015,.038,.063),(.03,-.32,.072,.026,.046)])
loft('CONTROL_OBLIQUE_SHOULDER',[(.067,-.371,-.155,.015,.025),(.089,-.378,-.105,.033,.047),(.102,-.358,-.04,.039,.061),(.091,-.325,.025,.034,.067),(.066,-.283,.075,.024,.047),(.043,-.257,.105,.012,.018)])
loft('CONTROL_UPPER_ARM',[(.08,-.307,-.30,.013,.018),(.086,-.325,-.252,.022,.027),(.091,-.339,-.205,.028,.036),(.093,-.348,-.157,.029,.039),(.084,-.338,-.116,.022,.028)],12)
bpy.context.preferences.view.smooth_view=0
for o in bpy.context.selected_objects:o.select_set(False)
controls[1].select_set(True);bpy.context.view_layer.objects.active=controls[1]
def view(tag,label='01_CONTROL'):
 direction=Vector({'SIDE':(1,0,0),'FRONT':(0,-1,0),'FRONT34':(1,-1,0)}[tag])
 for a in bpy.context.screen.areas:
  if a.type=='VIEW_3D':
   s=a.spaces.active;s.overlay.show_overlays=False;s.shading.type='SOLID';s.shading.light='STUDIO';s.shading.show_cavity=False
   s.region_3d.view_perspective='ORTHO';s.region_3d.view_location=Vector((0,-.345,-.055));s.region_3d.view_distance=.63;s.region_3d.view_rotation=direction.to_track_quat('Z','Y');s.region_3d.update();a.tag_redraw()
 bpy.context.view_layer.update()
 print(bpy.types.blendermcp_server.get_viewport_screenshot(max_size=1400,filepath=str(OUT/(label+'_'+tag+'.png'))))
(OUT/'CONTROL_COUNTS.json').write_text(json.dumps({o.name:{'vertices':len(o.data.vertices),'faces':len(o.data.polygons)} for o in controls},indent=2))
bpy.app.driver_namespace['anatomy_control']={'view':view,'controls':controls,'body':body}
view('SIDE')
