"""Save R7 static candidate from formal R6, with verification rig kept separate.

Reject trial A. Transfer only reviewed local coordinates from guarded trial B.
Audit pre-existing BVH candidates, original-surface normals and protected data.
"""
import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/R7_SAVE_AND_STATIC_AUDIT.json';assert not OUT.exists()
STATIC=ROOT/'S_ZERO_CANDIDATE_REVISED_R7.blend'
RIG=ROOT/'verification/S_ZERO_R7_HIP_DEFORMATION_VERIFIED_B.blend'
assert not STATIC.exists() and not RIG.exists()
audit=json.loads((ROOT/'evidence/INDEPENDENT_R6_R7B_SWEEP.json').read_text())
assert audit['protected_meshes_exact']==140 and audit['rig_bones_action_exact']
assert audit['R7_using_original_R6_rest_denominators']['1']['rest_normal_dot_negative']==0
old=np.load(ROOT/'evidence/R6_BODY_ARRAYS.npz');r0=old['rest'];t=old['tris'];w0=old['weights']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'verification/S_ZERO_R7_HIP_TRIAL_B.blend'),load_ui=False)
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];bpy.context.scene.frame_set(1)
r1=np.array([v.co[:] for v in body.data.vertices])
body.data.calc_loop_triangles()
polygons=np.array([tri.polygon_index for tri in body.data.loop_triangles])
original_cross=np.cross(r0[t[:,1]]-r0[t[:,0]],r0[t[:,2]]-r0[t[:,0]])
new_cross=np.cross(r1[t[:,1]]-r1[t[:,0]],r1[t[:,2]]-r1[t[:,0]])
normal_cosine=np.sum(original_cross*new_cross,axis=1)/(np.linalg.norm(original_cross,axis=1)*np.linalg.norm(new_cross,axis=1))
assert normal_cosine.min()>.99499
shift=np.linalg.norm(r1-r0,axis=1)
changed=np.where(shift>0)[0]
assert shift.max()<.004001
static_normals={'min_cosine':float(normal_cosine.min()),'max_degrees':float(math.degrees(math.acos(np.clip(normal_cosine.min(),-1,1)))),
 'negative_count':int((normal_cosine<0).sum())}
collisions=[]
baseframes=audit['records']['R6']['frames'];newframes=audit['records']['R7']['frames']
for before,after in zip(baseframes,newframes):
    if 'contacts' not in before:continue
    assert before['contacts']['candidate_self_pairs']==after['contacts']['candidate_self_pairs']
    # One borderline dorsal-mantle overlap toggles by one between frames; record it.
    assert all(abs(after['contacts']['hip_to_other_mesh_BVH'].get(k,0)-v)<=1 for k,v in before['contacts']['hip_to_other_mesh_BVH'].items())
for pair in baseframes[0]['contacts']['candidate_self_pairs']:
    idx=np.unique(t[pair]);coords=r0[idx]
    collisions.append({'triangle_ids':pair,'polygon_ids':polygons[pair].tolist(),'vertex_ids':idx.tolist(),
     'centers':[r0[t[i]].mean(axis=0).tolist() for i in pair],
     'bounds':[coords.min(axis=0).tolist(),coords.max(axis=0).tolist()],
     'R7_rest_exact':bool(np.array_equal(r0[idx],r1[idx])),
     'all_fixed_pelvis_weights':bool(np.all(w0[idx,0]==1)),
     'same_original_polygon':bool(polygons[pair[0]]==polygons[pair[1]])})
projection={}
for view in ['SIDE','FRONT','FRONT34','REAR34','BACK']:
    cam=bpy.data.objects['CAM_'+view];rotation=np.array(cam.matrix_world.to_quaternion().inverted().to_matrix())
    screen=(r1-r0)@rotation.T
    projection[view]={'max_projected_displacement_at_128px_vertical':float(np.linalg.norm(screen[:,:2],axis=1).max()*128/cam.data.ortho_scale),
     'ortho_scale':float(cam.data.ortho_scale)}
