"""Reload the DELIVERED rescue GLB and render real five-camera evidence."""
import bpy, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence/p-canonical-3d-v7b-rescue-20261014'
src=ROOT/'art/p-creature/workspaces/P-v7b-rescue-static.blend'
glb=ROOT/'public/models/evowild-p/p-canonical-v7b-rescue.glb'
assert src.is_file() and glb.is_file()
bpy.ops.wm.open_mainfile(filepath=str(src))
# Strip the existing authoring meshes: render only what loads from the GLB.
for o in list(bpy.data.objects):
    if o.type=='MESH' and not o.name.startswith('REVIEW_'):
        bpy.data.objects.remove(o,do_unlink=True)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(glb))
loaded=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
assert loaded,'No actual GLB mesh reimported'
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=12
scene.render.resolution_x=1100;scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
records=[]
for view in views:
    scene.camera=bpy.data.objects['CAM_'+view]
    scene.render.filepath=str(E/(view+'.png'))
    bpy.ops.render.render(write_still=True)
    records.append({
      'view':view,'sourceGLB':'public/models/evowild-p/p-canonical-v7b-rescue.glb',
      'GLBSHA256':hashlib.sha256(glb.read_bytes()).hexdigest(),
      'render':view+'.png',
      'engine':'CYCLES','samples':12,
      'cameraLocation':list(scene.camera.location),
      'cameraRotation':list(scene.camera.rotation_euler),
      'orthographicScale':scene.camera.data.ortho_scale
    })
(E/'RENDER_PROVENANCE.json').write_text(json.dumps({'actualReimportMeshes':len(loaded),'views':records},indent=2)+'\n')
print('P_RESCUE_RENDER_VALIDATED',len(loaded),len(records))
