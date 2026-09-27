"""Resume from saved v1 .blend; reference-led proportion correction only."""
import bpy,os,math,json,bmesh
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-blockout-v1.blend'))
# Reuse the actual saved editable geometry, not an earlier game creature.
source=bpy.data.collections['S_EDITABLE_SOURCE'];model=bpy.data.collections['S_MODEL']
for ob in list(model.objects):bpy.data.objects.remove(ob,do_unlink=True)
source.hide_viewport=False;source.hide_render=False
for ob in list(source.objects):
 source.objects.unlink(ob);model.objects.link(ob)
bpy.data.collections.remove(source)
skin=list(model.objects);clay=bpy.data.materials['Neutral sculpt clay']

def shift_head(p):
 p.z-=.16
 p.y-=.08
 return p
# Lower and narrow the head/neck, retain a long forward transition.
for ob in skin:
 name=ob.name
 if name.startswith('Neck'):
  for v in ob.data.vertices:
   f=max(0,min(1,(v.co.z-2.23)/.8));v.co.x*=1-.22*f;v.co.z-=.16*f;v.co.y-=.08*f
 elif name.startswith('Central_skull'):
  for v in ob.data.vertices:shift_head(v.co)
 elif name.startswith('Sagittal_crown'):
  # Thin the tall swollen blade around each saved ring centre.
  vs=ob.data.vertices
  for k in range(0,len(vs),12):
   ring=list(vs[k:k+12]);c=sum((v.co for v in ring),Vector())/len(ring)
   for v in ring:
    v.co=c+(v.co-c)*.59;v.co.x*=.88;shift_head(v.co)
 elif name.startswith('Temporal'):
  for v in ob.data.vertices:
   v.co.y=-1.77+(v.co.y+1.77)*.65;v.co.z=3.07+(v.co.z-3.07)*.52;shift_head(v.co)
 elif name.startswith('Thorax'):
  for v in ob.data.vertices:
   # Athletic chest, rising belly and narrow waist instead of smooth barrel.
   if -.8<v.co.y<.2:
    v.co.x*=.91
    if v.co.z>2.25:v.co.z+=.055
   if .05<v.co.y<.7 and v.co.z<2.25:v.co.z+=.055
 elif name.startswith('Forelimb'):
  for v in ob.data.vertices:
   if 1.0<v.co.z<1.55:v.co.x*=1.01
   if v.co.x<0:
    f=max(0,min(1,(2.15-v.co.z)/1.85));v.co.y-=.34*f
 elif name.startswith('Fore_digit'):
  for v in ob.data.vertices:
   if v.co.x<0:v.co.y-=.34
 elif name.startswith('Hindlimb'):
  for v in ob.data.vertices:
   if v.co.x<0:
    f=max(0,min(1,(2.15-v.co.z)/1.9));v.co.y+=.28*f
 elif name.startswith('Hind_digit'):
  for v in ob.data.vertices:
   if v.co.x<0:v.co.y+=.28
 elif name.startswith('Tail'):
  for v in ob.data.vertices:
   if v.co.y>1.3:v.co.x*=.8
 for mod in ob.modifiers:
  if mod.type=='SUBSURF':mod.levels=1;mod.render_levels=1

# Replace only the v1 soft skull with a designed cranial wedge and mandible.
for ob in list(skin):
 if ob.name.startswith('Central_skull'):
  skin.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)

def surface(name,verts,faces):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 ob=bpy.data.objects.new(name,me);model.objects.link(ob);ob.data.materials.append(clay);skin.append(ob)
 for p in me.polygons:p.use_smooth=True
 return ob

def section_mesh(name,rows):
 # Each row defines transverse width and ventral/dorsal limits, with flat dorsal plane.
 vs=[]
 profile=[(1,.30),(.72,1),(-.72,1),(-1,.30),(-.72,-.75),(0,-1),(.72,-.75)]
 for y,z,w,h in rows:
  for x,a in profile:vs.append((x*w,y,z+a*h))
 n=len(profile);fs=[]
 for i in range(len(rows)-1):
  for j in range(n):fs.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
 fs+=[tuple(reversed(range(n))),tuple((len(rows)-1)*n+j for j in range(n))]
 return surface(name,vs,fs)
