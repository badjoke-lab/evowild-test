"""Live MCP Edit Mode surface planes; no Gaussian fields or added mesh parts.

Run in the existing V4 GUI scene with STAGE = shoulder / chest_arm / refine.
Each proposal is constrained to a feathered polygon on the existing surface.
Topology stays fixed. A global line search rejects face inversion/collapse.
"""
import bpy, bmesh, numpy as np, json
from pathlib import Path

ROOT = Path(bpy.data.filepath).resolve().parents[6]
OUT = ROOT / 'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/review-v4'
body = bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4']
assert Path(bpy.data.filepath).parent == OUT
if body.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = body
body.hide_set(False)
body.select_set(True)
mesh = body.data
before = np.array([v.co[:] for v in mesh.vertices], dtype=np.float64)
faces = np.array([p.vertices[:] for p in mesh.polygons], dtype=np.int32)
assert before.shape == (38802, 3) and faces.shape == (77684, 3)
x, y, z = before.T
mid = -.03588832542300224
side = np.where(x >= mid, 1., -1.)
d = np.abs(x-mid)

def ease(a, b, t):
    t = np.clip((t-a)/(b-a), 0, 1)
    return t*t*(3-2*t)

def polygon(points, feather=.035):
    """Convex yz polygon; smooth feather entirely inside the support."""
    p = np.array(points, dtype=float)
    area = np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
    sign = np.sign(area)
    dist = np.full(len(before), np.inf)
    for a,b in zip(p, np.roll(p,-1,axis=0)):
        edge = b-a
        dist = np.minimum(dist, sign*(edge[0]*(z-a[1])-edge[1]*(y-a[0]))/np.linalg.norm(edge))
    return ease(0, feather, dist)

delta = np.zeros_like(before)
if STAGE == 'shoulder':
    # Main sloping lateral shoulder sheet. Project side surface toward an
    # oblique plane, preserving the upper crest and arm below the plate.
    w = polygon([(-.49,-.075),(-.435,-.18),(-.30,-.165),(-.185,.07),(-.345,.145),(-.465,.085)], .035)
    w *= ease(.05,.105,d)
    target = .163 + .15*(y+.35) + .13*(z+.02)
    delta[:,0] = side * (target-d) * w * .88
elif STAGE == 'chest_arm':
    # Lower pectoral plane turns inward into the thoracic underside, rather
    # than cutting a groove beside the shoulder. Move on existing surface.
    w = polygon([(-.53,-.09),(-.48,-.27),(-.34,-.29),(-.275,-.15),(-.39,-.085)], .045)
    w *= ease(.015,.09,d)
    target = .123 + .14*(z+.18) + .10*(y+.41)
    delta[:,0] += side * (target-d) * w * .48
    delta[:,1] += .012*w
    # Broad oriented upper-arm face, with a continuous tapered transition.
    arm = polygon([(-.335,-.15),(-.345,-.30),(-.24,-.365),(-.185,-.245),(-.23,-.13)],.03)
    arm *= ease(.07,.115,d)
    target_arm = .158 + .13*(z+.24) - .10*(y+.265)
    delta[:,0] += side*(target_arm-d)*arm*.50
    delta[:,1] += .009*arm
elif STAGE == 'shoulder_shear':
    # Canonical shoulder runs from the rear-upper sheet to the forward-lower
    # deltoid. Shear the existing face patch along y rather than inflate it.
    w = polygon([(-.50,-.075),(-.445,-.20),(-.28,-.18),(-.175,.07),(-.34,.15),(-.47,.085)],.055)
    w *= ease(.04,.10,d)
    delta[:,1] = np.clip(.23*(z+.04)+.008,-.028,.028)*w
elif STAGE == 'upper_overlap':
    # A shallow diagonal upper sheet over the primary shoulder plane. Broad
    # feather and bounded motion avoid the rejected deep posterior crease.
    w = polygon([(-.46,.025),(-.38,-.065),(-.25,-.035),(-.18,.07),(-.32,.145),(-.425,.105)],.04)
    w *= ease(.055,.115,d)
    target = .185 + .10*(y+.34) + .22*(z-.04)
    delta[:,0] = side*np.clip((target-d)*.50,-.014,.014)*w
elif STAGE == 'refine':
    # Posterior shoulder sheet gets its own oblique facet, overlapping the
    # primary plane through a wide continuous feather, never a narrow slit.
    w = polygon([(-.35,.035),(-.285,-.075),(-.115,-.015),(-.07,.095),(-.22,.145)],.035)
    w *= ease(.065,.12,d)
    target = .147 + .20*(y+.23) + .11*(z-.035)
    delta[:,0] = side*(target-d)*w*.65
else:
    raise ValueError(STAGE)

def norms(p):
    n = np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
    return n, np.linalg.norm(n,axis=1)

n0,a0 = norms(before)
base = np.load(OUT/'V3_BASE_COORDS.npy')
nb,ab = norms(base)
factor = 1.
for attempt in range(16):
    proposal = (before+factor*delta).astype(np.float32).astype(np.float64)
    n,a = norms(proposal)
    valid = (a0>1e-12)&(ab>1e-12)
    bad = (np.sum(n*n0,axis=1)<=0)|(np.sum(n*nb,axis=1)<=0)|(a<a0*.25)|(a<ab*.25)
    if not np.any(bad&valid):
        break
    factor *= .8
else:
    raise RuntimeError('Plane proposal failed face orientation/area gate')
changed = np.any(before!=proposal,axis=1)
assert np.count_nonzero(changed)>50, 'No meaningful edit'
assert factor>=.2, 'Stop rather than silently make a negligible edit'
np.save(OUT/(STAGE+'_BEFORE.npy'),before)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(mesh)
bm.verts.ensure_lookup_table()
for v in bm.verts:
    v.select_set(bool(changed[v.index]))
    if changed[v.index]:
        v.co = proposal[v.index]
bmesh.update_edit_mesh(mesh,loop_triangles=True,destructive=False)
bpy.ops.object.mode_set(mode='OBJECT')
mesh.update()
actual = np.array([v.co[:] for v in mesh.vertices],dtype=np.float64)
assert np.array_equal(actual,proposal)
np.save(OUT/(STAGE+'_AFTER.npy'),actual)
method = 'feathered polygon tangential shoulder shear' if STAGE == 'shoulder_shear' else 'feathered polygon surface-to-oblique-plane projection'
report = dict(stage=STAGE,mode='EDIT via bmesh.from_edit_mesh',method=method,gaussian=False,changed_vertices=int(changed.sum()),max_move=float(np.linalg.norm(actual-before,axis=1).max()),factor=factor,new_flipped_faces=0,new_degenerate_faces=0,minimum_valid_face_area_ratio=float((a/a0)[valid].min()),added_mesh_objects=0)
(OUT/(STAGE+'_EDIT_LOG.json')).write_text(json.dumps(report,indent=2)+'\n')
body['v4_method']='Live MCP Edit Mode; polygon-supported oblique surface planes'
body['v4_last_stage']=STAGE
body['review_decision']='PENDING_VISUAL_REVIEW'
print(json.dumps(report,indent=2))
