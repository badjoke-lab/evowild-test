"""Gate C v10: read-only production topology / rig readiness audit."""
import bpy,os,json,hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
src=os.path.join(OUT,'S-gateC-v9.blend')
bpy.ops.wm.open_mainfile(filepath=src)

cage=bpy.data.collections['S_REBUILD_GATE_A']
detail=bpy.data.collections.get('S_PRODUCTION_DETAIL')

def digest():
    return hashlib.sha256(b''.join(
        repr(tuple(v.co)).encode()
        for o in sorted(cage.objects,key=lambda o:o.name)
        if o.type=='MESH'
        for v in o.data.vertices
    )).hexdigest()

mesh_report={}
for o in sorted(cage.objects,key=lambda o:o.name):
    if o.type!='MESH': continue
    mesh_report[o.name]={
      'vertices':len(o.data.vertices),
      'polygons':len(o.data.polygons),
      'materials':[m.name for m in o.data.materials],
      'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],
    }

detail_report={}
if detail:
    for o in sorted(detail.objects,key=lambda o:o.name):
        detail_report[o.name]={
          'type':o.type,
          'location':[float(x) for x in o.location],
          'scale':[float(x) for x in o.scale],
          'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],
          'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],
        }

limb_names=['S_forelimb_L','S_forelimb_R','S_hindlimb_L','S_hindlimb_R']
limb_ring_centroids={}
for name in limb_names:
    o=bpy.data.objects[name]
    n=len(o.data.vertices)
    assert n%8==0
    rings=n//8
    centers=[]
    for r in range(rings):
        pts=[o.data.vertices[r*8+k].co for k in range(8)]
        c=sum((p.copy() for p in pts),Vector())/8
        centers.append([float(c.x),float(c.y),float(c.z)])
    limb_ring_centroids[name]=centers

armatures=[o.name for o in bpy.data.objects if o.type=='ARMATURE']
actions=[a.name for a in bpy.data.actions]
unapplied_modifiers=sum(len(o.modifiers) for o in bpy.data.objects if o.type=='MESH')
toe_count=sum(1 for o in cage.objects if o.type=='MESH' and '_toe_' in o.name)
cage_mesh_count=sum(1 for o in cage.objects if o.type=='MESH')

report={
 'gate':'C','pass':'v10','status':'AUDIT_COMPLETE','source':'S-gateC-v9.blend',
 'geometry_sha256':digest(),
 'surface_pattern_decision':'M1_SOLID_NO_ADDED_PATTERN',
 'cage_mesh_count':cage_mesh_count,
 'toe_mesh_count':toe_count,
 'mesh_report':mesh_report,
 'detail_objects':detail_report,
 'armatures':armatures,
 'actions':actions,
 'unapplied_modifier_count':unapplied_modifiers,
 'limb_ring_centroids':limb_ring_centroids,
 'production_state':{
   'visual_design_reviewed':True,
   'base_geometry_still_multi_object':cage_mesh_count>1,
   'armature_present':bool(armatures),
   'animation_present':bool(actions),
   'modifiers_remain_non_destructive':unapplied_modifiers>0,
   'eyes_and_cue_band_are_separate_detail_objects':bool(detail_report),
 },
 'next_required_decisions':[
   'Choose rig-prep strategy for separate core/limb/toe meshes versus consolidated production mesh',
   'Create production armature and weight/skin test before animation',
   'Decide whether to keep non-destructive modifiers for rig source or apply them to a derived production copy'
 ]
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v10-production-readiness.json'),'w'),indent=2)
print('GATE_C_V10_AUDIT',json.dumps({
 'cage_mesh_count':cage_mesh_count,
 'toe_mesh_count':toe_count,
 'armatures':armatures,
 'actions':actions,
 'unapplied_modifier_count':unapplied_modifiers,
 'detail_object_count':len(detail_report)
}))
