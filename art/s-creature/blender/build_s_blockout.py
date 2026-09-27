"""New reference-led S blockout. Blender 3.4+/4.x; never imports existing creatures.
Coordinate system: +Z up, -Y forward, X bilateral. Units are modelling units.
"""
import bpy, math, os, json
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
# Use supplied scene bootstrap, with engine compatibility only.
setup=open(os.path.join(ROOT,'blender/setup_scene.py')).read()
if bpy.app.version < (4,2,0): setup=setup.replace('BLENDER_EEVEE_NEXT','BLENDER_EEVEE')
exec(compile(setup,'setup_scene.py','exec'))
model=bpy.data.collections['S_MODEL']; skin=[]
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.68
 return m
clay=material('Neutral sculpt clay',(.34,.41,.45)); crestmat=clay

def mesh(name,verts,faces,sub=2,merge=True,mat=clay):
 me=bpy.data.meshes.new(name+'_editable');me.from_pydata(verts,[],faces);me.update()
 import bmesh
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(name,me);model.objects.link(ob);ob.data.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 if sub:
  mo=ob.modifiers.new('Editable surface subdivision','SUBSURF');mo.levels=sub;mo.render_levels=sub
 if merge:skin.append(ob)
 return ob

def loft(name,stations,n=12,sub=2,merge=True):
 # stations = center, transverse radius, sagittal radius. Continuous anatomical cross sections.
 vs=[]
 for i,(p,rx,rz) in enumerate(stations):
  p=Vector(p);a=Vector(stations[max(0,i-1)][0]);b=Vector(stations[min(len(stations)-1,i+1)][0]);t=(b-a).normalized()
  u=Vector((1,0,0));u=(u-t*u.dot(t)).normalized();v=u.cross(t).normalized()
  for j in range(n):
   th=2*math.pi*j/n; q=p+u*(rx*math.cos(th))+v*(rz*math.sin(th));vs.append(q)
 fs=[]
 for i in range(len(stations)-1):
  for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
 fs.extend([tuple(reversed(range(n))),tuple((len(stations)-1)*n+j for j in range(n))])
 return mesh(name,vs,fs,sub,merge)

# Thorax is deeper at shoulder; lifted ventral abdomen; separate elevated pelvic arch.
loft('Thorax_abdomen_pelvis',[
 ((0,-.99,2.20),.12,.21),((0,-.82,2.20),.27,.42),((0,-.48,2.22),.33,.45),
 ((0,-.1,2.24),.29,.38),((0,.26,2.25),.205,.245),((0,.58,2.27),.22,.22),
 ((0,.87,2.29),.29,.31),((0,1.1,2.24),.26,.28),((0,1.24,2.20),.13,.16)],n=16)
loft('Neck_integrated_keel',[
 ((0,-.68,2.20),.24,.30),((0,-.96,2.39),.235,.28),((0,-1.20,2.57),.18,.22),
 ((0,-1.43,2.78),.14,.17),((0,-1.59,2.98),.145,.17),((0,-1.68,3.04),.13,.13)],n=16)
# One central cranial volume, tapered angular muzzle. No bilateral split.
loft('Central_skull_muzzle',[
 ((0,-2.20,2.79),.055,.055),((0,-2.14,2.83),.085,.085),((0,-1.98,2.96),.125,.11),
 ((0,-1.84,3.07),.175,.155),((0,-1.66,3.09),.16,.165),((0,-1.53,3.03),.09,.105)],n=12,sub=2)
# Long swept crown is a single sagittal blade with a broad fused cranial root.
loft('Sagittal_crown',[
 ((0,-1.80,3.13),.14,.11),((0,-1.62,3.28),.15,.14),((0,-1.36,3.48),.125,.135),
 ((0,-1.00,3.73),.09,.11),((0,-.59,3.96),.052,.075),((0,-.18,4.14),.022,.032),
 ((0,.12,4.24),.003,.004)],n=12)
# Secondary low swept temple fins grow from the same root, not free antler rods.
for s,label in [(-1,'L'),(1,'R')]:
 loft('Temporal_sweep_'+label,[
  ((s*.10,-1.77,3.07),.065,.09),((s*.18,-1.51,3.16),.065,.105),
  ((s*.20,-1.17,3.30),.046,.07),((s*.19,-.80,3.48),.009,.014)],n=10)
 # Shoulder strongly angled, compact elbow and thin wrist; taper varied per segment.
 loft('Forelimb_'+label,[
  ((s*.24,-.67,2.39),.13,.19),((s*.33,-.71,2.20),.17,.215),
  ((s*.36,-.53,1.95),.125,.17),((s*.35,-.40,1.70),.085,.115),
  ((s*.35,-.43,1.59),.083,.09),((s*.355,-.56,1.37),.067,.085),
  ((s*.36,-.71,1.03),.045,.059),((s*.365,-.84,.66),.043,.049),
  ((s*.37,-.89,.43),.062,.072),((s*.37,-.95,.28),.045,.052),
  ((s*.37,-1.04,.15),.075,.07)],n=12)
 # Hindlimb: hip -> forward knee -> rear hock -> narrow metatarsus.
 loft('Hindlimb_'+label,[
  ((s*.20,.88,2.35),.17,.21),((s*.29,.88,2.17),.21,.25),
  ((s*.35,.68,1.94),.17,.20),((s*.36,.51,1.72),.12,.14),
  ((s*.365,.55,1.56),.095,.11),((s*.37,.79,1.34),.085,.11),
  ((s*.38,1.04,1.05),.052,.075),((s*.38,1.12,.87),.072,.085),
  ((s*.38,1.10,.71),.047,.065),((s*.38,.98,.37),.04,.05),
  ((s*.38,.94,.20),.055,.065),((s*.38,.84,.13),.09,.065)],n=12)
 # Three narrow, grounded toes, no hooves/paws.
 for ybase,prefix in [(-1.02,'Fore'),(.85,'Hind')]:
  for j in [-1,0,1]:
   x=s*.37+j*.065
   loft(prefix+'_digit_'+label+str(j),[
    ((x,ybase+.05,.14),.045,.058),((x+j*.018,ybase-.065,.10),.038,.048),
    ((x+j*.025,ybase-.19-(.025 if j==0 else 0),.065),.024,.028),
    ((x+j*.028,ybase-.25-(.025 if j==0 else 0),.043),.004,.009)],n=8,sub=1)
