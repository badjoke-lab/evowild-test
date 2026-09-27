"""Local neck/chest edit from saved v2. No generation or remeshing."""
import bpy, os, json, math
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-blockout-v2.blend'))
source=bpy.data.collections['S_EDITABLE_SOURCE'];source.hide_viewport=False
neck=next(o for o in source.objects if o.name.startswith('Neck_integrated_keel'))
body=next(o for o in bpy.data.collections['S_MODEL'].objects if o.type=='MESH')
original=[v.co.copy() for v in body.data.vertices]
rings=[list(neck.data.vertices[i:i+16]) for i in range(0,len(neck.data.vertices),16)]
centers=[sum((v.co for v in ring),Vector())/len(ring) for ring in rings]
factors=[.85,.85,.93,1.,1.,1.]
shifts=[Vector((0,0,.025)),Vector((0,0,.015)),Vector((0,0,.005)),Vector(),Vector(),Vector()]
# Explicit editable-source operation: lower two cross sections shrink by exactly 15%.
for i,ring in enumerate(rings):
 for v in ring:v.co=centers[i]+(v.co-centers[i])*factors[i]+shifts[i]

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def displacement(p):
 # Compact support excludes skull/crest, limbs, back, pelvis and tail.
 if p.y<=-1.49 or p.y>=-.28 or p.z<=1.83:return Vector()
 best=None
 for i in range(3):
  a,b=centers[i],centers[i+1];d=b-a;t=max(0.,min(1.,(p-a).dot(d)/d.length_squared));c=a+t*d
  dist=(p-c).length_squared
  if best is None or dist<best[0]:best=(dist,i,t,c)
 dist,i,t,c=best
 f=factors[i]*(1-t)+factors[i+1]*t
 shift=shifts[i]*(1-t)+shifts[i+1]*t
 w=(1-smooth(.33,.53,math.sqrt(dist)))*smooth(1.83,2.04,p.z)*(1-smooth(-.68,-.28,p.y))*smooth(-1.49,-1.39,p.y)
 return ((p-c)*(f-1)+shift)*w
# Transfer the edited section field onto saved continuous sculpt surface.
# Vertex count/order, connectivity and all untouched vertex coordinates stay exact.
for v in body.data.vertices:v.co+=displacement(v.co)
for ob in source.objects:
 if ob.name.startswith('Thorax'):
  for v in ob.data.vertices:v.co+=displacement(v.co)
source.hide_viewport=True;source.hide_render=True
body.name='S_organism_blockout_v3';body.data.update()
changed=[i for i,v in enumerate(body.data.vertices) if (v.co-original[i]).length>1e-8]
head=[i for i,p in enumerate(original) if p.y<-1.50]
assert all((body.data.vertices[i].co-original[i]).length==0 for i in head)
assert len(body.data.vertices)==len(original)
report={'input':'S-blockout-v2.blend','output':'S-blockout-v3.blend','source_object':neck.name,'lower_source_section_scale':[.85,.85],'modified_surface_vertices':len(changed),'total_vertices':len(original),'skull_and_crest_vertices_unchanged':True,'topology_unchanged':True,'changed_bounds':[[min(body.data.vertices[i].co[a] for i in changed) for a in range(3)],[max(body.data.vertices[i].co[a] for i in changed) for a in range(3)]],'scope':'lower neck and chest junction only','accepted':False}
scene=bpy.context.scene;scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-blockout-v3.blend'),compress=True)
json.dump(report,open(os.path.join(OUT,'neck-v3-validation.json'),'w'),indent=2)
state=json.load(open(os.path.join(ROOT,'HANDOFF_STATE.json')))
state.update(stage='S-blockout-v3',current_stage='S-blockout-v3 — saved, review pending',current_model_file='output/S-blockout-v3.blend',next_action='Inspect the four v3 review renders for lower-neck width and chest-junction continuity against reference 01.',resume_inputs=['CHECKPOINT.md','HANDOFF_STATE.json','output/S-blockout-v3.blend'])
json.dump(state,open(os.path.join(ROOT,'HANDOFF_STATE.json'),'w'),ensure_ascii=False,indent=2)
p=os.path.join(ROOT,'CHECKPOINT.md');s=open(p).read().replace('current_stage: S-blockout-v2 — self-reviewed, NOT accepted/final','current_stage: S-blockout-v3 — saved, review pending').replace('current_model_file: output/S-blockout-v2.blend','current_model_file: output/S-blockout-v3.blend')
s=s.replace(next(line for line in s.splitlines() if line.startswith('next_action:')),'next_action: Inspect the four v3 review renders for lower-neck width and chest-junction continuity against reference 01.')
open(p,'w').write(s)
review=os.path.join(OUT,'review/v3');os.makedirs(review,exist_ok=True)
for stem,cam in [('front','CAM_FRONT'),('side','CAM_SIDE'),('front34','CAM_FRONT34'),('rear34','CAM_REAR34')]:
 scene.camera=bpy.data.objects[cam];scene.render.filepath=os.path.join(review,'S_blockout_'+stem+'.png');bpy.ops.render.render(write_still=True)
print('NECK_V3',json.dumps(report))
