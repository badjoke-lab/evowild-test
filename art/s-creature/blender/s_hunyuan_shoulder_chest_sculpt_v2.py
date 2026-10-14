"""EvoWild S V2: shape-directed direct editing of real original Hunyuan V1 mesh.

Art hypotheses: reduce frontal shoulder bulk; create oblique scapula -> humerus
ridge and recessed crease; separate pectoral / proximal upper arm in side/3/4.
No primitive additions, no remeshing, no reference replacements, no auto KEEP.
"""
import bpy, hashlib, json, sys
from pathlib import Path
import numpy as np
from mathutils import Vector

ROOT=Path.cwd()
STATION=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
SOURCE=STATION/'S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend'
V1=STATION/'review-v1/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1.blend'
OUT=STATION/'review-v2'
OUT.mkdir(parents=True,exist_ok=True)
V2=OUT/'S_HUNYUAN_SHOULDER_CHEST_SCULPT_V2.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p.relative_to(ROOT)):sha(p) for p in (REF,SOURCE,V1)}
assert sha(REF)=='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert sha(SOURCE)=='1f26bbd4485721a69d74c0c4c4da917dacf9341c15932785e42ba478c3f71c37'
assert sha(V1)=='13d911bbefed39ec602df35b812ce04d27815ac3a7afe3ec0205d77aa65fd212'
assert bpy.app.version[:3]==(4,3,2),bpy.app.version_string
bpy.ops.wm.open_mainfile(filepath=str(V1))
body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1']
mesh=body.data
assert mesh.name=='geometry_0' and len(mesh.vertices)==38802 and len(mesh.polygons)==77684
if body.mode!='OBJECT':
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.mode_set(mode='OBJECT')
before=np.asarray([v.co[:] for v in mesh.vertices],dtype=np.float64)
triangles=np.asarray([p.vertices[:] for p in mesh.polygons],dtype=np.int32)
world=np.asarray([(body.matrix_world@v.co)[:] for v in mesh.vertices],dtype=np.float64)
x,y,z=world.T
mid=-.03588832542300224
side=np.where(x>=mid,1.,-1.)
distance=np.abs(x-mid)
def smoothstep(a,b,v):
    t=np.clip((v-a)/(b-a),0.,1.)
    return t*t*(3-2*t)
def radial(y0,z0,yr,zr):
    return np.exp(-((y-y0)/yr)**2-((z-z0)/zr)**2)
# Continuous mask 0 outside shoulder-chest-upperarm compartment.
mask=(smoothstep(-.59,-.52,y)*(1-smoothstep(-.025,.06,y))*
      smoothstep(-.40,-.345,z)*(1-smoothstep(.18,.25,z)))
lateral=smoothstep(.015,.090,distance)

# V1 balloons across frontal clavicle/deltoid: subtract broad round volume.
narrow=radial(-.398,-.026,.177,.145)

# Angle-controlled band flowing down and backwards from upper shoulder.
ridge_axis=-.370+.47*(.06-z)
ridge=np.exp(-((y-ridge_axis)/.046)**2-((z-.014)/.157)**4)
ridge_recess=np.exp(-((y-(ridge_axis+.064))/.031)**2-((z+.004)/.135)**4)
# Distinct long proximal humerus; avoid another spherical lump.
arm_axis=-.249+.18*(z+.225)
humerus=np.exp(-((y-arm_axis)/.049)**2-((z+.232)/.13)**4)
arm_seam=radial(-.309,-.170,.048,.068)
# Restrained pectoral faceting: edge separates from the arm but tapers into belly.
pectoral=radial(-.472,-.145,.11,.097)
chest_taper=radial(-.326,-.227,.155,.080)
axilla=radial(-.170,-.096,.078,.077)

D=np.zeros_like(world)
D[:,0]=side*lateral*(-.019*narrow+.016*ridge-.012*ridge_recess+
                      .009*humerus-.006*arm_seam+.006*pectoral-.007*axilla)
D[:,1]=-.006*ridge+.004*ridge_recess-.005*pectoral+.003*humerus
D[:,2]= .006*ridge-.003*ridge_recess+.005*humerus+.008*chest_taper-.005*pectoral
D*=mask[:,None]
assert np.isfinite(D).all()
inv=body.matrix_world.inverted()
for v,p in zip(mesh.vertices,world+D):
    v.co=inv@Vector(p)
