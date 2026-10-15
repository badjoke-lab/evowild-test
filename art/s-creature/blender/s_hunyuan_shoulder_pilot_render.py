"""Matched real Cycles render. VERSION, TAG, DETAIL supplied by MCP caller."""
import bpy,json,time
from mathutils import Vector
pilot=bpy.app.driver_namespace['shoulder_pilot'];body=pilot['body'];OUT=pilot['OUT']
scene=bpy.context.scene
direction=Vector({'SIDE':(1,0,0),'FRONT':(0,-1,0),'FRONT34':(1,-1,0),'REAR34':(1,1,0),'BACK':(0,1,0),'LEFT_SIDE':(-1,0,0),'LEFT_FRONT34':(-1,-1,0)}[TAG]).normalized()
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=False
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.use_compositing=False;scene.render.use_sequencer=False;scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0;scene.view_settings.look='AgX - Medium High Contrast'
for c in bpy.data.collections:c.hide_render=False
def show(c):
    c.exclude=False
    for x in c.children:show(x)
for layer in scene.view_layers:show(layer.layer_collection)
for ob in scene.objects:ob.hide_render=(ob!=body)
body.hide_set(False);body.hide_render=False;body.hide_viewport=False
for layer in scene.view_layers:layer.material_override=bpy.data.materials['V4_REVIEW_CLAY']
scene.world=bpy.data.worlds['V4_REVIEW_WORLD']
for tag in ['KEY','FILL','RIM']:bpy.data.objects['V4_REVIEW_'+tag].hide_render=False
cam=bpy.data.objects['V4_REVIEW_CAMERA']
cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0))
if DETAIL:target=Vector((-.035,-.32,-.045));width=.85
else:
    p=[v.co for v in pilot['baseline'].vertices]
    rx=[v.dot(right) for v in p];uy=[v.dot(up) for v in p]
    target=right*((min(rx)+max(rx))/2)+up*((min(uy)+max(uy))/2)
    width=max(max(rx)-min(rx),(max(uy)-min(uy))*1.25)*1.13
cam.location=target+direction*5;cam.data.type='ORTHO';cam.data.ortho_scale=width;scene.camera=cam
path=OUT/(VERSION+('_DETAIL_' if DETAIL else '_')+TAG+'.png')
scene.render.filepath=str(path)
current=body.data
try:
    if VERSION=='STAGE1_MATCHED':body.data=pilot['baseline']
    start=time.time();bpy.ops.render.render(write_still=True)
finally:body.data=current
assert path.is_file()
report={'path':path.name,'seconds':round(time.time()-start,2),'engine':scene.render.engine,'samples':24,'resolution':[1000,800],'camera_location':list(cam.location),'camera_rotation':list(cam.rotation_euler),'ortho_scale':width,'target':list(target),'lights':{k:float(bpy.data.objects['V4_REVIEW_'+k].data.energy) for k in ['KEY','FILL','RIM']},'clay_material_override':'V4_REVIEW_CLAY','source_file_not_written':True}
(OUT/(path.stem+'_RENDER.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