# Tail is an extension of the pelvis, swept down with a terminal narrow blade.
loft('Tail_axial',[
 ((0,1.07,2.29),.17,.16),((0,1.30,2.24),.155,.145),((0,1.50,2.01),.105,.12),
 ((0,1.63,1.73),.078,.11),((0,1.79,1.49),.068,.1),((0,2.02,1.30),.049,.08),
 ((0,2.22,1.12),.017,.04),((0,2.34,1.02),.003,.003)],n=12)
loft('Tail_terminal_keel',[
 ((0,1.75,1.55),.065,.08),((0,1.91,1.39),.075,.16),((0,2.12,1.20),.04,.15),
 ((0,2.34,1.02),.002,.002)],n=10)
# Save editable components before union; retained hidden in final .blend.
source=bpy.data.collections.new('S_EDITABLE_SOURCE');bpy.context.scene.collection.children.link(source)
for ob in skin:
 copy=ob.copy();copy.data=ob.data.copy();source.objects.link(copy)
source.hide_render=True;source.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-blockout-v1-working.blend'))
# Sculpt-friendly continuous surface, removes intersecting part seams.
bpy.ops.object.select_all(action='DESELECT')
for ob in skin:
 ob.select_set(True);bpy.context.view_layer.objects.active=ob
 for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.context.view_layer.objects.active=skin[0];bpy.ops.object.join();body=bpy.context.object;body.name='S_organism_blockout'
rem=body.modifiers.new('Unified_anatomical_surface','REMESH');rem.mode='VOXEL';rem.voxel_size=.018;rem.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=rem.name)
sm=body.modifiers.new('Light_surface_relax','SMOOTH');sm.factor=.45;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
# Neutral clay, intentionally no eyes, markings, textures, or decorative anatomy.
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=768;scene.render.resolution_y=768
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.18,.21,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
for ob in bpy.data.collections['REVIEW'].objects:
 if ob.type=='LIGHT':ob.rotation_euler=(Vector((0,0,2))-ob.location).to_track_quat('-Z','Y').to_euler()
target=Vector((0,0,2.10))
for name,loc in {'CAM_FRONT':(0,-9,2.1),'CAM_SIDE':(9,0,2.1),'CAM_FRONT34':(6,-7,3.3),'CAM_REAR34':(-6,7,3.3)}.items():
 cam=bpy.data.objects[name];cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=5.2
scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-blockout-v1.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'S-blockout-v1.glb'),use_selection=True,export_format='GLB')
state=json.load(open(os.path.join(ROOT,'HANDOFF_STATE.json')));state.update(stage='S-blockout-v1',current_stage='S-blockout-v1',branch='feat/s-creature-model',current_model_file='output/S-blockout-v1.blend',latest_export='output/S-blockout-v1.glb',next_action='Render the four supplied review cameras and compare torso/limb proportions against references 01 and 02.',blockers=[])
json.dump(state,open(os.path.join(ROOT,'HANDOFF_STATE.json'),'w'),indent=2)
open(os.path.join(ROOT,'CHECKPOINT.md'),'w').write('''# S-type checkpoint\ncurrent_stage: S-blockout-v1 — awaiting four-view review\nbranch: feat/s-creature-model\ncurrent_model_file: output/S-blockout-v1.blend\ndone:\n- New S mesh from references 01/02; no previous procedural geometry used.\n- Unified head/crown/neck, thorax, abdomen, pelvis, four jointed limbs, digits, tail.\n- Editable source cross sections retained in hidden S_EDITABLE_SOURCE collection.\n- Saved .blend and .glb.\nnext_action: Render the four supplied review cameras and compare torso/limb proportions against references 01 and 02.\nquality_issues:\n- Blockout proportions require first visual review; no acceptance claimed.\nblockers: none\n''')
exec(compile(open(os.path.join(ROOT,'blender/render_review.py')).read().replace("'//output/review/'",repr(os.path.join(OUT,'review/v1/'))),'render_review.py','exec'))
