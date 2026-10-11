"""H0: local shape-key sculpt + hand-authored, surface-fitted armor panels.
Opens the exact original blend. Never generates/replaces the full body.
"""
import bpy, math, json, hashlib, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'art/s-creature/references/00_s_type_modeling_image_v1.png').is_file())
EXP=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011'
SRC=EXP/'hunyuan2mv-original-source-20261012/HUNYUAN2MV_S_THREEVIEW_REAL_ASSET_UNAPPROVED.blend'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
OUT=EXP/'h0-body-armor-pass1'
REVIEW=OUT/'review'
OUT.mkdir(exist_ok=True);REVIEW.mkdir(exist_ok=True)
assert hashlib.sha256(REF.read_bytes()).hexdigest()=='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='6651109695536db026d9b52fe10c3fa829cab82915cda1955a5f56eedcec4345'
assert REF.stat().st_size==1982782
bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene=bpy.context.scene
body=next(o for o in scene.objects if o.type=='MESH')
body.name='S_H0_Original_Hunyuan_Body'
basis=body.shape_key_add(name='Basis_Original_Hunyuan_untouched')
sculpt=body.shape_key_add(name='H0_Shoulder_Chest_Haunch_volume')
source=np.array([list(body.matrix_world@v.co) for v in body.data.vertices])
# Compact support prevents leaking edits onto skull, distal limbs, or tail.
def compact(t):
 t=max(0.,1.-t*t)
 return t*t

def ellip(y,z,cy,cz,ry,rz):
 return compact(math.sqrt(((y-cy)/ry)**2+((z-cz)/rz)**2))

def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)

weights=[]
for i,(x,y,z) in enumerate(source):
 # All masks go exactly to zero outside their local elliptical supports.
 shoulder=ellip(y,z,-.355,.018,.255,.215)
 chest=ellip(y,z,-.425,-.025,.180,.155)
 hip=ellip(y,z,.285,.02,.225,.24)
 upper= smooth(-.25,-.12,z)
 # Preserve center seam and original asymmetry; expand the existing volume.
 dx=(x+.0355)*(.16*shoulder+.08*chest+.20*hip)
 dy=-.022*chest + .010*hip
 dz=-.022*chest*(1-smooth(-.09,.09,z))
 dz+=.018*shoulder*smooth(.03,.14,z)
 dz+=.014*hip*smooth(.06,.16,z)
 # Hard protection to keep tail, head and lower leg coordinates exact.
 allowed=(-.61<y<.495 and z>-.25)
 delta=Vector((dx,dy,dz)) if allowed else Vector((0,0,0))
 sculpt.data[i].co=body.data.vertices[i].co+delta
 weights.append(max(shoulder,chest,hip) if allowed else 0)
sculpt.value=1
vg=body.vertex_groups.new(name='H0_Torso_sculpt_mask')
for i,w in enumerate(weights):
 if w>0: vg.add([i],w,'REPLACE')
body['source_blend']=str(SRC.relative_to(ROOT))
body['H0_method']='Original vertices retained; local editable shape key. Armor is surface-fitted separate geometry.'
body['not_game_approved']=True
coords=[v.co.copy() for v in sculpt.data]
bvh=BVHTree.FromPolygons(coords,[list(p.vertices) for p in body.data.polygons],all_triangles=True)

def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.64
 return m
