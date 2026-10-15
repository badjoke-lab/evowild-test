"""Finalize own checkpoints, strip unused rollback buffers, save/reopen exactly."""
import bpy,numpy as np,json,hashlib
pilot=bpy.app.driver_namespace['shoulder_pilot'];body=pilot['body'];OUT=pilot['OUT'];ROOT=pilot['ROOT']
current=body.data
def fingerprint(mesh):
    coords=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',coords)
    loops=np.empty(len(mesh.loops),dtype=np.int32);mesh.loops.foreach_get('vertex_index',loops)
    counts=np.empty(len(mesh.polygons),dtype=np.int32);mesh.polygons.foreach_get('loop_total',counts)
    return hashlib.sha256(coords.tobytes()+loops.tobytes()+counts.tobytes()).hexdigest()
before=fingerprint(current)
validation={}
for label,mesh in [('stage1',pilot['baseline']),('candidate',current)]:
    test=mesh.copy();validation[label+'_validate_changed_copy']=test.validate(verbose=False,clean_customdata=False);bpy.data.meshes.remove(test)
assert not any(validation.values()),validation
# Keep the accepted one-side checkpoint separately from the bilateral model.
body.data=pilot['right_final'];body['review_status']='LOCAL_ONE_SIDE_VISUAL_KEEP'
body['sculpt_revision']='Connected shoulder structural pilot from immutable V5_STAGE1, 2026-10-15'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'S_HUNYUAN_SHOULDER_LAYER_RIGHT_FINAL.blend'),compress=True)
body.data=current;body['review_status']='LOCAL_BILATERAL_SHOULDER_VISUAL_KEEP_GLOBAL_UNAPPROVED'
body['topology_changed']=True
body['source_stage1_sha256']='96b1bbc709f1db0dcd559540e28bd79d3863cfcc73ea2a5d916a020108a91f53'
bpy.context.scene['full_creature_modeling_approved']=False
pilot['view']('FRONT34','16_FINAL')
# Only the final editable mesh is retained in the deliverable. All of these
# other mesh datablocks are internal, objectless rollback buffers in this copy.
removed=[]
for mesh in list(bpy.data.meshes):
    if mesh==current:continue
    if mesh.users==0 or (mesh.use_fake_user and mesh.users==1):
        removed.append(mesh.name);bpy.data.meshes.remove(mesh)
assert fingerprint(current)==before
bpy.ops.file.pack_all()
path=OUT/'S_HUNYUAN_SHOULDER_LAYER_PILOT.blend'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
protected=json.loads((OUT/'PROTECTED_BEFORE.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
bpy.ops.wm.open_mainfile(filepath=str(path))
reloaded=bpy.data.objects['S_SHOULDER_STRUCTURE_PILOT']
after=fingerprint(reloaded.data)
assert before==after
assert bpy.app.version[:3]==(4,3,2)
report={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mesh_fingerprint_before':before,'mesh_fingerprint_after_reload':after,'coordinates_and_face_loops_reload_exact':before==after,'vertices':len(reloaded.data.vertices),'polygons':len(reloaded.data.polygons),'mesh_objects':len([o for o in bpy.context.scene.objects if o.type=='MESH']),'mesh_datablocks':len(bpy.data.meshes),'unused_buffer_datablocks_removed':len(removed),'native_blender_validation_on_copies':validation,'blender_version':bpy.app.version_string,'dirty_after_reload':bpy.data.is_dirty,'protected_hashes_unchanged':True,'packed_images':[i.name for i in bpy.data.images if i.packed_file]}
(OUT/'SAVE_RELOAD_VERIFIED.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
