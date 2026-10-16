"""Rebuild one anatomical lateral patch including the diagnosed V undercut.

Replace the giant PILOT cap/root, rather than replaying A's displacement strips.
Retain an exact connected perimeter, rebuild cross-section-driven chest/arm
surface, and integrate a smaller upper overlap through two rounded return rows.
"""
import bpy,bmesh,json,math,numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from mathutils.bvhtree import BVHTree
s=bpy.app.driver_namespace['shoulder_b'];body=s['body'];out=s['OUT']
assert s['fingerprint'](body.data)==s['fingerprint'](s['baseline'])
assert not s.get('rebuild_applied')
bm=bmesh.new();bm.from_mesh(body.data);bm.normal_update()
tree=BVHTree.FromBMesh(bm)
leaf=[(-.468,-.018),(-.455,.048),(-.410,.098),(-.350,.142),(-.292,.156),(-.251,.125),(-.222,.058),(-.225,-.010),(-.240,-.075),(-.250,-.140),(-.270,-.220),(-.300,-.250),(-.337,-.226),(-.363,-.175),(-.425,-.118),(-.463,-.063)]
# Use a convex cut domain so replacement triangle chords cannot cross into
# retained faces outside the patch at the old concave inferior boundary.
def turn(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
pts=sorted(leaf);lower=[];upper=[]
for p in pts:
 while len(lower)>1 and turn(lower[-2],lower[-1],p)<=0:lower.pop()
 lower.append(p)
for p in reversed(pts):
 while len(upper)>1 and turn(upper[-2],upper[-1],p)<=0:upper.pop()
 upper.append(p)
leaf=lower[:-1]+upper[:-1]
def inside(y,z,poly):
 c=False
 for i,(a,b) in enumerate(poly):
  d,e=poly[(i+1)%len(poly)]
  if (b>z)!=(e>z) and y<(d-a)*(z-b)/(e-b)+a:c=not c
 return c
def smooth(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def original_x(y,z):
 hit,_,_,_=tree.ray_cast(Vector((.6,float(y),float(z))),Vector((-1,0,0)))
 assert hit is not None,(y,z)
 return hit.x
diagnosis=[]
for z in [-.195,-.18,-.165,-.15,-.14,-.13,-.12]:
 hit,n,_,_=tree.ray_cast(Vector((.6,-.335,z)),Vector((-1,0,0)))
 diagnosis.append({'y':-.335,'z':z,'x':hit.x,'normal':list(n)})
(out/'V_UNDERCUT_DIAGNOSIS.json').write_text(json.dumps({'cause':'Continuous, sharply recessed shoulder-root surface with downward-facing inferior return, not an open mesh boundary. No BVH candidate contacts occur in this shoulder ROI; existing candidates are in the tail.','samples':diagnosis,'method':'Exact triangle-plane intersections and BVH exterior ray hits; diagnostic sliced live mesh screenshot retained.'},indent=2))
# Cut a new perimeter around BOTH old shield and inferior undercut.
clipfaces=[f for f in bm.faces if -.50<f.calc_center_median().y<-.19 and -.28<f.calc_center_median().z<.19]
clipgeom=set(clipfaces)
for f in clipfaces:clipgeom.update(f.edges);clipgeom.update(f.verts)
bmesh.ops.bisect_plane(bm,geom=list(clipgeom),dist=1e-7,plane_co=Vector((.025,0,0)),plane_no=Vector((1,0,0)),clear_inner=False,clear_outer=False)
for i,(y,z) in enumerate(leaf):
 yy,zz=leaf[(i+1)%len(leaf)]
 fs=[f for f in bm.faces if all(v.co.x>=.0249999 for v in f.verts) and -.50<f.calc_center_median().y<-.19 and -.28<f.calc_center_median().z<.19]
 geom=set(fs)
 for f in fs:geom.update(f.edges);geom.update(f.verts)
 bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-7,plane_co=Vector((0,y,z)),plane_no=Vector((0,zz-z,y-yy)),clear_inner=False,clear_outer=False)
fs={f for f in bm.faces if all(v.co.x>=.0249999 for v in f.verts) and f.calc_center_median().x>.025 and inside(f.calc_center_median().y,f.calc_center_median().z,leaf)}
seed=min(fs,key=lambda f:(f.calc_center_median()-Vector((.11,-.34,0))).length)
component={seed};stack=[seed]
while stack:
 f=stack.pop()
 for e in f.edges:
  for o in e.link_faces:
   if o in fs and o not in component:component.add(o);stack.append(o)
fs=component
boundary=[e for e in bm.edges if sum(f in fs for f in e.link_faces)==1]
links={}
for e in boundary:
 for v in e.verts:links.setdefault(v,[]).append(e.other_vert(v))
assert all(len(v)==2 for v in links.values()),'Patch boundary is not a closed simple ring'
start=min(links,key=lambda v:tuple(v.co));ring=[start];prev=None;curr=start
while True:
 nxt=next(n for n in links[curr] if n!=prev)
 if nxt==start:break
 ring.append(nxt);prev,curr=curr,nxt
assert len(ring)==len(links),'Multiple boundary loops: reject before changing live mesh'
interior={v for f in fs for v in f.verts}-set(ring)
removed=len(fs)
bmesh.ops.delete(bm,geom=list(fs),context='FACES_ONLY')
bmesh.ops.delete(bm,geom=list(interior),context='VERTS')
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
# Anatomically directed lateral cross sections: the shoulder/chest taper and
# proximal arm lobe are explicit control rows, not a uniform smoothing field.
ys=[-.48,-.44,-.40,-.36,-.32,-.28,-.24,-.20]
zs=[-.26,-.22,-.18,-.14,-.10,-.04,.02,.08,.12,.16,.20]
rows=[
 [.025,.035,.045,.068,.100,.133,.132,.100],
 [.030,.040,.055,.080,.105,.130,.135,.110],
 [.035,.045,.065,.087,.099,.120,.127,.100],
 [.040,.055,.080,.095,.095,.103,.110,.090],
 [.045,.065,.090,.102,.099,.094,.095,.080],
 [.065,.085,.105,.113,.110,.096,.085,.075],
 [.070,.090,.108,.115,.112,.100,.086,.075],
 [.045,.065,.092,.108,.107,.096,.083,.068],
 [.030,.045,.065,.087,.090,.078,.065,.055],
 [.025,.030,.040,.053,.060,.056,.045,.040],
 [.020,.025,.032,.040,.045,.042,.035,.030]]
def interpolate(axis,vals,t):
 for i in range(len(axis)-1):
  if axis[i]<=t<=axis[i+1]:
   q=(t-axis[i])/(axis[i+1]-axis[i]);q=q*q*(3-2*q)
   return vals[i]*(1-q)+vals[i+1]*q
 return vals[0] if t<axis[0] else vals[-1]
def distance(y,z,poly):
 p=Vector((y,z));best=10
 for i,a in enumerate(poly):
  a=Vector(a);b=Vector(poly[(i+1)%len(poly)]);d=b-a
  q=a+d*max(0,min(1,(p-a).dot(d)/d.length_squared));best=min(best,(p-q).length)
 return best
def base_x(y,z):
 values=[interpolate(ys,row,y) for row in rows]
 return interpolate(zs,values,z)
def chart(v):
 # The root wraps under the chest: a SIDE orthographic projection folds its
 # boundary over itself. Use an injective perspective chart from inside the
 # torso, verified against exact original boundary segment intersections.
 return Vector(((v.co.y+.30)/v.co.x,(v.co.z+.05)/v.co.x))
def make_uv(u,v):
 lo,hi=.005,.22
 for _ in range(40):
  r=(lo+hi)*.5
  if base_x(-.30+u*r,-.05+v*r)>r:lo=r
  else:hi=r
 r=(lo+hi)*.5
 # Keep the reconstructed point within the actual cut perimeter in 3D;
 # perspective-chart containment alone is insufficient on this wrapped root.
 a,b=0.,.6
 for _ in range(40):
  t=(a+b)*.5
  if inside(-.30+u*t,-.05+v*t,leaf):a=t
  else:b=t
 r=min(r,a*.985)
 return bm.verts.new(Vector((r,-.30+u*r,-.05+v*r)))
newfaces=[]
def make(y,z,x=None):return bm.verts.new(Vector((base_x(y,z) if x is None else x,y,z)))
# Triangulate directly from the injective perspective boundary. A homothetic
# inner ring is unsafe here: the under-chest perimeter is concave in this chart.
# Every retained boundary vertex is used directly in the replacement surface.
inner=ring
# An upper oblique anatomical leaf; the rest of the shoulder is curved chest
# and arm root. This is a smaller integrated layer, not another whole shield.
cap=[(-.412,.040),(-.390,.080),(-.355,.113),(-.310,.140),(-.278,.133),(-.254,.103),(-.252,.080),(-.276,.043),(-.310,.018),(-.342,-.003),(-.369,-.016),(-.389,.001)]
cap=[(-.335+(y+.335)*.78,.060+(z-.060)*.78) for y,z in cap]
inner_polygon=[tuple(chart(v)) for v in inner]
caproot=[make(y,z) for y,z in cap]
cap_polygon=[tuple(chart(v)) for v in caproot]
assert all(inside(*chart(v),inner_polygon) for v in caproot),'Upper leaf must lie within retained inner perimeter'
controls=[]
for z in np.arange(-.22,.141,.025):
 for y in np.arange(-.445,-.224,.025):
  y,z=float(y),float(z)
  probe=Vector(((y+.30)/base_x(y,z),(z+.05)/base_x(y,z)))
  if inside(y,z,leaf) and distance(y,z,leaf)>.015 and inside(*probe,inner_polygon) and distance(*probe,inner_polygon)>.04 and not inside(*probe,cap_polygon) and distance(*probe,cap_polygon)>.04:controls.append(make(y,z))
def triangulate_constrained(verts,loops,extra_edges=()):
 edges=[]
 for loop in loops:edges.extend((loop[i],loop[(i+1)%len(loop)]) for i in range(len(loop)))
 edges.extend(extra_edges)
 r=delaunay_2d_cdt([chart(v) for v in verts],edges,[loops[0]],1,1e-8,True)
 resolved=[]
 for uv,ids in zip(r[0],r[3]):resolved.append(verts[ids[0]] if ids else make_uv(*uv))
 return r,resolved
verts=inner+caproot+controls;n=len(inner);nc=len(caproot)
r,resolved=triangulate_constrained(verts,[list(range(n)),list(range(n,n+nc))])
for ids in r[2]:
 yz=sum((Vector(r[0][i]) for i in ids),Vector((0,0)))/len(ids)
 if not inside(*yz,cap_polygon):newfaces.append(bm.faces.new([resolved[i] for i in ids]))
# Two rounded thickness rows blend the leading edge; rear/inferior returns
# have only .006 local thickness, with zero lift at the anterior root.
c=Vector((-.335,.062));last=caproot
for scale,factor in [(.95,.4),(.82,1.0)]:
 layer=[]
 for y,z in cap:
  yz=c+(Vector((y,z))-c)*scale
  lift=.004*smooth(-.405,-.32,float(yz.x))
  layer.append(make(*yz,base_x(*yz)+lift*factor))
 for i in range(nc):
  j=(i+1)%nc;newfaces.append(bm.faces.new((last[i],last[j],layer[j],layer[i])))
 last=layer
cap_controls=[]
for y,z in [(-.38,.038),(-.36,.064),(-.334,.092),(-.303,.111),(-.284,.088),(-.306,.057),(-.332,.032),(-.358,.018)]:
 y,z=-.335+(y+.335)*.60,.062+(z-.062)*.60
 # Modest crown on a differently oriented upper surface.
 lift=.004*smooth(-.405,-.32,y)
 crown=.004*max(0,1-((y+.33)/.08)**2-((z-.07)/.08)**2)
 point=make(y,z,base_x(y,z)+lift+crown)
 if inside(*chart(point),[tuple(chart(v)) for v in last]):cap_controls.append(point)
 else:bm.verts.remove(point)
verts=last+cap_controls
r,resolved=triangulate_constrained(verts,[list(range(nc))])
for ids in r[2]:newfaces.append(bm.faces.new([resolved[i] for i in ids]))
bmesh.ops.triangulate(bm,faces=newfaces)
loose=[v for v in bm.verts if not v.link_edges]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
# Collapse only numerical near-zero cut edges inside the rebuilt ROI.
tiny_edges=[e for e in bm.edges if e.calc_length()<1e-7 and all(v.co.x>.025 and -.50<v.co.y<-.19 and -.28<v.co.z<.19 for v in e.verts)]
if tiny_edges:bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=tiny_edges)
flat=[f for f in bm.faces if f.calc_area()<1e-12 and all(v.co.x>.025 and -.50<v.co.y<-.19 and -.28<v.co.z<.19 for v in f.verts)]
if flat:bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list({e for f in flat for e in f.edges}))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
candidate=bpy.data.meshes.new('REVISION_B_COMPOUND_SHOULDER_ROOT')
bm.to_mesh(candidate);bm.free();candidate.update()
g,contacts=s['geometry'](candidate);a=s['baseline_geometry']
newcontacts=contacts-s['baseline_contacts']
good=(g['nonmanifold_edges']==0 and g['inconsistent_winding_edges']==0 and g['connected_components']==a['connected_components'] and g['degenerate_triangles_area_lt_1e_minus_12']==a['degenerate_triangles_area_lt_1e_minus_12'] and not newcontacts)
report={'method':'Connected anatomical patch replacement including diagnosed root undercut; cross-section control mesh, smaller upper overlap with rounded returns; no A supports replayed','old_faces_removed':removed,'boundary_vertices_retained':len(ring),'base_control_vertices':len(controls),'new_upper_leaf_yz':cap,'geometry':g,'new_bvh_candidates':len(newcontacts),'applied':good}
(out/'02_REBUILD_REPORT.json').write_text(json.dumps(report,indent=2))
if not good:
 from collections import Counter
 counts=Counter()
 for p in candidate.polygons:
  ids=list(p.vertices)
  for i,j in zip(ids,ids[1:]+ids[:1]):counts[tuple(sorted((i,j)))]+=1
 bad=[{'uses':counts[tuple(sorted(e.vertices))],'points':[list(candidate.vertices[i].co) for i in e.vertices]} for e in candidate.edges if counts[tuple(sorted(e.vertices))]!=2]
 (out/'02_NONMANIFOLD_DIAGNOSTIC.json').write_text(json.dumps(bad,indent=2))
 bpy.data.meshes.remove(candidate)
 raise RuntimeError('B rebuild rejected in preflight; live PILOT copy remains unchanged')
old=body.data;body.data=candidate
if old.users==0:bpy.data.meshes.remove(old)
s['rebuild_applied']=True
print({k:v for k,v in report.items() if k not in ['geometry','new_upper_leaf_yz']})