base=material('Review_only_neutral_slate_same_in_before_and_after',(.22,.26,.32))
white=material('H0_Armor_pearl_white',(.86,.88,.92))
edge=material('H0_Armor_edge_cool_ivory',(.58,.63,.72))
body.data.materials.append(base)
armor=bpy.data.collections.new('H0_White_segmented_armor');scene.collection.children.link(armor)
# Individually drawn panel borders in anatomical Y/Z coordinates. Not ellipsoid proxies.
# Ordered perimeter, central ridge points, no new unsupported horns or spikes.
PANELS=[
 ('Shoulder_primary', [(-.482,.112),(-.407,.169),(-.310,.177),(-.265,.112),(-.280,.025),(-.333,-.126),(-.425,-.113),(-.487,-.010)],(-.376,.052),.021),
 ('Shoulder_upper_overlap',[(-.408,.174),(-.302,.212),(-.188,.204),(-.235,.153),(-.284,.107),(-.324,.134)],(-.291,.170),.018),
 ('Thorax_lateral',[(-.260,.145),(-.192,.187),(-.080,.178),(-.007,.142),(-.048,.085),(-.139,.048),(-.231,.075)],(-.141,.127),.022),
 ('Thorax_lower',[(-.243,.041),(-.157,.022),(-.073,.052),(-.022,.078),(-.070,-.008),(-.160,-.064),(-.238,-.077)],(-.156,-.003),.012),
 ('Waist_upper',[(-.015,.148),(.070,.187),(.167,.202),(.201,.167),(.110,.132),(.029,.110)],(.091,.165),.012),
 ('Haunch_primary',[(.236,.156),(.291,.205),(.378,.187),(.414,.114),(.410,.010),(.371,-.126),(.304,-.104),(.269,-.007)],(.341,.079),.025),
 ('Haunch_forward',[(.198,.159),(.257,.147),(.283,.069),(.292,-.028),(.260,-.085),(.220,-.029),(.194,.058)],(.242,.063),.016),
]
fit_audit=[]
for side in (1,-1):
 for label,outline,center,bulge in PANELS:
  # Match the small preexisting left/right placement differences using the actual mesh.
  # Cap size remains authored; each side is projected separately onto its body.
  def surface(y,z,offset):
   hit,n,idx,dist=bvh.ray_cast(Vector((side*2,y,z)),Vector((-side,0,0)))
   if hit is None:
    # Edges at the silhouette seat onto the nearest original surface.
    hit,n,idx,dist=bvh.find_nearest(Vector((-.0355+side*.04,y,z)))
    fit_audit.append({'panel':label,'side':side,'edge_seated':[y,z],'distance':dist})
   return (hit.x+side*(offset+.004),hit.y,hit.z)
  # Middle ring makes the plate a shallow convex faceted surface with a sharp narrow rim.
  cy,cz=center
  n=len(outline)
  outer=[surface(y,z,.0035) for y,z in outline]
  inner=[surface(cy+(y-cy)*.68,cz+(z-cz)*.68,bulge*.76) for y,z in outline]
  # Two spatially distinct ridge vertices avoid a uniform cone/diamond appearance.
  ridge_a=surface(cy-.021,cz+.016,bulge)
  ridge_b=surface(cy+.021,cz-.018,bulge*.93)
  verts=outer+inner+[ridge_a,ridge_b]
  faces=[]
  for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
  # Stable center fan with a short directional ridge; each triangle is a real plane.
  ia,ib=2*n,2*n+1
  for i in range(n):
   j=(i+1)%n
   yi=(outline[i][0]+outline[j][0])/2
   faces.append((n+i,n+j,ia if yi<cy else ib))
  # Fill transition wedges between the two ridge vertices.
  for i in range(n):
   prev=(outline[(i-1)%n][0]+outline[i][0])/2<cy
   nxt=(outline[i][0]+outline[(i+1)%n][0])/2<cy
   if prev!=nxt: faces.append((n+i,ia,ib) if prev else (n+i,ib,ia))
  mesh=bpy.data.meshes.new(label+('_R' if side==1 else '_L'))
  mesh.from_pydata(verts,[],faces);mesh.update()
  obj=bpy.data.objects.new('H0_'+mesh.name,mesh);armor.objects.link(obj)
  # Recalculate outward consistent normals.
  import bmesh
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
  # Point the open shell towards the viewing side before solidifying inward.
  if sum(p.normal.x for p in mesh.polygons)*side<0:
   bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
  # Geometric subdivision seats a curved outline without painting fake plates.
  bm=bmesh.new();bm.from_mesh(mesh)
  bmesh.ops.triangulate(bm,faces=list(bm.faces))
  bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=2,use_grid_fill=True)
  for v in bm.verts:
   hit,normal,ix,dist=bvh.ray_cast(Vector((side*2,v.co.y,v.co.z)),Vector((-side,0,0)))
   if hit is not None and side*(v.co.x-hit.x)<.012: v.co.x=hit.x+side*.012
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
  for p in mesh.polygons:p.use_smooth=True
  mesh.materials.append(white);mesh.materials.append(edge)
  solid=obj.modifiers.new('True_plate_thickness','SOLIDIFY');solid.thickness=.005;solid.offset=-1;solid.material_offset_rim=1
  bevel=obj.modifiers.new('Narrow_softened_plate_edges','BEVEL');bevel.width=.0017;bevel.segments=2
  bevel.limit_method='ANGLE';bevel.angle_limit=.5
  obj['purpose']='H0 torso armor only; hand-authored border fitted onto revised source mesh'
  obj['canonical_reference']=str(REF.relative_to(ROOT))
