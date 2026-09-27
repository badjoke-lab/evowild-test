"""Render review views from the recovered S blockout without modifying geometry."""
import bpy
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output", "review", "v3-recovery")
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
# Fast deterministic review render only; do not save the .blend after this.
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

views = [
    ("front", "CAM_FRONT"),
    ("side", "CAM_SIDE"),
    ("front34", "CAM_FRONT34"),
    ("rear34", "CAM_REAR34"),
]

for stem, cam_name in views:
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        raise RuntimeError(f"Missing review camera: {cam_name}")
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, f"S_blockout_{stem}.png")
    bpy.ops.render.render(write_still=True)

print("Rendered v3 recovery review to", OUT)
