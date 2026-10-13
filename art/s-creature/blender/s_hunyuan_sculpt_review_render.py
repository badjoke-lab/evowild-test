"""Identical clay lighting and orthographic framing for before/after actual meshes."""
import bpy
from mathutils import Vector
from pathlib import Path
DIRECTIONS={'SIDE':(1,0,0),'FRONT':(0,-1,0),'FRONT34':(1,-1,0),'REAR34':(1,1,0),'BACK':(0,1,0)}
def setup(body):
 s=bpy.context.scene
 for c in bpy.data.collections:c.hide_render=False
 def show(l):
  l.exclude=False
  for c in l.children:show(c)
 for v in s.view_layers:show(v.layer_collection)
 for o in s.objects:o.hide_render=o!=body
 body.hide_render=False;body.hide_viewport=False;body.hide_set(False)
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=48;s.cycles.use_denoising=False
 s.render.resolution_x=900;s.render.resolution_y=720;s.render.resolution_percentage=100
 s.render.use_compositing=False;s.render.use_sequencer=False;s.render.film_transparent=False
 s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0
 w=bpy.data.worlds.new('REVIEW_WORLD');s.world=w;w.use_nodes=True
 w.node_tree.nodes['Background'].inputs['Color'].default_value=(.13,.15,.18,1)
 w.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
 mat=bpy.data.materials.new('REVIEW_CLAY');mat.use_nodes=True
 bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.24,.29,.32,1);bs.inputs['Roughness'].default_value=.8
 # View-layer override leaves the saved original materials intact.
 for v in s.view_layers:v.material_override=mat
 for name,loc,energy,size in [('KEY',(2,-3,3),350,2.0),('FILL',(-3,-1,1),100,3),('RIM',(1,3,2),250,2)]:
  d=bpy.data.lights.new('REVIEW_'+name,'AREA');d.energy=energy;d.shape='DISK';d.size=size
  ob=bpy.data.objects.new(d.name,d);s.collection.objects.link(ob);ob.location=loc
  ob.rotation_euler=(Vector((0,-.2,0))-ob.location).to_track_quat('-Z','Y').to_euler()
 return s

def render(body, points, out, prefix):
 s=setup(body);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 points=[Vector(p) for p in points]
 views=[]
 for detail in (False,True):
  for tag,direction in DIRECTIONS.items():
   if detail and tag not in ('SIDE','FRONT','FRONT34'):continue
   direction=Vector(direction).normalized()
   d=bpy.data.cameras.new('REVIEW_'+tag);cam=bpy.data.objects.new(d.name,d);s.collection.objects.link(cam);s.camera=cam
   cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
   q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0))
   if detail:
    target=Vector((-.035,-.32,-.045));width=.85
   else:
    rx=[p.dot(right) for p in points];uy=[p.dot(up) for p in points]
    target=right*((min(rx)+max(rx))/2)+up*((min(uy)+max(uy))/2)
    width=max(max(rx)-min(rx),(max(uy)-min(uy))*1.25)*1.13
   cam.location=target+direction*5;d.type='ORTHO';d.ortho_scale=width
   name=prefix+('_DETAIL_' if detail else '_')+tag+'.png'
   s.render.filepath=str(out/name);bpy.ops.render.render(write_still=True)
   views.append(name)
 return views
