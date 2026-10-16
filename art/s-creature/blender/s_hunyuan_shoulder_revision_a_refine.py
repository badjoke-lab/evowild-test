"""Viewport-directed refinement of existing support loops, never rerun cuts."""
import bpy,bmesh,json,math
from mathutils import Vector
s=bpy.app.driver_namespace['shoulder_revision'];b=s['body'];out=s['OUT']
assert s.get('revision_edit_applied') and not s.get('refine_applied')
before=b.data.copy();s['before_refine']=before
bm=bmesh.new();bm.from_mesh(b.data)
leaf=[(-.448,-.025),(-.437,.021),(-.409,.063),(-.363,.102),(-.310,.132),(-.280,.137),(-.256,.112),(-.245,.073),(-.257,.022),(-.280,-.043),(-.305,-.101),(-.326,-.139),(-.345,-.142),(-.391,-.108),(-.428,-.065)]
def smooth(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def inside(y,z):
 c=False
 for i,(a,bb) in enumerate(leaf):
  d,e=leaf[(i+1)%len(leaf)]
  if (bb>z)!=(e>z) and y<(d-a)*(z-bb)/(e-bb)+a:c=not c
 return c
def distance(y,z):
 p=Vector((y,z));best=1
 for i,a in enumerate(leaf):
  a=Vector(a);bb=Vector(leaf[(i+1)%len(leaf)]);d=bb-a
  q=a+d*max(0,min(1,(p-a).dot(d)/d.length_squared));best=min(best,(p-q).length)
 return best
controls=[(-.20,-.004),(-.065,-.004),(-.045,.007),(-.025,.003),(.025,-.004),(.045,.008),(.065,.003),(.15,-.004)]
def profile(t):
 for (a,x),(bb,y) in zip(controls,controls[1:]):
  if a<=t<=bb:return x+(y-x)*(t-a)/(bb-a)
 return 0
count=0
for v in bm.verts:
 x,y,z=v.co
 if x<=.025 or not (-.49<y<-.20 and -.24<z<.18):continue
 lateral=smooth(.025,.070,x)
 cap=inside(y,z)
 relief=profile(z-.55*(y+.34))*smooth(0,.025,distance(y,z)) if cap else 0
 envelope=smooth(-.49,-.42,y)*(1-smooth(-.27,-.20,y))*smooth(-.22,-.12,z)*(1-smooth(.12,.18,z))
 # Retain a shallow overlapping turn, remove the two severe artificial bands.
 dx=-.72*relief*lateral
 # Curve the support rows and the inferior return in geometry, not shading.
 arch=.012*max(0,1-((y+.345)/.12)**2)*envelope*lateral
 # Ease the posterior root back toward the adjacent tissue and fill compact V.
 rear=smooth(-.29,-.24,y)*(1-smooth(-.23,-.20,y))*smooth(-.15,-.08,z)*(1-smooth(.09,.16,z))
 fill=smooth(-.225,-.18,z)*(1-smooth(-.115,-.075,z))*smooth(-.415,-.37,y)*(1-smooth(-.29,-.24,y))
 dx+=lateral*(-.004*rear+.005*fill)
 if dx or arch:v.co.x+=dx;v.co.z+=arch;count+=1
bm.normal_update()
candidate=bpy.data.meshes.new('REVISION_A_CURVED_CONNECTED_LOOPS');bm.to_mesh(candidate);bm.free();candidate.update()
a=s['baseline_geometry'];g,contacts=s['geometry'](candidate)
new=contacts-s['baseline_contacts']
good=g['nonmanifold_edges']==0 and g['inconsistent_winding_edges']==0 and g['connected_components']==a['connected_components'] and g['degenerate_triangles_area_lt_1e_minus_12']==a['degenerate_triangles_area_lt_1e_minus_12'] and not new
report={'operation':'refine already cut support rows: reduce crest relief by 72 percent, curved z support arch .012 max, ease posterior root .004, compact V fill .005','vertices_shaped':count,'new_nonadjacent_bvh_contacts':len(new),'geometry':g,'applied':good}
(out/'03_CURVED_LOOP_REFINEMENT.json').write_text(json.dumps(report,indent=2))
if not good:
 bpy.data.meshes.remove(candidate)
 raise RuntimeError('Refinement rejected before applying; previous preview retained')
old=b.data;b.data=candidate
if old.users==0:bpy.data.meshes.remove(old)
s['refine_applied']=True
print({k:v for k,v in report.items() if k!='geometry'})
