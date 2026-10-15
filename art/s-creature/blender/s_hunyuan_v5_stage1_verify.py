"""Read-only mesh validation after reopening the accepted Stage 1 file."""
import bpy,bmesh,numpy as np,json,hashlib
from pathlib import Path
out=Path(bpy.data.filepath).resolve().parent
root=out.parents[5]
station=out.parent
assert Path(bpy.data.filepath).name=='S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_STAGE1.blend'
protected={
 station/'review-v3/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend':'820f6ade08f626db7d163dade691fd03e6fa54aa75e8d43ae38ef617252623ec',
 station/'review-v4/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend':'38efa5c29e5ac7b1a6a6afba1256d498763e0f8d3b8e7435d9b38b4b183e879e',
 root/'art/s-creature/references/00_s_type_modeling_image_v1.png':'93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in protected.items():assert sha(p)==h,(str(p),sha(p))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.name=='geometry_0')
mesh=body.data
after=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
faces=np.array([p.vertices[:] for p in mesh.polygons],dtype=np.int32)
assert after.shape==(38802,3) and faces.shape==(77684,3)
assert np.array_equal(after,np.load(out/'STAGE1_EXPECTED_COORDS.npy'))
with bpy.data.libraries.load(str(station/'review-v4/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend'),link=False) as (src,dst):dst.meshes=['geometry_0']
m4=dst.meshes[0]
before=np.array([v.co[:] for v in m4.vertices],dtype=np.float32)
assert np.array_equal(faces,np.array([p.vertices[:] for p in m4.polygons],dtype=np.int32))
bpy.data.meshes.remove(m4)
v3=np.load(out.parent/'review-v4/V3_BASE_COORDS.npy')
def geom(v):
 v=v.astype(np.float64);n=np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]])
 return n,np.linalg.norm(n,axis=1)
n0,a0=geom(before);n1,a1=geom(after);n3,a3=geom(v3)
valid=(a0>1e-12)&(a1>1e-12)
flips=int(np.count_nonzero(np.sum(n0[valid]*n1[valid],axis=1)<=0))
newdeg=int(np.count_nonzero((a0>1e-12)&(a1<=1e-12)))
assert flips==newdeg==0
changed=np.any(after!=before,axis=1)
assert changed.sum()==807
roi=(before[:,1]>-.615)&(before[:,1]<-.025)&(before[:,2]>-.42)&(before[:,2]<.27)
assert not np.any(changed&~roi)
c=before[faces].mean(axis=1)
scope=(c[:,1]>-.59)&(c[:,1]<-.045)&(c[:,2]>-.4)&(c[:,2]<.25)
vr=(a0>1e-12)&(a3>1e-12)
rat0=np.ones(len(faces));rat1=np.ones(len(faces));rat0[vr]=a0[vr]/a3[vr];rat1[vr]=a1[vr]/a3[vr]
bm=bmesh.new();bm.from_mesh(mesh)
boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
front=(before[:,1]>-.53)&(before[:,1]<-.29)&(before[:,2]>-.08)&(before[:,2]<.14)
width=lambda v:float(np.diff(np.quantile(v[front,0],[.025,.975]))[0])
np.savez_compressed(out/'V4_TO_V5_STAGE1_DELTA.npz',indices=np.where(changed)[0],before=before[changed],after=after[changed])
report={'technical_result':'PASS','stage':'STAGE1_TRANSITION_REPAIR_ONLY','artistic_decision':'REVISE','final_v5_created':False,'save_reload_exact':True,'blender_version':bpy.app.version_string,'live_mcp':True,'vertices':len(after),'triangles':len(faces),'changed_from_v4':int(changed.sum()),'max_move':float(np.linalg.norm(after-before,axis=1).max()),'outside_roi_changed':0,'topology_identical_v4':True,'new_reversed_faces_relative_v4':flips,'new_degenerate_faces':newdeg,'minimum_v3_area_ratio_before':float(rat0[vr].min()),'minimum_v3_area_ratio_after':float(rat1[vr].min()),'severe_face_count_before':int(np.count_nonzero(scope&vr&(rat0<.45))),'severe_face_count_after':int(np.count_nonzero(scope&vr&(rat1<.45))),'hotspots':[{'face':i,'before':float(rat0[i]),'after':float(rat1[i])} for i in [65666,65664,12157,12159]],'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'front_width_before':width(before),'front_width_after':width(after),'protected_sha256':{str(p.relative_to(root)):sha(p) for p in protected},'stage1_blend_sha256':sha(Path(bpy.data.filepath)),'working_blend_sha256':sha(out/'S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_WORKING.blend'),'coordinates_sha256':hashlib.sha256(after.tobytes()).hexdigest(),'self_intersections':'not exhaustively tested'}
(out/'STAGE1_807_TECHNICAL_VERIFICATION.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
