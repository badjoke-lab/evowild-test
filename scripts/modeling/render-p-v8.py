"""Render delivered v7/v8 GLBs with the same v7 cameras and studio lighting."""
import bpy,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence/p-canonical-3d-v8-20261013'
W=ROOT/'work/p-canonical-v8/rendered';W.mkdir(parents=True,exist_ok=True)
views=['SIDE','FRONT','FRONT34','REAR34','BACK']
versions=['v7','v8'];records=[]
for version in versions:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/p-creature/workspaces/P-v8-layered-anatomy.blend'))
    for o in list(bpy.data.objects):
        if o.type=='ARMATURE' or (o.type=='MESH' and not o.name.startswith('REVIEW_')):bpy.data.objects.remove(o,do_unlink=True)
    asset=ROOT/f'public/models/evowild-p/p-canonical-{version}.glb'
    bpy.ops.import_scene.gltf(filepath=str(asset))
    assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
    scene=bpy.context.scene;scene.cycles.samples=32;scene.cycles.use_denoising=False
    scene.render.resolution_x=1100;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    for name in views:
        scene.camera=bpy.data.objects['CAM_'+name]
        output=W/f'{version}-{name}.png';scene.render.filepath=str(output)
        bpy.ops.render.render(write_still=True)
        records.append({'version':version,'view':name,'image':('v7-' if version=='v7' else '')+name+'.webp','renderSourcePNG':output.name,'glbSHA256':hashlib.sha256(asset.read_bytes()).hexdigest(),'cameraLocation':list(scene.camera.location),'cameraRotation':list(scene.camera.rotation_euler),'orthoScale':scene.camera.data.ortho_scale,'resolution':[1100,900],'engine':scene.render.engine,'samples':32,'pose':'static rest','displayEncoding':'WebP quality 94; no retouch'})
    (E/'render-provenance.json').write_text(json.dumps(records,indent=2)+'\n')
# Clay renders expose geometry independently of the new material boundaries.
clay=bpy.data.materials.new('REVIEW ONLY neutral clay');clay.diffuse_color=(.22,.22,.22,1);clay.use_nodes=True
bs=clay.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.22,.22,.22,1);bs.inputs['Roughness'].default_value=.8
for version in versions:
    for o in list(bpy.data.objects):
        if o.type=='MESH' and not o.name.startswith('REVIEW_'):bpy.data.objects.remove(o,do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/f'public/models/evowild-p/p-canonical-{version}.glb'))
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and not o.name.startswith('REVIEW_'):
            o.data.materials.clear();o.data.materials.append(clay)
            for p in o.data.polygons:p.material_index=0
    scene.camera=bpy.data.objects['CAM_FRONT34'];scene.render.filepath=str(W/f'{version}-clay-FRONT34.png');bpy.ops.render.render(write_still=True)
print('V8_RENDER_COMPLETE',len(records),'five-view color renders plus 2 clay checks')
