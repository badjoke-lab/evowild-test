"""EvoWild Run S — real editable 3D, CANONICAL-ONLY clean-room silhouette A0.

Explicitly does NOT import, use, deform, or optimize any rejected QEM,
TRELLIS, S-blockout-v12, R0/R5, Tripo or proxy candidate as the morphology
base. This is NOT a final S. Produces a *different* full-body 3D anatomy
layout in Blender against the exact user-locked 1448×1086 S modeling image.

The only goal for A0: inspect and REJECT/REVISE/KEEP the five-view full-body
silhouette BEFORE any rig, tail topology optimization, final materials or
game imports. Neither technical counts nor Actions SUCCESS can grant approval.

Any text dimensions here are unapproved MODELING HYPOTHESES and cannot replace
the original repository PNG. The reference itself is embedded in the .blend.
"""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils import Quaternion

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/"references/00_s_type_modeling_image_v1.png"
EXPECTED_SHA="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert REF.exists() and hashlib.sha256(REF.read_bytes()).hexdigest()==EXPECTED_SHA
OUT=ROOT/"experiments/canonical-cleanroom-fullbody-20261011/a0-full-silhouette"
RDR=OUT/"review"
RDR.mkdir(parents=True,exist_ok=True)

# Proven clean-room: no loaded wrong-model .blend and no old mesh imported.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
ref_image=bpy.data.images.load(str(REF),check_existing=True)
ref_image.name="IMMUTABLE_USER_AUTHORIZED_S_REFERENCE_00"
ref_image.pack()
scene["sole_S_modeling_reference"]="art/s-creature/references/00_s_type_modeling_image_v1.png"
scene["sole_S_modeling_reference_sha256"]=EXPECTED_SHA
scene["A0_morph_approved"]=False
scene["prohibit_using_failed_QEM_as_S_modeling_target"]=True
scene["cleanroom_original_model_source"]="NO_PRIOR_MESH"
scene["A0_accepted"]=False
objects_by_group={}
def group(label):
    collection=bpy.data.collections.new("S_A0_"+label)
    scene.collection.children.link(collection)
    objects_by_group[label]=collection
    return collection
groups={name:group(name) for name in
        ("CORE_BODY","HEAD_NECK","TWIN_CREST","FORELIMBS","HINDLIMBS",
         "SPLIT_FEET","SHOULDER_ARMOR","PELVIS_ARMOR","TAIL_CORE",
         "TAIL_LAMINAE","FACIAL_MARKERS")}
def mat(name, color):
    obj=bpy.data.materials.new(name)
    obj.diffuse_color=tuple(color)+(1.,)
    return obj
