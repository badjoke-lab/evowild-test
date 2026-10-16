"""One-side connected-panel revision; guard against double execution."""
import bpy,bmesh,numpy as np,json,math
from mathutils import Vector
s=bpy.app.driver_namespace['shoulder_revision'];body=s['body'];out=s['OUT']
assert s['fingerprint'](body.data)==s['fingerprint'](s['baseline'])
assert 'revision_edit_applied' not in s
bm=bmesh.new();bm.from_mesh(body.data);bm.normal_update()
leaf=[(-.448,-.025),(-.437,.021),(-.409,.063),(-.363,.102),(-.310,.132),(-.280,.137),(-.256,.112),(-.245,.073),(-.257,.022),(-.280,-.043),(-.305,-.101),(-.326,-.139),(-.345,-.142),(-.391,-.108),(-.428,-.065)]
def inside(y,z):
 c=False
 for i,(a,b) in enumerate(leaf):
  d,e=leaf[(i+1)%len(leaf)]
  if (b>z)!=(e>z) and y<(d-a)*(z-b)/(e-b)+a:c=not c
 return c
def smooth(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def distance(y,z):
 p=Vector((y,z));best=1
 for i,a in enumerate(leaf):
  a=Vector(a);b=Vector(leaf[(i+1)%len(leaf)]);d=b-a
  q=a+d*max(0,min(1,(p-a).dot(d)/d.length_squared))
  best=min(best,(p-q).length)
 return best
initial=len(bm.verts)
# Deliberate support loops across the existing panel, with paired support lines
# around two oblique crests. No detached plate and no full-surface subdivision.
cutlog=[]
for height in [-.065,-.045,.025,.045,.065]:
 fs=[f for f in bm.faces if f.normal.x>.65 and f.calc_area()>1e-7 and all(v.co.x>.055 for v in f.verts) and inside(f.calc_center_median().y,f.calc_center_median().z)]
 geom=set(fs)
 for f in fs:geom.update(f.edges);geom.update(f.verts)
 result=bmesh.ops.bisect_plane(bm,geom=list(geom),dist=1e-6,plane_co=Vector((0,-.34,height)),plane_no=Vector((0,-.55,1)),clear_inner=False,clear_outer=False)
 cutlog.append({'z_at_y_minus_034':height,'faces_in_cut':len(fs),'cut_elements':len(result['geom_cut'])})
 bm.normal_update()
controls=[(-.20,-.004),(-.065,-.004),(-.045,.007),(-.025,.003),(.025,-.004),(.045,.008),(.065,.003),(.15,-.004)]
def profile(t):
 for (a,x),(b,y) in zip(controls,controls[1:]):
  if a<=t<=b:return x+(y-x)*(t-a)/(b-a)
 return 0
changed=0
for v in bm.verts:
 x,y,z=v.co
 if x<=.025 or not (-.49<y<-.20 and -.24<z<.18):continue
 lateral=smooth(.025,.070,x)
 cap=inside(y,z)
 # Compound directional relief, faded into the original connected perimeter.
 relief=profile(z-.55*(y+.34))*smooth(0,.025,distance(y,z)) if cap else 0
 # Shorten and round the inferior root; fill the old compact V recess rather
 # than attaching another mass. These are local continuous coordinate shears.
 lower=smooth(-.24,-.18,z)*(1-smooth(-.115,-.065,z))*smooth(-.43,-.37,y)*(1-smooth(-.29,-.24,y))
 fill=smooth(-.225,-.18,z)*(1-smooth(-.13,-.09,z))*smooth(-.415,-.365,y)*(1-smooth(-.285,-.235,y))
 upper=smooth(.035,.09,z)*(1-smooth(.14,.18,z))*smooth(-.44,-.37,y)*(1-smooth(-.25,-.20,y))
 dx=lateral*(relief+.011*fill-.004*upper)
 dz=lateral*.010*lower
 dy=lateral*.006*lower
 if dx or dy or dz:
  v.co+=Vector((dx,dy,dz));changed+=1
bm.normal_update()
candidate=bpy.data.meshes.new('REVISION_A_CONNECTED_SUPPORT_LOOPS')
bm.to_mesh(candidate);bm.free();candidate.update()
a=s['baseline_geometry'];b,contacts=s['geometry'](candidate)
newcontacts=contacts-s['baseline_contacts']
report={'operation':'right connected cap: five oblique support cuts, two directional crests, inferior root return and compact V fill','cuts':cutlog,'original_vertices':initial,'candidate_vertices':len(candidate.vertices),'vertices_shaped':changed,'baseline_geometry':a,'candidate_geometry':b,'new_nonadjacent_bvh_contacts':len(newcontacts),'live_applied':False}
good=(b['nonmanifold_edges']==a['nonmanifold_edges'] and b['connected_components']==a['connected_components'] and b['inconsistent_winding_edges']==0 and b['degenerate_triangles_area_lt_1e_minus_12']==a['degenerate_triangles_area_lt_1e_minus_12'] and not newcontacts)
if not good:
 (out/'02_REVISION_PREFLIGHT_REJECTED.json').write_text(json.dumps(report,indent=2))
 bpy.data.meshes.remove(candidate)
 raise RuntimeError('Revision preflight rejected; live mesh remains exact recovered PILOT')
old=body.data;body.data=candidate
if old.users==0:bpy.data.meshes.remove(old)
s['revision_edit_applied']=True
report['live_applied']=True
(out/'02_REVISION_EDIT.json').write_text(json.dumps(report,indent=2))
print({k:v for k,v in report.items() if k not in ['baseline_geometry','candidate_geometry']})
