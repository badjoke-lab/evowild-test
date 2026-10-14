"""Actual Cycles render of V3 coordinates or current V4, identical cameras.

Invoked through live Blender MCP with VERSION and TAG. No batch Blender or VM.
"""
import bpy, numpy as np, json, time
from pathlib import Path
from mathutils import Vector
OUT = Path(bpy.data.filepath).resolve().parent
body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4']
scene=bpy.context.scene
mesh=body.data
current=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
base=np.load(OUT/'V3_BASE_COORDS.npy').astype(np.float32)
direction=Vector({'SIDE':(1,0,0),'FRONT':(0,-1,0),'FRONT34':(1,-1,0),'REAR34':(1,1,0),'BACK':(0,1,0)}[TAG]).normalized()
detail=bool(DETAIL)
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=24
scene.cycles.use_denoising=False
scene.render.resolution_x=1000
scene.render.resolution_y=800
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.use_compositing=False
scene.render.use_sequencer=False
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=0
scene.view_settings.look='AgX - Medium High Contrast'
for c in bpy.data.collections:c.hide_render=False
def show(c):
    c.exclude=False
    for x in c.children:show(x)
for layer in scene.view_layers:show(layer.layer_collection)
for ob in scene.objects:ob.hide_render=(ob!=body)
body.hide_set(False)
body.hide_viewport=False
body.hide_render=False
if 'V4_REVIEW_CLAY' not in bpy.data.materials:
    mat=bpy.data.materials.new('V4_REVIEW_CLAY')
    mat.use_nodes=True
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(.24,.29,.32,1)
    bs.inputs['Roughness'].default_value=.8
else:mat=bpy.data.materials['V4_REVIEW_CLAY']
for layer in scene.view_layers:layer.material_override=mat
if 'V4_REVIEW_WORLD' not in bpy.data.worlds:
    world=bpy.data.worlds.new('V4_REVIEW_WORLD')
    world.use_nodes=True
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
    bg.inputs['Color'].default_value=(.13,.15,.18,1)
    bg.inputs['Strength'].default_value=.45
else:world=bpy.data.worlds['V4_REVIEW_WORLD']
scene.world=world
for name,loc,energy,size in [('KEY',(2,-3,3),350,2),('FILL',(-3,-1,1),100,3),('RIM',(1,3,2),250,2)]:
    name='V4_REVIEW_'+name
    if name not in bpy.data.objects:
        data=bpy.data.lights.new(name,'AREA')
        data.energy=energy;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new(name,data)
        scene.collection.objects.link(ob)
        ob.location=loc
        ob.rotation_euler=(Vector((0,-.2,0))-ob.location).to_track_quat('-Z','Y').to_euler()
    bpy.data.objects[name].hide_render=False
name='V4_REVIEW_CAMERA'
if name not in bpy.data.objects:
    data=bpy.data.cameras.new(name)
    cam=bpy.data.objects.new(name,data)
    scene.collection.objects.link(cam)
else:cam=bpy.data.objects[name]
cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
q=cam.rotation_euler.to_quaternion()
right=q@Vector((1,0,0));up=q@Vector((0,1,0))
if detail:
    target=Vector((-.035,-.32,-.045));width=.85
else:
    # V3 fixed framing is shared by all versions.
    p=[Vector(v) for v in base]
    rx=[v.dot(right) for v in p];uy=[v.dot(up) for v in p]
    target=right*((min(rx)+max(rx))/2)+up*((min(uy)+max(uy))/2)
    width=max(max(rx)-min(rx),(max(uy)-min(uy))*1.25)*1.13
cam.location=target+direction*5
cam.data.type='ORTHO';cam.data.ortho_scale=width
scene.camera=cam
path=OUT/(VERSION+('_DETAIL_' if detail else '_')+TAG+'.png')
scene.render.filepath=str(path)
start=time.time()
try:
    if VERSION=='V3':
        mesh.vertices.foreach_set('co',base.ravel());mesh.update()
    elif VERSION!='V4':raise ValueError(VERSION)
    bpy.ops.render.render(write_still=True)
finally:
    mesh.vertices.foreach_set('co',current.ravel());mesh.update()
assert path.is_file()
print(json.dumps({'render':str(path),'engine':scene.render.engine,'samples':scene.cycles.samples,'seconds':round(time.time()-start,2),'v4_coordinates_restored':True}))