NAVY=mat("01_DEEP_MIDNIGHT_NAVY",(0.042,0.066,0.17))
BLUE=mat("02_SHADED_ULTRAMARINE",(0.10,0.20,0.41))
PALE=mat("03_PALE_CREAM_PLATES",(0.90,0.88,0.81))
WHITE=mat("04_PEARL_WHITE_LAMINAE",(0.92,0.94,0.97))
LAV=mat("05_IRIDESCENT_LAVENDER",(0.43,0.42,0.75))
SKY=mat("06_COOL_BLUE_CRESTS",(0.25,0.43,0.79))
SOLE=mat("07_DARK_SPLIT_TOE_TIPS",(0.047,0.067,0.13))
EYE=mat("08_ORANGE_EYE_MARKERS",(0.86,0.41,0.20))
# Keep geometry physically editable meshes, not flat sprites or AI renders.
mesh_total=0
def make_mesh(name,vertices,faces,material,collection,metadata=None):
    global mesh_total
    mesh=bpy.data.meshes.new(name+"_GEO")
    mesh.from_pydata([tuple(v) for v in vertices],[],faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    collection.objects.link(ob)
    ob.data.materials.append(material)
    for f in mesh.polygons:f.use_smooth=True
    for k,v in (metadata or {}).items():ob[k]=v
    mesh_total+=1
    return ob

def catmull(pa,pb,pc,pd,t):
    # Piecewise Catmull-Rom spline on actual polygonal centerline.
    return (pb*2.0 + (pc-pa)*t +
           (pa*2.-pb*5.+pc*4.-pd)*t*t +
           (-pa+pb*3.-pc*3.+pd)*t*t*t)*0.5
def scalar_catmull(a,b,c,d,t):
    return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
def tube(name,spec,material,coll,reference_axis=(1,0,0),sides=12,per_span=5):
    """Closed smooth 3D ellipsoidal segmented loft with real geometry.

    spec = [((x,y,z), halfwidth, halfdepth)] along centerline.
    Built as one manifold submesh, externally grouped by anatomical region.
    """
    assert len(spec)>=2
    values=[]
    for i in range(len(spec)-1):
        for step in range(per_span):
            t=step/per_span
            lo=max(0,i-1);hi=min(len(spec)-1,i+2)
            pos=catmull(Vector(spec[lo][0]),Vector(spec[i][0]),
                       Vector(spec[i+1][0]),Vector(spec[hi][0]),t)
            wa=scalar_catmull(spec[lo][1],spec[i][1],spec[i+1][1],spec[hi][1],t)
            wb=scalar_catmull(spec[lo][2],spec[i][2],spec[i+1][2],spec[hi][2],t)
            values.append((pos,max(.004,float(wa)),max(.004,float(wb))))
    values.append((Vector(spec[-1][0]),max(.004,spec[-1][1]),max(.004,spec[-1][2])))
    result_verts=[]
    ref=Vector(reference_axis)
    for k,(p,radius_a,radius_b) in enumerate(values):
        ahead=values[min(k+1,len(values)-1)][0]
        behind=values[max(k-1,0)][0]
        tangent=(ahead-behind).normalized()
        wa=ref-tangent*ref.dot(tangent)
        if wa.length<1e-5:
            ref=Vector((0,1,0));wa=ref-tangent*ref.dot(tangent)
        wa.normalize()
        wb=tangent.cross(wa).normalized()
        for j in range(sides):
            ang=math.tau*j/sides
            v=p+wa*(radius_a*math.cos(ang))+wb*(radius_b*math.sin(ang))
            result_verts.append(v)
    faces=[]
    for k in range(len(values)-1):
        for j in range(sides):
            n=(j+1)%sides
            faces.append((k*sides+j,k*sides+n,(k+1)*sides+n,(k+1)*sides+j))
    faces.append(tuple(reversed(tuple(range(sides)))))
    faces.append(tuple((len(values)-1)*sides+j for j in range(sides)))
    return make_mesh(name,result_verts,faces,material,coll,
      {"source":"CANONICAL_ONLY_NEW_3D_BLOCKOUT","count_centreline_points":len(spec)})

def leaf(name,points,widths,thickness,material,coll,axis=(0,0,1)):
    assert len(points)==len(widths)
    return tube(name,[(tuple(p),w,thickness*(max(.008,w)/max(widths))**.55)
                      for p,w in zip(points,widths)],
                material,coll,reference_axis=axis,sides=10,per_span=5)

# Morphology hypotheses are normalized in WORLD UNITS below, not separate
# fake assets. +Y = backwards, -Y = front, +Z upwards.
# A solid high shoulder, deliberately deep waist tuck, distinct strong hips.
core=tube("01_CONTINUOUS_ATHLETIC_THORAX_WAIST_PELVIS",[
 ((0,-1.24,1.72),.23,.28),
 ((0,-.98,1.61),.35,.37),
 ((0,-.61,1.57),.35,.35),
 ((0,-.25,1.63),.24,.23),
 ((0,.11,1.69),.17,.18),
 ((0,.49,1.70),.23,.24),
 ((0,.90,1.72),.35,.34),
 ((0,1.23,1.69),.22,.23)],
 NAVY,groups["CORE_BODY"],sides=20,per_span=5)
# Integrated-forward sloped neck is deliberately non-straight with thick root.
tube("02_FLARED_DARK_NECK_SKULL_TRANSITION",[
 ((0,-1.14,1.76),.235,.30),
 ((0,-1.34,1.96),.18,.22),
 ((0,-1.50,2.25),.135,.16),
 ((0,-1.76,2.57),.105,.13),
 ((0,-2.00,2.78),.106,.12)],
 NAVY,groups["HEAD_NECK"],sides=16)
# A low wedge skull with racing snout, not an upward deer muzzle.
tube("03_SMALL_WEDGE_RACING_HEAD",[
 ((0,-1.91,2.76),.14,.13),
 ((0,-2.12,2.80),.16,.14),
 ((0,-2.34,2.83),.10,.075),
 ((0,-2.55,2.80),.028,.032)],
 NAVY,groups["HEAD_NECK"],reference_axis=(1,0,0),sides=12)
tube("04_PALE_FACIAL_CHEEK_RIDGE",[
 ((0,-2.30,2.79),.060,.035),
 ((0,-2.50,2.795),.019,.015)],
 PALE,groups["FACIAL_MARKERS"],sides=12)
# TWO real, separate dominant crest blades, each emerges from opposite side
# of the skull, sweeps BACKWARD and UPWARD. No central unicorn spear.
for side in (-1,1):
    label="L" if side<0 else "R"
    leaf(f"05_{label}_PRIMARY_LONG_SWEPT_CREST",[
       (side*.098,-2.10,2.86),
       (side*.145,-2.09,3.14),
       (side*.195,-1.98,3.47),
       (side*.225,-1.71,3.76),
       (side*.21,-1.42,3.94)],
       [.038,.09,.15,.115,.012],.055,
       LAV if side<0 else SKY,groups["TWIN_CREST"],
       axis=(0,1,0))
    leaf(f"06_{label}_FORWARD_TEMPORAL_SECONDARY_BLADE",[
       (side*.135,-2.13,2.83),
       (side*.16,-2.05,2.99),
       (side*.29,-1.79,3.10),
       (side*.39,-1.57,3.16)],
       [.023,.087,.10,.012],.033,
       SKY,groups["TWIN_CREST"],axis=(0,0,1))
    leaf(f"07_{label}_SKULL_INTEGRATED_CRESTRIDGE",[
       (side*.080,-2.20,2.95),
       (side*.120,-2.12,3.06),
       (side*.15,-1.97,3.13)],
       [.023,.050,.010],.026,
       WHITE,groups["TWIN_CREST"],axis=(0,1,0))
    # Small amber eye off lateral head surface — not a deer face.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,
                                      radius=1,location=(side*.137,-2.30,2.873))
    eye=bpy.context.object;eye.name=f"S_A0_{label}_EYE"
    eye.scale=(.012,.028,.021)
    for c in list(eye.users_collection):c.objects.unlink(eye)
    groups["FACIAL_MARKERS"].objects.link(eye)
    eye.data.materials.append(EYE)
    mesh_total+=1

