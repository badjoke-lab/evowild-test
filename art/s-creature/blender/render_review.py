# Run inside Blender after S-blockout geometry exists.
# Writes exactly four review views to //output/review/.
import bpy
import os

scene = bpy.context.scene
base = bpy.path.abspath('//output/review/')
os.makedirs(base, exist_ok=True)

views = [
    ('front', 'CAM_FRONT'),
    ('side', 'CAM_SIDE'),
    ('front34', 'CAM_FRONT34'),
    ('rear34', 'CAM_REAR34'),
]

for stem, cam_name in views:
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        raise RuntimeError(f'Missing camera: {cam_name}. Run setup_scene.py first.')
    scene.camera = cam
    scene.render.filepath = os.path.join(base, f'S_blockout_{stem}.png')
    bpy.ops.render.render(write_still=True)

print('Rendered 4 S-blockout review views to', base)