head=section_mesh('Central_cranium_v2',[
 (-2.29,2.645,.050,.040),(-2.23,2.69,.077,.065),(-2.08,2.80,.097,.068),
 (-1.97,2.87,.137,.107),(-1.82,2.905,.17,.126),(-1.66,2.895,.128,.128),(-1.59,2.86,.067,.069)])
be=head.modifiers.new('Cranial_edge_relief','BEVEL');be.width=.028;be.segments=2
section_mesh('Mandible_v2',[
 (-2.24,2.632,.043,.019),(-2.08,2.694,.068,.030),(-1.97,2.736,.10,.041),
 (-1.79,2.765,.12,.075),(-1.70,2.78,.077,.060)])
# Broad structural scapular keels, not surface decoration; root embedded in chest.
for s in [-1,1]:
 vs=[(s*.14,-.82,2.38),(s*.21,-.55,2.66),(s*.38,-.61,2.41),(s*.42,-.52,2.16),
     (s*.28,-.70,1.99),(s*.21,-.86,2.15),(s*.15,-.54,2.32)]
 fs=[(0,1,2),(0,2,5),(2,3,4,5),(5,4,6),(4,3,6),(3,2,1,6),(0,5,6,1)]
 ob=surface('Scapular_keel_'+str(s),vs,fs);b=ob.modifiers.new('Broad_ridge_relief','BEVEL');b.width=.06;b.segments=2
# Retain all edited cross sections for direct work in Blender after handoff.
source=bpy.data.collections.new('S_EDITABLE_SOURCE');bpy.context.scene.collection.children.link(source)
for ob in skin:
 cp=ob.copy();cp.data=ob.data.copy();source.objects.link(cp)
source.hide_render=True;source.hide_viewport=True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-blockout-v2-working.blend'))
bpy.ops.object.select_all(action='DESELECT')
for ob in skin:
 ob.select_set(True);bpy.context.view_layer.objects.active=ob
 for m in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
bpy.context.view_layer.objects.active=skin[0];bpy.ops.object.join();body=bpy.context.object;body.name='S_organism_blockout_v2'
r=body.modifiers.new('Continuous_sculpt_surface','REMESH');r.mode='VOXEL';r.voxel_size=.010;r.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=r.name)
s=body.modifiers.new('Minimal_relax','SMOOTH');s.factor=.22;s.iterations=2;bpy.ops.object.modifier_apply(modifier=s.name)
# Small recessed orbital landmarks: no Cue Band, no large glowing mascot eyes.
for sign in [-1,1]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(sign*.126,-1.971,2.892))
 cutter=bpy.context.object;cutter.scale=(.05,.06,.035);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.context.view_layer.objects.active=body
 mod=body.modifiers.new('Small_orbital_recess','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
for p in body.data.polygons:p.use_smooth=True
scene=bpy.context.scene
# Remove visible ground horizon while keeping supplied review lighting/cameras.
bpy.data.objects['REVIEW_GROUND'].scale=(10,10,1)
scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-blockout-v2.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'S-blockout-v2.glb'),use_selection=True,export_format='GLB')
state=json.load(open(os.path.join(ROOT,'HANDOFF_STATE.json')))
state.update(stage='S-blockout-v2',current_stage='S-blockout-v2',current_model_file='output/S-blockout-v2.blend',latest_export='output/S-blockout-v2.glb',next_action='Inspect the four v2 renders for crown-root continuity, angular head structure, and joint visibility before further edits.')
json.dump(state,open(os.path.join(ROOT,'HANDOFF_STATE.json'),'w'),indent=2)
# Use supplied four-view script; version directory prevents overwriting v1 review.
script=open(os.path.join(ROOT,'blender/render_review.py')).read().replace("'//output/review/'",repr(os.path.join(OUT,'review/v2/')))
exec(compile(script,'render_review.py','exec'))