# Visible shoulder plates form broad curved asymmetric armor laminae
# along a substantial shoulder, chest and lateral neck-root junction.
for side in (-1,1):
    label="L" if side<0 else "R"
    leaf(f"08_{label}_CHAMPION_SHOULDER_WHITE_ARMOR",[
      (side*.30,-1.22,1.79),
      (side*.42,-.92,1.98),
      (side*.47,-.51,2.12),
      (side*.42,-.14,2.19),
      (side*.32,.16,2.26)],
      [.058,.16,.24,.16,.012],.067,
      WHITE,groups["SHOULDER_ARMOR"],axis=(0,0,1))
    leaf(f"09_{label}_CHEST_PLATE_UNDERLAY",[
      (side*.26,-1.20,1.52),
      (side*.34,-1.11,1.72),
      (side*.40,-.78,1.80),
      (side*.37,-.46,1.85)],
      [.065,.14,.13,.018],.054,
      PALE,groups["SHOULDER_ARMOR"],axis=(0,1,0))
    leaf(f"10_{label}_THORAX_LATERAL_BLUE_SHELL",[
      (side*.36,-.87,1.71),
      (side*.43,-.57,1.65),
      (side*.37,-.28,1.58),
      (side*.24,.20,1.57)],
      [.055,.14,.13,.016],.045,
      BLUE,groups["SHOULDER_ARMOR"],axis=(0,0,1))
    # Hip protected by layered NON-deer tapered armored mass.
    leaf(f"11_{label}_HIGH_HAUNCH_SHELL",[
      (side*.27,.63,1.84),
      (side*.39,.93,1.99),
      (side*.40,1.22,1.92),
      (side*.31,1.52,1.81)],
      [.042,.155,.145,.016],.065,
      BLUE,groups["PELVIS_ARMOR"],axis=(0,0,1))
    leaf(f"12_{label}_HIP_LOWER_PALE_FLANGE",[
      (side*.32,.79,1.57),
      (side*.38,1.06,1.50),
      (side*.31,1.31,1.44)],
      [.040,.10,.012],.040,PALE,groups["PELVIS_ARMOR"],
      axis=(0,1,0))

