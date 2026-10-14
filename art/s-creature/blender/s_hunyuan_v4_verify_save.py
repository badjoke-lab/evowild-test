"""Validate the live edited mesh, save V4 separately, reopen and check exactness."""
import bpy, numpy as np, hashlib, json, bmesh
from pathlib import Path
ROOT=Path(bpy.data.filepath).resolve().parents[6]
STATION=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
OUT=STATION/'review-v4'
V3=STATION/'review-v3/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend'
V4=OUT/'S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(V3.relative_to(ROOT)):'820f6ade08f626db7d163dade691fd03e6fa54aa75e8d43ae38ef617252623ec',str(REF.relative_to(ROOT)):'93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'}
assert all(sha(ROOT/p)==h for p,h in protected.items())
body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4']
mesh=body.data
before=np.load(OUT/'V3_BASE_COORDS.npy')
after=np.array([v.co[:] for v in mesh.vertices],dtype=np.float64)
faces=np.array([p.vertices[:] for p in mesh.polygons],dtype=np.int32)
assert mesh.name=='geometry_0' and after.shape==(38802,3) and faces.shape==(77684,3)
assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==1
assert np.isfinite(after).all()
def normals(p):
    n=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
    return n,np.linalg.norm(n,axis=1)
n0,a0=normals(before);n1,a1=normals(after)
valid=(a0>1e-12)&(a1>1e-12)
flipped=int(np.count_nonzero(np.sum(n0[valid]*n1[valid],axis=1)<=0))
newdeg=int(np.count_nonzero((a0>1e-12)&(a1<=1e-12)))
assert flipped==0 and newdeg==0
changed=np.any(after!=before,axis=1)
x,y,z=before.T
roi=(y>-.59)&(y<-.045)&(z>-.40)&(z<.25)
assert not np.any(changed&~roi)
front=(y>-.53)&(y<-.29)&(z>-.08)&(z<.14)
width=lambda arr:float(np.diff(np.quantile(arr[front,0],[.025,.975]))[0])
bm=bmesh.new();bm.from_mesh(mesh)
boundary=sum(e.is_boundary for e in bm.edges)
nonmanifold=sum(not e.is_manifold for e in bm.edges)
bm.free()
np.savez_compressed(OUT/'V3_TO_V4_DELTA.npz',vertices=np.where(changed)[0],before=before[changed],after=after[changed])
np.save(OUT/'FINAL_V4_COORDS.npy',after)
body['review_decision']='REVISE'
body['v4_method']='MCP live Edit Mode: oriented shoulder planes, pectoral/upper-arm planes, local adjacency relaxation, shoulder shear; no Gaussian'
body['v4_source_sha256']=protected[str(V3.relative_to(ROOT))]
bpy.context.scene['full_creature_modeling_approved']=False
for im in bpy.data.images:
    if im.name.startswith('CANONICAL_CROP_') or Path(im.filepath).name=='00_s_type_modeling_image_v1.png':
        im.pack()
# Restore the full-body inspection camera and display the original sheet.
cam=bpy.data.objects['VIEW_FRONT34_SOURCE_MODEL_CHECK']
cam.location=(3.5000338554382324,-3.5005338191986084,-.0354)
cam.data.ortho_scale=2.16
bpy.context.scene.camera=cam
for ob in bpy.data.objects:
    if ob.type=='EMPTY' and ob.name.startswith('CANONICAL_'):ob.hide_set(True)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        space=area.spaces.active
        space.region_3d.view_perspective='CAMERA'
        space.region_3d.view_camera_zoom=12
        space.overlay.show_overlays=False
    if area.type=='IMAGE_EDITOR':
        area.spaces.active.image=bpy.data.images.get('00_s_type_modeling_image_v1.png')
        region=next((r for r in area.regions if r.type=='WINDOW'),None)
        if region:
            with bpy.context.temp_override(area=area,region=region):bpy.ops.image.view_all(fit_view=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(V4),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(V4))
reopened=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4']
reload=np.array([v.co[:] for v in reopened.data.vertices],dtype=np.float64)
reload_faces=np.array([p.vertices[:] for p in reopened.data.polygons],dtype=np.int32)
assert np.array_equal(reload,after) and np.array_equal(reload_faces,faces)
# Compare actual source topology from a read-only library load. Do not open,
# save, rename or change the V3 file on disk.
with bpy.data.libraries.load(str(V3),link=False) as (source,target):
    target.meshes=['geometry_0']
source_mesh=target.meshes[0]
source_coords=np.array([v.co[:] for v in source_mesh.vertices],dtype=np.float64)
source_faces=np.array([p.vertices[:] for p in source_mesh.polygons],dtype=np.int32)
assert np.array_equal(source_coords,before) and np.array_equal(source_faces,faces)
bpy.data.meshes.remove(source_mesh)
assert all(sha(ROOT/p)==h for p,h in protected.items())
logs={}
for p in OUT.glob('*_EDIT_LOG.json'):
    log=json.loads(p.read_text())
    log['retained']=p.name!='refine_EDIT_LOG.json'
    if p.name=='refine_EDIT_LOG.json':log['rejection_reason']='sharp dark posterior shoulder boundary in actual FRONT34 viewport; restored checkpoint'
    if p.name=='shoulder_shear_EDIT_LOG.json':log['method']='feathered polygon tangential shoulder shear'
    p.write_text(json.dumps(log,indent=2)+'\n')
    logs[p.name]=log
report=dict(technical_result='PASS',artistic_decision='REVISE',blender_version=bpy.app.version_string,live_mcp=True,mesh='geometry_0',vertices=len(after),faces=len(faces),mesh_objects=1,changed_from_v3=int(changed.sum()),max_move=float(np.linalg.norm(after-before,axis=1).max()),mean_changed_move=float(np.linalg.norm(after[changed]-before[changed],axis=1).mean()),changed_coordinates_sha256=hashlib.sha256(after.tobytes()).hexdigest(),topology_identical_to_actual_v3=True,save_reload_exact=True,outside_shoulder_chest_upperarm_roi_unchanged=True,newly_reversed_face_normals=flipped,newly_degenerate_faces=newdeg,existing_degenerate_faces=int(np.count_nonzero(a0<=1e-12)),boundary_edges=boundary,nonmanifold_edges=nonmanifold,v3_front_width_quantile=width(before),v4_front_width_quantile=width(after),front_width_change_percent=(width(after)/width(before)-1)*100,minimum_valid_area_ratio=float((a1[valid]/a0[valid]).min()),protected_hashes=protected,output_sha256=sha(V4),stages=logs,render_engine='CYCLES',render_samples=24,self_intersection_test='not exhaustively tested; no claim of watertightness',files=[p.name for p in sorted(OUT.glob('*.png'))])
(OUT/'V4_TECHNICAL_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['stages','files']},indent=2))
