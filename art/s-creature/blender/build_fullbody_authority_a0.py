"""EvoWild S / authoritative full-body silhouette A0.

New from-scratch topology. Does not import/modify TRELLIS or Blender v12-R5.
The 00_s_type_modeling_image_v1.png remains the only final morphology authority.
This is an unapproved structural/silhouette prototype, never a game-ready asset.
"""
import bpy, bmesh, math, json
from mathutils import Vector
from pathlib import Path
from math import pi, sin, cos

ROOT=Path(bpy.path.abspath("//")).resolve()
OUT=ROOT/"art/s-creature/experiments/fullbody-authority-a0"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def mat(name,rgb):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1.0)
    return m
GRAPHITE=mat("S_dark_anatomy",(0.21,0.24,0.30))
PLATE=mat("S_light_plate",(0.75,0.79,0.85))
EDGE=mat("S_secondary_dark",(0.33,0.38,0.46))
BLUE=mat("S_blue_inlay",(0.12,0.35,0.60))

built=[]
def add_mesh(name,verts,faces,material,smooth=False):
    me=bpy.data.meshes.new(name+"_geometry")
    me.from_pydata(verts,[],faces)
    me.update()
    ob=bpy.data.objects.new(name,me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(me);bm.free()
    if smooth:
        for p in me.polygons:p.use_smooth=True
    built.append(ob)
    return ob

def longitudinal_loft(name,rings,material,sides=20):
    """Morphological single connected centerline body: (y,z,halfwidth,halfdepth)."""
    vs=[];fs=[]
    for y,z,w,d in rings:
        for j in range(sides):
            a=j*2*pi/sides
            vs.append((w*cos(a),y,z+d*sin(a)))
    fs.append(tuple(range(sides-1,-1,-1)))
    for i in range(len(rings)-1):
        for j in range(sides):
            k=i*sides+j;nx=i*sides+(j+1)%sides
            fs.append((k,nx,nx+sides,k+sides))
    fs.append(tuple((len(rings)-1)*sides+j for j in range(sides)))
    return add_mesh(name,vs,fs,material,True)

body_profile=[
 (-1.39,1.78,.010,.012),(-1.35,1.79,.051,.040),
 (-1.29,1.81,.082,.068),(-1.21,1.82,.105,.086),
 (-1.12,1.83,.106,.117),(-1.05,1.77,.109,.135),
 (-.95,1.66,.116,.144),(-.80,1.54,.132,.170),
 (-.65,1.46,.175,.222),(-.49,1.38,.206,.280),
 (-.33,1.37,.222,.305),(-.15,1.39,.210,.269),
 (.05,1.40,.175,.227),(.22,1.40,.155,.201),
 (.42,1.40,.172,.220),(.61,1.43,.198,.263),
 (.72,1.43,.197,.267),(.81,1.44,.156,.227),
 (.90,1.44,.093,.135),(.97,1.45,.055,.082)]
body=longitudinal_loft("S_A0_CONTINUOUS_SKULL_NECK_THORAX_PELVIS",body_profile,GRAPHITE,24)

def cross_tube(name,stations,material,sides=14):
    """Joint-continuous limb tube; station=(x,y,z, lateral_radius, other_radius)."""
    centers=[Vector((x,y,z)) for x,y,z,_,_ in stations]
    vs=[];fs=[]
    for i,st in enumerate(stations):
        x,y,z,ra,rb=st
        tang=(centers[min(i+1,len(stations)-1)]-centers[max(i-1,0)]).normalized()
        ref=Vector((1.0,0.0,0.0))
        u=ref-tang*ref.dot(tang)
        if u.length<.0001:
            ref=Vector((0,1,0));u=ref-tang*ref.dot(tang)
        u.normalize()
        v=tang.cross(u).normalized()
        for j in range(sides):
            ang=j*2*pi/sides
            p=centers[i]+u*(ra*cos(ang))+v*(rb*sin(ang))
            vs.append(tuple(p))
    fs=[tuple(range(sides-1,-1,-1))]
    for i in range(len(stations)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides
            fs.append((a,b,b+sides,a+sides))
    fs.append(tuple((len(stations)-1)*sides+j for j in range(sides)))
    return add_mesh(name,vs,fs,material,True)

# Deliberately DIFFERENT front and hind kinematic chain; no straight rods.
for s in (-1,1):
    tag="L" if s<0 else "R"
    cross_tube("S_A0_FORELEG_"+tag,[
      (s*.192,-.38,1.48,.130,.127),
      (s*.220,-.41,1.33,.116,.110),
      (s*.223,-.46,1.08,.076,.079),
      (s*.227,-.55,.81,.073,.078),
      (s*.215,-.61,.52,.049,.054),
      (s*.215,-.65,.23,.036,.044),
      (s*.213,-.68,.13,.037,.038)],
      GRAPHITE)
    cross_tube("S_A0_HINDLEG_"+tag,[
      (s*.176,.63,1.45,.165,.159),
      (s*.209,.76,1.25,.153,.159),
      (s*.220,.93,.97,.087,.094),
      (s*.220,.80,.70,.077,.081),
      (s*.219,.68,.50,.052,.059),
      (s*.203,.82,.27,.040,.045),
      (s*.203,.88,.13,.039,.040)],GRAPHITE)
    # Separate narrow racing toes terminate in claws, NOT hooves.
    for toe in (-1,1):
        sideoff=.038*toe
        cross_tube(f"S_A0_FRONT_SPLIT_TOE_{tag}_{toe}",[
          (s*.213+sideoff*.30,-.685,.135,.027,.027),
          (s*.213+sideoff*.65,-.741,.077,.026,.024),
          (s*.213+sideoff,-.831,.055,.017,.019),
          (s*.213+sideoff*1.15,-.887,.044,.004,.007)],EDGE,10)
        cross_tube(f"S_A0_HIND_SPLIT_TOE_{tag}_{toe}",[
          (s*.203+sideoff*.32,.875,.136,.028,.027),
          (s*.203+sideoff*.70,.828,.076,.024,.024),
          (s*.203+sideoff,.758,.056,.017,.017),
          (s*.203+sideoff*1.15,.720,.042,.005,.007)],EDGE,10)

# Aerodynamic tapered tail as a continuous extension from the rump.
cross_tube("S_A0_CORE_TAIL",[
    (0,.88,1.48,.100,.10),(0,1.01,1.47,.087,.085),
    (0,1.16,1.43,.069,.074),(0,1.32,1.34,.044,.055),
    (0,1.49,1.25,.028,.039),(0,1.65,1.13,.007,.015)],GRAPHITE,16)

def swept_leaf(name,points,rx,wide,material):
    """Blade profile broad in YZ, thickness & front-view separation in X."""
    c=[Vector(p) for p in points]
    vs=[];n=12
    for i,p in enumerate(c):
        tang=(c[min(i+1,len(c)-1)]-c[max(0,i-1)])
        yz=Vector((0,tang.y,tang.z)).normalized()
        perp=Vector((0,-yz.z,yz.y))
        for j in range(n):
            a=2*pi*j/n
            v=p+Vector((rx[i]*cos(a),0,0))+perp*(wide[i]*sin(a))
            vs.append(tuple(v))
    fs=[tuple(range(n-1,-1,-1))]
    for i in range(len(c)-1):
        for j in range(n):
            a=i*n+j;b=i*n+(j+1)%n
            fs.append((a,b,b+n,a+n))
    fs.append(tuple((len(c)-1)*n+j for j in range(n)))
    return add_mesh(name,vs,fs,material,True)

for s in (-1,1):
    tag="L" if s<0 else "R"
    # Layered paired backward sweep is integrated at skull-cap root.
    swept_leaf("S_A0_MAIN_CRANIAL_LAMINA_"+tag,[
        (s*.072,-1.145,1.910),(s*.081,-1.103,1.977),
        (s*.090,-1.027,2.082),(s*.100,-.918,2.221),
        (s*.108,-.760,2.367),(s*.116,-.552,2.505),
        (s*.118,-.390,2.583)],
        [.021,.026,.028,.027,.022,.015,.002],
        [.027,.049,.066,.078,.067,.041,.002],PLATE)
    swept_leaf("S_A0_SECONDARY_CRANIAL_LAMINA_"+tag,[
        (s*.077,-1.127,1.909),(s*.087,-1.075,1.966),
        (s*.115,-.968,2.034),(s*.137,-.839,2.100),
        (s*.145,-.738,2.117)],
        [.017,.024,.021,.012,.001],
        [.028,.046,.050,.027,.001],EDGE)

# An armor-patch drapes along muscle, not a detached tube.
def armor_patch(name, ylo,yhi,theta0,theta1, material,lift=.018):
    """Use interpolated body profile sections + radial offset over selected arcs."""
    rings=[r for r in body_profile if ylo<=r[0]<=yhi]
    if len(rings)<2:return
    K=9;verts=[];faces=[]
    for y,z,rx,rz in rings:
        for j in range(K):
            a=theta0+(theta1-theta0)*j/(K-1)
            verts.append(((rx+lift)*cos(a),y,z+(rz+lift)*sin(a)))
    for i in range(len(rings)-1):
        for j in range(K-1):
            k=i*K+j
            faces.append((k,k+1,k+K+1,k+K))
    add_mesh(name,verts,faces,material,True)

# Split mirrored shoulder shell and articulated side/pelvis plates.
armor_patch("S_A0_WHITE_DORSAL_SHELL",-.61,.01,.30,2.84,PLATE)
armor_patch("S_A0_WHITE_RUMP_SHELL",.41,.84,.33,2.81,PLATE)
for side in (-1,1):
    tag="L" if side<0 else "R"
    if side>0:
        shoulder_angles=(-.05,.85); hip_angles=(-.10,.72)
    else:
        shoulder_angles=(2.27,3.22); hip_angles=(2.46,3.24)
    armor_patch("S_A0_SHOULDER_WHITE_"+tag,-.55,-.12,*shoulder_angles,PLATE)
    armor_patch("S_A0_HIP_WHITE_"+tag,.47,.82,*hip_angles,PLATE)

# Shingled tail vanes following a coherent curved tail backbone.
for i in range(4):
    y=.98+i*.14;z=1.49-i*.082
    for s in (-1,1):
        tag="L" if s<0 else "R"
        swept_leaf(f"S_A0_TAIL_LAYER_{i}_{tag}",[
            (s*.037,y,z),
            (s*(.055+i*.008),y+.13,z-.05),
            (s*(.079+i*.01),y+.29,z-.13),
            (s*(.083+i*.01),y+.39,z-.19)],
           [.013,.016,.010,.001],
           [.023,.046,.040,.001],EDGE)

# Prevent provisional details from hiding faults: workbench shape review.
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.render.resolution_x=850
scene.render.resolution_y=850
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.render.image_settings.file_format='PNG'
scene.world.color=(.052,.061,.077)

pts=[ob.matrix_world@v.co for ob in built for v in ob.data.vertices]
minimum=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
maximum=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
center=(minimum+maximum)*.5
ext=maximum-minimum

cam=bpy.data.cameras.new("ORTHO_FIVE_VIEW_A0")
obj=bpy.data.objects.new("ORTHO_FIVE_VIEW_A0",cam)
scene.collection.objects.link(obj);scene.camera=obj
cam.type='ORTHO'
dirs={"side":Vector((1,0,0)),
      "front":Vector((0,-1,0)),
      "front34":Vector((1,-1,0)).normalized(),
      "rear34":Vector((1,1,0)).normalized(),
      "back":Vector((0,1,0))}
for name,d in dirs.items():
    obj.location=center+d*6
    obj.rotation_euler=((center-obj.location).to_track_quat('-Z','Y')).to_euler()
    side=Vector((-d.y,d.x,0)).normalized()
    proj=[p.dot(side) for p in pts]
    cam.ortho_scale=max(max(proj)-min(proj),ext.z)*1.17
    scene.render.filepath=str(REV/("S_fullbody_A0_"+name+".png"))
    bpy.ops.render.render(write_still=True)

# Save actual geometry, not a mocked rendered drawing.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-fullbody-authority-A0.blend"))
bpy.ops.object.select_all(action='DESELECT')
for o in built:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(OUT/"S-fullbody-authority-A0.glb"),
                          export_format='GLB',use_selection=True,export_apply=True,export_yup=True)

report={
 "model":"S-fullbody-authority-A0.glb","native_blend":"S-fullbody-authority-A0.blend",
 "authoritative_image_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
 "technique":"Entirely new parametric whole-body silhouette cage, not a TRELLIS-derived edit",
 "base_3d_imported":False, "whole_body_created":True,
 "main_body_connectivity":"single centerline loft from muzzle to pelvis",
 "part_count":len(built),"names":[o.name for o in built],
 "notes":"Armor, limbs and cranial lamina are separate intersecting objects. No combined watertight skin mesh.",
 "morphology_review":"PENDING_REAL_RENDER_REVIEW",
 "accepted_for_rig":False,"accepted_for_game":False,
 "views":list(dirs.keys()),"bounding_box":[list(minimum),list(maximum)]
}
(OUT/"A0_GEOMETRY_FACTS.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"parts":len(built),"bounds":report["bounding_box"],"status":"REVIEW_PENDING"}))