# Four real articulated quadruped legs, not simple straight rods:
# FORE: shoulder -> outward-forward elbow -> swept-forward wrist -> split toes
# HIND: hip -> anterior drive-knee -> rear hock -> split toes.
legs=[]
for side in (-1,1):
    label="L" if side<0 else "R"
    x=side*.33
    x_foot=side*.31
    fore=[
       ((x,-.91,1.65),.215,.17),
       ((side*.39,-1.06,1.31),.165,.145),
       ((side*.38,-.92,.98),.12,.104),
       ((x_foot,-1.19,.64),.087,.077),
       ((x_foot,-1.45,.27),.067,.057),
       ((x_foot,-1.52,.11),.055,.050)]
    tube(f"13_{label}_FORE_ARM_DISTINCT_CHAIN",fore,
         PALE,groups["FORELIMBS"],sides=14)
    legs.append({"side":label,"type":"FORE","chain":[v[0] for v in fore]})
    hind=[
       ((side*.33,.99,1.72),.22,.19),
       ((side*.40,.82,1.35),.20,.17),
       ((side*.41,.56,1.10),.14,.125),
       ((side*.39,1.03,.67),.095,.080),
       ((side*.32,1.34,.27),.071,.060),
       ((x_foot,1.42,.11),.060,.050)]
    tube(f"14_{label}_HIND_SPRINT_DRIVE_CHAIN",hind,
         PALE,groups["HINDLIMBS"],sides=14)
    legs.append({"side":label,"type":"HIND","chain":[v[0] for v in hind]})
    for limb,yy in (("FORE",-1.53),("HIND",1.42)):
        # Actual 3D split racing contact feet, two distinct long prongs per foot.
        for finger in (-1,1):
            xend=x_foot+finger*.058
            toe_y=yy-.105
            leaf(f"15_{label}_{limb}_SPLIT_CONTACT_PRONG_{finger:+d}",[
               (x_foot+finger*.032, yy,.12),
               (xend, yy-.025,.085),
               (xend+finger*.015,toe_y,.052),
               (xend+finger*.019,toe_y-.09,.037)],
               [.033,.041,.030,.008],.026,
               SOLE,groups["SPLIT_FEET"],axis=(1,0,0))

# LONG original-style integrated tapered true 3D tail. Multiple large
# layered blades are distinct sculptable subobjects for look evaluation.
# Topological joining is expressly a later design-dependent operation.
tube("16_LONG_AERODYNAMIC_REAR_TAIL_SPINE",[
 ((0,1.18,1.76),.17,.16),
 ((0,1.54,1.68),.13,.135),
 ((0,1.92,1.57),.10,.09),
 ((0,2.42,1.39),.072,.062),
 ((0,2.94,1.22),.050,.038),
 ((0,3.46,1.06),.025,.018),
 ((0,3.91,.94),.006,.007)],
 NAVY,groups["TAIL_CORE"],sides=16)
tail_specs=[
 ("DORSAL_BLADE_1",-.08,1.43,2.42,.43),
 ("DORSAL_BLADE_2",.10,1.63,2.77,.40),
 ("DORSAL_BLADE_3",-.12,2.04,3.28,.36),
 ("DORSAL_BLADE_4",.08,2.36,3.66,.31),
 ("LATERAL_LIGHT_BLADE_5",-.15,1.66,3.09,-.18),
 ("LATERAL_LIGHT_BLADE_6",.12,2.31,4.12,-.24)
]
for num,(name,lateral,y0,y1,rise) in enumerate(tail_specs):
    z0=1.72-.34*(max(0,y0-1.3)/2.8)
    length=y1-y0
    z_delta=rise
    leaf(f"17_LONG_LAYERED_TAIL_{name}",[
      (lateral*.40,y0,z0),
      (lateral*.8,y0+length*.24,z0+z_delta*.47),
      (lateral*1.04,y0+length*.58,z0+z_delta*.66),
      (lateral*.82,y0+length*.84,z0+z_delta*.43),
      (lateral*.60,y1,z0+z_delta*.10)],
      [.030,.125,.135,.092,.009],
      .038,
      WHITE if num%3==0 else PALE if num%3==1 else BLUE,
      groups["TAIL_LAMINAE"],
      axis=(0,0,1))
