"""Render the exact delivered v6/v7 GLBs under identical camera/light settings."""
import bpy,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence/p-canonical-3d-v7-20261012'
W=ROOT/'work/p-canonical-v7/rendered';W.mkdir(parents=True,exist_ok=True)
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
versions=['v6','v7']
if '--v7-only' in sys.argv:versions=['v7']
if '--preview' in sys.argv:views=['FRONT34'];versions=['v7']
records=json.loads((E/'render-provenance.json').read_text())[:5] if '--v7-only' in sys.argv else []
for version in versions:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/p-creature/workspaces/P-v7-reference-retopology.blend'))
    for o in list(bpy.data.objects):
        if o.type=='ARMATURE' or (o.type=='MESH' and not o.name.startswith('REVIEW_')):bpy.data.objects.remove(o,do_unlink=True)
    asset=ROOT/f'public/models/evowild-p/p-canonical-{version}.glb'
    bpy.ops.import_scene.gltf(filepath=str(asset))
    for o in bpy.context.scene.objects:
        if o.type=='ARMATURE':o.animation_data_clear();o.data.pose_position='REST'
    scene=bpy.context.scene
    if '--preview' in sys.argv:scene.render.resolution_percentage=65;scene.cycles.samples=16
    for name in views:
        scene.camera=bpy.data.objects['CAM_'+name]
        output=W/(('preview-' if '--preview' in sys.argv else '')+(version+'-' if version=='v6' else '')+name+'.png')
        scene.render.filepath=str(output)
        bpy.ops.render.render(write_still=True)
        records.append({'version':version,'view':name,'image':output.name,'glbSHA256':hashlib.sha256(asset.read_bytes()).hexdigest(),'cameraLocation':list(scene.camera.location),'cameraRotation':list(scene.camera.rotation_euler),'orthoScale':scene.camera.data.ortho_scale,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'engine':scene.render.engine,'samples':scene.cycles.samples,'pose':'static rest'})
if '--preview' not in sys.argv:(E/'render-provenance.json').write_text(json.dumps(records,indent=2)+'\n')
