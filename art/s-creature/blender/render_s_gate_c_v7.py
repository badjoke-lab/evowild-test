"""Render five review views from S-gateC-v7.blend."""
import bpy,os,json,hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','gate-c-v7')
os.makedirs(REVIEW,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v7.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
def digest():
    return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()
report=json.load(open(os.path.join(OUT,'S-gateC-v7.json')))
assert digest()==report['base_geometry_sha256']
for stem in ('side','front','front34','rear34','back'):
    bpy.context.scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    bpy.context.scene.render.filepath=os.path.join(REVIEW,'S_gateC_'+stem+'.png')
    bpy.ops.render.render(write_still=True)
assert digest()==report['base_geometry_sha256']
report.update(rendered_views=['SIDE','FRONT','FRONT34','REAR34','BACK'],base_geometry_unchanged_during_render=True)
json.dump(report,open(os.path.join(OUT,'S-gateC-v7.json'),'w'),indent=2)
print('GATE_C_V7_FIVE_VIEWS_DONE_STOPPED')