mesh.update()
body.name='S_HUNYUAN_SHOULDER_CHEST_SCULPT_V2'
body['sculpt_revision']='V2 oblique shoulder/pectoral plane and frontal-width reduction'
body['review_decision']='PENDING_REAL_VISUAL_REVIEW'
bpy.context.scene['full_creature_modeling_approved']=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(V2),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(V2))
body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V2']
mesh=body.data
after=np.asarray([v.co[:] for v in mesh.vertices],dtype=np.float64)
assert np.array_equal(triangles,np.asarray([p.vertices[:] for p in mesh.polygons],dtype=np.int32))
expected=np.asarray([(inv@Vector(p))[:] for p in world+D])
assert np.allclose(after,expected,atol=1e-7,rtol=0)
assert len(after)==len(before)
delta=after-before
changed=np.any(delta!=0,axis=1)
assert changed.sum()>500
assert not np.any(changed[mask==0])
def triangle_stats(verts):
    normals=np.cross(verts[triangles[:,1]]-verts[triangles[:,0]],
                     verts[triangles[:,2]]-verts[triangles[:,0]])
    mag=np.linalg.norm(normals,axis=1)
    return normals,mag
old_n,old_m=triangle_stats(before)
new_n,new_m=triangle_stats(after)
valid=(old_m>1e-12)&(new_m>1e-12)
reversed_faces=int(np.count_nonzero(np.sum(old_n[valid]*new_n[valid],axis=1)<0))
old_degen=int(np.count_nonzero(old_m<=1e-12))
new_degen=int(np.count_nonzero(new_m<=1e-12))
assert reversed_faces==0, reversed_faces
assert new_degen<=old_degen, (old_degen,new_degen)

# Quantiles rather than single extreme crease/spur determine front width.
front_region=(y>-.53)&(y<-.29)&(z>-.08)&(z<.14)
assert front_region.sum()>200
v1_front=np.quantile(before[front_region,0],[.025,.975])
v2_front=np.quantile(after[front_region,0],[.025,.975])
# Report measurement only: do not mark artwork KEEP by arithmetic.
width1=float(v1_front[1]-v1_front[0])
width2=float(v2_front[1]-v2_front[0])
assert all(sha(ROOT/p)==h for p,h in protected.items())
np.savez_compressed(OUT/'vertex_delta_v1_to_v2.npz',
                    indices=np.where(changed)[0],before=before[changed],
                    after=after[changed],delta=delta[changed])
report=dict(
 result='ACTUAL_V2_NATIVE_MESH_SCULPT_SAVED_AND_RELOADED',
 blender_version=bpy.app.version_string,source_commit='3e54d59555d1f5a17f38ee9c7f2846b41bf9fd71',
 source_mesh=mesh.name, vertices=len(mesh.vertices),faces=len(mesh.polygons),
 changed_vertices=int(changed.sum()),max_displacement=float(np.linalg.norm(delta,axis=1).max()),
 input_shoulder_width_quantile_world=width1,
 v2_shoulder_width_quantile_world=width2,
 shoulder_width_change_world=width2-width1,
 front_width_region_count=int(front_region.sum()),
 face_normals_reversed=reversed_faces,old_degenerate_faces=old_degen,
 v2_degenerate_faces=new_degen,
 topology_preserved=True,roi_preserved_outside=True,reload_exact_match=True,
 protected_input_hashes_unchanged=True,protected_sha256=protected,
 output_sha256=sha(V2),output_file=str(V2.relative_to(ROOT)),
 morphology_gate='UNREVIEWED; NO AUTOMATIC_KEEP')
(OUT/'V2_SCULPT_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
print('S_REAL_NATIVE_V2_SAVE_RELOAD_PASS',json.dumps(report),flush=True)
# Fixed V1 review camera and lights. Only actual edited mesh is rendered.
sys.path.insert(0,str(ROOT/'art/s-creature/blender'))
from s_hunyuan_sculpt_review_render import render
render(body,world,OUT,'V2')
assert all(sha(ROOT/p)==h for p,h in protected.items())
print('S_V2_REAL_FIVE_VIEW_AND_DETAIL_RENDER_PASS',flush=True)