# Front-facing shoulder plates join the side shoulder mass around the anterior breast.
def fitted_panel(name,outline,center,bulge,axis,direction):
 import bmesh
 def project(u,v,lift):
  if axis=='Y':
   origin=Vector((u,-2,v));ray=Vector((0,1,0))
  else:
   origin=Vector((u,v,2));ray=Vector((0,0,-1))
  hit,n,ix,dist=bvh.ray_cast(origin,ray)
  assert hit is not None,(name,u,v)
  hit['XYZ'.index(axis)]+=direction*lift
  return hit
 n=len(outline);cu,cv=center
 verts=[project(u,v,.012) for u,v in outline]
 verts += [project(cu+(u-cu)*.64,cv+(v-cv)*.64,bulge*.9) for u,v in outline]
 verts.append(project(cu,cv,bulge))
 faces=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 faces += [(i+n,(i+1)%n+n,2*n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=list(bm.faces))
 bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=2,use_grid_fill=True)
 idx='XYZ'.index(axis)
 for v in bm.verts:
  if axis=='Y':u,w=v.co.x,v.co.z
  else:u,w=v.co.x,v.co.y
  surface=project(u,w,.012)
  if direction*(v.co[idx]-surface[idx])<0:v.co[idx]=surface[idx]
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 if sum(p.normal[idx] for p in mesh.polygons)*direction<0:
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 for p in mesh.polygons:p.use_smooth=True
 obj=bpy.data.objects.new(name,mesh);armor.objects.link(obj)
 mesh.materials.append(white);mesh.materials.append(edge)
 so=obj.modifiers.new('True_plate_thickness','SOLIDIFY');so.thickness=.005;so.offset=-1;so.material_offset_rim=1
 be=obj.modifiers.new('Narrow_softened_plate_edges','BEVEL');be.width=.0012;be.segments=2;be.limit_method='ANGLE'
 obj['purpose']='H0 surface-fitted torso armor; original image is sole authority'
for side in (1,-1):
 outline=[(.083,.123),(.120,.077),(.168,.025),(.190,-.039),(.168,-.094),(.125,-.134),(.081,-.102),(.066,-.035),(.073,.056)]
 outline=[(-.0355+side*u,v) for u,v in outline]
 fitted_panel('H0_Shoulder_anterior_'+('R' if side==1 else 'L'),outline,(-.0355+side*.126,-.027),.020,'Y',-1)
fitted_panel('H0_Pelvis_dorsal_cap',[(-.0355,.155),(.032,.192),(.056,.283),(.025,.346),(-.0355,.373),(-.098,.332),(-.123,.245),(-.096,.184)],(-.0355,.26),.012,'Z',1)
for p in body.data.polygons:p.use_smooth=True
scene['H0_status']='REJECT_H0_NOT_GAME_READY'
scene['H0_review']='S_H0_BODY_ARMOR_PASS1_REVIEW.md'
scene['H0_source_commit']='99a9e454b048336f8383b1ec6ebdcb9e41a44c77'
scene['H0_reference_sha256']=hashlib.sha256(REF.read_bytes()).hexdigest()
scene['H0_stop']='Do not proceed to H1, rigging, animation, or runtime integration.'
scene.render.engine='BLENDER_WORKBENCH'
sh=scene.display.shading
sh.light='STUDIO';sh.studiolight_rotate_z=math.radians(18)
sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='WORLD';sh.curvature_ridge_factor=1.15;sh.curvature_valley_factor=.8
sh.cavity_ridge_factor=.65;sh.cavity_valley_factor=.8
sh.background_type='WORLD'
if scene.world is None: scene.world=bpy.data.worlds.new('H0_Review_World')
scene.world.color=(.38,.38,.38)
sh.show_specular_highlight=False
scene.view_settings.view_transform='AgX'
scene.render.resolution_x=1440;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=2.16
center=Vector((-.0355,.035,-.0354))
views={'SIDE':(1,0,0),'FRONT':(0,-1,0),'FRONT34':(1,-1,0),'REAR34':(1,1,0),'BACK':(0,1,0)}
cam.location=center+Vector(views['FRONT34']).normalized()*5
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(REVIEW/'S_H0_FRONT34.png')
# Store exact source basis and local modification audit. Counts are not an art acceptance criterion.
changed=np.array([list(v.co) for v in sculpt.data])-source
stats={'source_blend_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'source_commit':scene['H0_source_commit'],'reference_sha256':scene['H0_reference_sha256'],'reference_bytes':REF.stat().st_size,'base_vertices_retained':len(source),'shape_key_changed_vertices':int(np.count_nonzero(np.linalg.norm(changed,axis=1)>1e-8)),'max_vertex_displacement':float(np.linalg.norm(changed,axis=1).max()),'protected_distal_leg_vertices_unchanged':bool(np.max(np.abs(changed[source[:,2]<=-.25]))==0),'protected_head_vertices_unchanged':bool(np.max(np.abs(changed[source[:,1]<=-.61]))==0),'protected_tail_vertices_unchanged':bool(np.max(np.abs(changed[source[:,1]>=.495]))==0),'armor_panels':len(armor.objects),'edge_fit_events':fit_audit,'review_materials':'Same neutral slate display applied to baseline and revised; white geometry is H0 armor. No source texture or new head/leg/tail detail.','render_camera':{'center':list(center),'ortho_scale':cam.data.ortho_scale,'resolution':[1440,1080],'views':views}}
(OUT/'H0_GEOMETRY_PROVENANCE.json').write_text(json.dumps(stats,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'S_H0_body_armor_pass1.blend'),compress=True)
print('H0_SAVED',json.dumps(stats))
if '--preview' in sys.argv:
 scene.render.resolution_percentage=65
 bpy.ops.render.render(write_still=True)