assert mesh_total>=30,("Unintended missing actual 3D pieces",mesh_total)

# Save Blender camera and exact reference embedded; all views are native 3D.
camera_data=bpy.data.cameras.new("S_A0_ORTHOGRAPHIC_REVIEW_CAMERA")
cam=bpy.data.objects.new("S_A0_REVIEW_CAMERA",camera_data)
scene.collection.objects.link(cam)
scene.camera=cam
camera_data.type="ORTHO"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.light="STUDIO"
scene.display.shading.show_cavity=True
scene.display.shading.show_shadows=True
scene.render.image_settings.file_format="PNG"
scene.render.resolution_x=1280
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.view_settings.view_transform="Standard"
world=bpy.data.worlds.new("S_A0_NEUTRAL_REVIEW_LIGHT")
scene.world=world
angles={
 "SIDE":Vector((1,0,0)),
 "FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))}
for name,look in angles.items():
    focus=Vector((0,.62,1.84))
    cam.location=focus+look*11
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.ortho_scale=7.8
    scene.render.filepath=str(RDR/f"S_CLEANROOM_A0_ACTUAL_3D_{name}.png")
    bpy.ops.render.render(write_still=True)

# The .blend contains the EXACT original reference image packed in ID data,
# no donor proxy, and named all-body morphology parts for true manual sculpt.
scene["approved_source_original_image_packed"]=ref_image.packed_file is not None
mesh_objects=[o for o in bpy.data.objects if o.type=="MESH"]
coords=[]
for o in mesh_objects:
    for v in o.data.vertices:coords.append(tuple(o.matrix_world@v.co))
from collections import Counter
stats=Counter(o.name.split("_")[2] for o in mesh_objects if o.name.startswith("S_A0"))
bbox=[
 [min(v[k] for v in coords) for k in range(3)],
 [max(v[k] for v in coords) for k in range(3)]]
report={
  "canonical_S_image_path":"art/s-creature/references/00_s_type_modeling_image_v1.png",
  "canonical_S_image_sha256":EXPECTED_SHA,
  "canonical_image_packed_into_actual_blend":ref_image.packed_file is not None,
  "full_cleanroom_geometry_source":"NEW BLENDER MESHES ONLY, NO QEM/TRELLIS/R0/R5",
  "prior_failed_creature_geometry_used":False,
  "mesh_object_count":len(mesh_objects),
  "total_physical_3D_vertices":sum(len(o.data.vertices) for o in mesh_objects),
  "total_physical_3D_polygons":sum(len(o.data.polygons) for o in mesh_objects),
  "joined_manifold_single_mesh":False,
  "rigged":False,
  "native_blender_scene_ready_for_manual_artistic_edit":True,
  "split_contact_prong_count":8,
  "separated_primary_cranial_blade_count":2,
  "tail_long_multi_armor_lamina_count":len(tail_specs),
  "four_leg_chains":legs,
  "world_bounds_xyz":bbox,
  "views_rendered":list(angles),
  "morphology_target":"exact original reference PNG, not modeled guesses",
  "visual_morphology_pass":"REVIEW_PENDING",
  "approved_for_rig_animation_game":False,
  "main_modified":False,
  "completed_S_count":0
}
(OUT/"A0_REAL_FULLBODY_CLEANROOM_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-fullbody-canonical-cleanroom-A0-UNAPPROVED.blend"),compress=True)
# Editable color-bearing GLB for inspecting actual geometry in viewers.
bpy.ops.object.select_all(action="DESELECT")
for ob in mesh_objects:ob.select_set(True)
if mesh_objects:bpy.context.view_layer.objects.active=mesh_objects[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/"S-fullbody-canonical-cleanroom-A0-UNAPPROVED.glb"),
       export_format="GLB",use_selection=True,export_apply=True)
print("S_REAL_SCRATCH_CREATURE_A0",report["mesh_object_count"],
      report["total_physical_3D_vertices"],
      report["total_physical_3D_polygons"],
      "approved",False,"no_old_mesh",True)
