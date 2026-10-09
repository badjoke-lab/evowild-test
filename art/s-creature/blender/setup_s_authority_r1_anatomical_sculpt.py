"""Make an editable, reviewable S R1 anatomical sculpt PROJECT from accepted R0.

Source morphology preserved *bit-for-bit*. Candidate duplicate is ready for
targeted hand/sculpt tool work; this script itself does not pretend to sculpt.
Highlights fore and hind anatomical regions on five locked cameras.
"""
import bpy,os,json,hashlib
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"output","review","authority-r1-sculpt-region")
os.makedirs(OUT,exist_ok=True)
BASE=bpy.data.objects["S_B2a_v5_continuous_body"]
MESH=bpy.data.collections["S_REBUILD_GATE_A"]
vertices=[v.co.copy() for v in BASE.data.vertices]
polys=[tuple(face.vertices) for face in BASE.data.polygons]
before=hashlib.sha256(repr([(tuple(v)) for v in vertices]+polys).encode()).hexdigest()

def clamp(v):return max(0,min(1,v))
def smooth(t):
    t=clamp(t);return t*t*(3-2*t)
def axis(v,a,b,c,d):
    if v<=a or v>=d:return 0.
    if b<=v<=c:return 1.
    if v<b:return smooth((v-a)/(b-a))
    return smooth((d-v)/(d-c))
def w(p,kind):
    ax=abs(p.x)
    if kind=="fore":wy=axis(p.y,-.18,-.10,.14,.26)
    else:wy=axis(p.y,.58,.66,.88,.98)
    return min(axis(ax,.06,.085,.20,.235),wy,axis(p.z,.70,.78,1.04,1.12))

fore=[w(p,"fore") for p in vertices]
hind=[w(p,"hind") for p in vertices]
assert 250<=sum(x>0 for x in fore)<=2500
assert 250<=sum(x>0 for x in hind)<=2500

sandbox=bpy.data.collections.new("S_R1_SURFACE_SCULPT_SANDBOX")
bpy.context.scene.collection.children.link(sandbox)
cand=BASE.copy()
cand.data=BASE.data.copy()
cand.name="S_R1_ANATOMICAL_SCULPT_CANDIDATE"
sandbox.objects.link(cand)
cand.matrix_world=BASE.matrix_world.copy()
# Original body stays in its existing approved collection. Candidate alone renders.
BASE.hide_render=True

for name,weights in [("R1_FORE_ROOT_EDITABLE",fore),("R1_HIND_ROOT_EDITABLE",hind)]:
    vg=cand.vertex_groups.new(name=name)
    for i,val in enumerate(weights):
        if val>0:vg.add([i],float(val),"REPLACE")
mask=cand.data.attributes.get(".sculpt_mask")
if mask is None:mask=cand.data.attributes.new(name=".sculpt_mask",type="FLOAT",domain="POINT")
for i,item in enumerate(mask.data):
    item.value=float(1.0-max(fore[i],hind[i]))

def overlay(name,weights,material):
    verts=[];faces=[]
    lookup={}
    for face in cand.data.polygons:
        vs=list(face.vertices)
        if max(weights[i] for i in vs)<=.16:continue
        # Use slight NORMAL offset to avoid flicker; overlays are diagnostic.
        faceidx=[]
        for i in vs:
            if i not in lookup:
                v=cand.data.vertices[i]
                lookup[i]=len(verts)
                verts.append(tuple(v.co+v.normal*.006))
            faceidx.append(lookup[i])
        faces.append(faceidx)
    me=bpy.data.meshes.new(name+"_mesh");me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);sandbox.objects.link(ob)
    ob.matrix_world=cand.matrix_world.copy()
    ob.data.materials.append(material)
    ob.hide_select=True
    return ob,len(faces)
def material(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
fore_ob,nfore=overlay("ROI_SHOULDER_FORE_ROOT_ORANGE",fore,material("EDIT_FORE_ORANGE",(0.95,.28,.09)))
hind_ob,nhind=overlay("ROI_PELVIS_HIND_ROOT_BLUE",hind,material("EDIT_HIND_BLUE",(.1,.62,.95)))

scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.light="STUDIO"
scene.display.shading.show_shadows=True
scene.render.image_settings.file_format="PNG"
views=["side","front","front34","rear34","back"]
for v in views:
    scene.camera=bpy.data.objects["S_REBUILD_CAM_"+v.upper()]
    scene.render.filepath=os.path.join(OUT,"S_R1_SCULPT_regions_"+v+".png")
    bpy.ops.render.render(write_still=True)
# Do not include colored overlays as production geometry; they are movable
# guide collections in the native editable Blender file.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,"output","S-authority-R1-anatomical-sculpt-setup.blend"),compress=True)
assert [tuple(v.co) for v in BASE.data.vertices]==[tuple(v) for v in vertices]
assert [tuple(f.vertices) for f in BASE.data.polygons]==polys
assert [tuple(v.co) for v in cand.data.vertices]==[tuple(v) for v in vertices]
after=hashlib.sha256(repr([(tuple(v)) for v in vertices]+polys).encode()).hexdigest()
assert before==after
facts={
 "source":"output/S-authority-r0-a5-v2.blend",
 "output_native_project":"output/S-authority-R1-anatomical-sculpt-setup.blend",
 "original_body_exactly_unchanged":True,
 "candidate_geometry_initially_identical":True,
 "original_topology_sha256":before,
 "region_fore_nonzero_vertices":sum(t>0 for t in fore),
 "region_hind_nonzero_vertices":sum(t>0 for t in hind),
 "fore_overlay_faces":nfore,"hind_overlay_faces":nhind,
 "body_mask_attribute":".sculpt_mask",
 "fore_group":"R1_FORE_ROOT_EDITABLE","hind_group":"R1_HIND_ROOT_EDITABLE",
 "rendered_views":views,
 "geometry_edit_performed":False,
 "note":"Orange/blue surfaces are diagnostic overlays only. R0 morphology is unchanged, future sculpt not done. This is not a completed creature."
}
with open(os.path.join(OUT,"R1_SCULPT_REGION_SETUP.json"),"w") as f:json.dump(facts,f,indent=2)
print("R1_ANATOMICAL_SCULPT_READY",json.dumps(facts))