sc=bpy.context.scene;sc.frame_set(1);sc['stage']='R7_GUARDED_HIP_DEFORMATION_VERIFICATION_ONLY'
sc['candidate_status']='REVISE; bounded local mesh edit and cotangent weights improve hip stress; not locomotion or production KEEP'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(RIG),compress=True)

def mesh_signature(o,geometry=True):
    m=o.data
    return hashlib.sha256(repr((([tuple(v.co) for v in m.vertices] if geometry else None),
     [(tuple(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],
     [(a.name,a.domain,a.data_type,[tuple(d.color) for d in a.data]) for a in m.color_attributes],
     [list(r) for r in o.matrix_world],[mat.name if mat else None for mat in m.materials])).encode()).hexdigest()

source=ROOT/'protected/S_ZERO_R6_STATIC_PROTECTED.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
assert np.array_equal(np.array([v.co[:] for v in b.data.vertices]),r0)
objects=[o for o in bpy.data.collections['S_ZERO_CREATURE'].objects if o.type=='MESH']
protected={o.name:mesh_signature(o) for o in objects if o!=b}
surface=mesh_signature(b,False)
for v,p in zip(b.data.vertices,r1):v.co=p
b.data.update()
assert mesh_signature(b,False)==surface
b['r7_revision']='Guarded local pelvic mesh relaxation only. Validation weights and rig live in a separate file.'
sc=bpy.context.scene;sc['stage']='S_ZERO_CANDIDATE_REVISED_R7'
sc['candidate_status']='REVISE; continue modeling. Static silhouette essentially R6; hip deformation improved in separate verification rig. No production KEEP.'
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
assert not bpy.data.actions
assert not any(o.vertex_groups for o in bpy.data.objects if o.type=='MESH')
assert not any(md.type=='ARMATURE' for o in bpy.data.objects for md in o.modifiers)
bpy.ops.wm.save_as_mainfile(filepath=str(STATIC),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(STATIC),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
assert np.array_equal(np.array([v.co[:] for v in b.data.vertices]),r1)
assert all(mesh_signature(bpy.data.objects[n])==sig for n,sig in protected.items())
assert mesh_signature(b,False)==surface
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
report={'blender':bpy.app.version_string,'static_file':STATIC.name,'static_sha256':hashlib.sha256(STATIC.read_bytes()).hexdigest(),
 'static_bytes':STATIC.stat().st_size,'rig_file':str(RIG.relative_to(ROOT)),'rig_sha256':hashlib.sha256(RIG.read_bytes()).hexdigest(),
 'reloaded_static_exact':True,'static_armatures':sum(o.type=='ARMATURE' for o in bpy.data.objects),'static_actions':len(bpy.data.actions),
 'static_vertex_groups':sum(len(o.vertex_groups) for o in bpy.data.objects if o.type=='MESH'),
 'static_armature_modifiers':sum(md.type=='ARMATURE' for o in bpy.data.objects for md in o.modifiers),
 'protected_mesh_objects_exact':len(protected),'body_topology_materials_colors_exact':True,
 'moved_vertices':len(changed),'max_rest_displacement':float(shift.max()),'changed_bounds':[r1[changed].min(axis=0).tolist(),r1[changed].max(axis=0).tolist()],
 'static_normal_comparison':static_normals,'camera_projection_bounds':projection,'preexisting_self_BVH_candidates':collisions,
 'trial_A_decision':'REJECT: two tiny static triangles reverse relative to R6. Kept as isolated evidence only.',
 'trial_B_decision':'Retain as R7 continuation candidate, REVISE for static and deformation; not production KEEP.'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('R7_SAVED_UNRIGGED',STATIC.name,'protected_meshes',len(protected),'normal_min',normal_cosine.min())
print('PREEXISTING_BVH',json.dumps(collisions))
