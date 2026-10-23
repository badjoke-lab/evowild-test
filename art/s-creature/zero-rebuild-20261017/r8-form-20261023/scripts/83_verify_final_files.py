"""Independent reopen: final rig repeats all 93 evaluated trial poses exactly."""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
variant=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'B';suffix='' if variant=='B' else variant
OUT=ROOT/('evidence/FINAL_FILES'+suffix+'_INDEPENDENT_RELOAD.json');assert not OUT.exists()
def digest_body(b):
    m=b.data
    return hashlib.sha256(repr(([tuple(v.co) for v in m.vertices],
        [(tuple(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],
        [tuple(d.color) for d in m.color_attributes['R8 plane coordinates'].data])).encode()).hexdigest()
def evaluate(b):
    rows=[]
    for time in np.linspace(1,24,93):
        f=int(time);bpy.context.scene.frame_set(f,subframe=float(time-f));bpy.context.view_layer.update()
        ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
        p=np.array([v.co[:] for v in m.vertices],dtype=np.float32);ev.to_mesh_clear()
        rows.append({'time':float(time),'evaluated_position_sha256':hashlib.sha256(p.tobytes()).hexdigest()})
    return rows
checks={};geom={};poses={};sha={}
for label,rel in [('trial','verification/S_ZERO_R8_FORM_TRIAL_'+variant+'.blend'),('rig','verification/S_ZERO_R8'+suffix+'_HIP_DEFORMATION_VERIFIED.blend'),('static','S_ZERO_CANDIDATE_REVISED_R8'+suffix+'.blend')]:
    p=ROOT/rel;sha[label]=hashlib.sha256(p.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False)
    b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];bpy.context.scene.frame_set(1)
    geom[label]=digest_body(b)
    if label!='static':poses[label]=evaluate(b)
    else:
        checks={'armatures':sum(o.type=='ARMATURE' for o in bpy.data.objects),'actions':len(bpy.data.actions),
          'vertex_groups':sum(len(o.vertex_groups) for o in bpy.data.objects if o.type=='MESH'),
          'armature_modifiers':sum(md.type=='ARMATURE' for o in bpy.data.objects for md in o.modifiers)}
    assert hashlib.sha256(p.read_bytes()).hexdigest()==sha[label]
assert poses['trial']==poses['rig']
assert len(set(geom.values()))==1 and not any(checks.values())
OUT.write_text(json.dumps({'blender':bpy.app.version_string,'independent_process':True,'file_sha256':sha,
  'body_geometry_and_surface_chart_identical':True,'formal_static_has_no_rig':checks,
  'final_rig_evaluated_coordinates_equal_trial_at_all_93_times':True,'times':poses['rig'],
  'source_files_unmodified':True},indent=2)+'\n')
print('FINAL_R8_RELOADED_EXACT; static unrigged; rig evaluated bytes identical at 93 times',flush=True)
