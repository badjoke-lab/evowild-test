# Run inside Blender's Scripting workspace.
# Creates a lightweight, repeatable scene for S-type blockout/review.
import bpy
import math
from mathutils import Vector

# ----- helpers -----
def ensure_collection(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

def remove_object(obj):
    bpy.data.objects.remove(obj, do_unlink=True)

def make_camera(name, location, target, ortho_scale=6.0):
    data = bpy.data.cameras.new(name + '_DATA')
    data.type = 'ORTHO'
    data.ortho_scale = ortho_scale
    obj = bpy.data.objects.new(name, data)
    review.objects.link(obj)
    obj.location = location
    # Track camera -Z to target, Y up.
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return obj

def make_area(name, location, energy=700.0, size=5.0):
    data = bpy.data.lights.new(name + '_DATA', type='AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(name, data)
    review.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (math.radians(55), 0, math.radians(30))
    return obj

# ----- scene cleanup -----
for obj in list(bpy.data.objects):
    remove_object(obj)

for coll_name in ['S_MODEL', 'CUE_BAND', 'REVIEW']:
    old = bpy.data.collections.get(coll_name)
    if old and old != bpy.context.scene.collection:
        # Keep collection datablock if already linked; empty contents were removed above.
        pass

model = ensure_collection('S_MODEL')
cue = ensure_collection('CUE_BAND')
review = ensure_collection('REVIEW')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.filepath = '//output/review/'

# Neutral world.
scene.world.color = (0.055, 0.055, 0.055)

# Review target at approximate torso center. Adjust if needed after blockout.
target = (0.0, 0.0, 1.4)

cams = {
    'CAM_FRONT':  ((0.0, -8.0, 1.4), 6.0),
    'CAM_SIDE':   ((8.0, 0.0, 1.4), 6.0),
    'CAM_FRONT34':((5.7, -5.7, 2.0), 6.0),
    'CAM_REAR34': ((-5.7, 5.7, 2.0), 6.0),
}
for name, (loc, scale) in cams.items():
    make_camera(name, loc, target, scale)

# Lighting kept simple so form, not materials, drives evaluation.
make_area('KEY', (4.5, -4.5, 7.0), 900.0, 5.0)
make_area('FILL', (-4.0, -2.0, 4.5), 500.0, 4.0)
make_area('RIM', (1.0, 5.0, 5.5), 650.0, 4.0)

# Ground plane.
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
plane = bpy.context.object
plane.name = 'REVIEW_GROUND'
# Move plane into REVIEW collection only.
for c in list(plane.users_collection):
    c.objects.unlink(plane)
review.objects.link(plane)

mat = bpy.data.materials.new('REVIEW_GROUND_MAT')
mat.diffuse_color = (0.14, 0.14, 0.14, 1.0)
plane.data.materials.append(mat)

# Placeholder empty for notes / origin reference.
empty = bpy.data.objects.new('S_ORIGIN_REFERENCE', None)
review.objects.link(empty)
empty.location = target

scene.camera = bpy.data.objects['CAM_FRONT34']
print('EvoWild S review scene ready. Build new geometry in S_MODEL only.')
