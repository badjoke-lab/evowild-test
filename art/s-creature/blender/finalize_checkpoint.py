import bpy,os,json,bmesh
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-blockout-v2.blend'))
body=bpy.data.objects['S_organism_blockout_v2'];me=body.data
# Check connected surface and manifoldness; no deformation-ready topology claim.
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();seen=set();components=[]; small=[]
for v in bm.verts:
 if v.index in seen:continue
 stack=[v];seen.add(v.index);n=0; group=[]
 while stack:
  a=stack.pop();n+=1;group.append(a)
  for e in a.link_edges:
   b=e.other_vert(a)
   if b.index not in seen:seen.add(b.index);stack.append(b)
 components.append(n)
 if n<100:small.extend(group)
if small:
 bmesh.ops.delete(bm,geom=small,context='VERTS');bm.to_mesh(me);me.update();components=[n for n in components if n>=100]
report={'stage':'S-blockout-v2','vertices':len(me.vertices),'polygons':len(me.polygons),'connected_component_sizes':sorted(components,reverse=True),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'rigged':False,'animation_tested':False,'reference_accepted':False,'front_axis':'-Y','up_axis':'+Z'}
bm.free()
# Neutral review plane meets the plantar surface.
minz=min(v.co.z for v in me.vertices);bpy.data.objects['REVIEW_GROUND'].location.z=minz-.002
report['ground_plane_z']=minz-.002
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
# File opens directly on the organism, with references retained externally.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_distance=6.2
   area.spaces.active.region_3d.view_location=(0,0,2.05)
   area.spaces.active.clip_end=200
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-blockout-v2.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'S-blockout-v2.glb'),use_selection=True,export_format='GLB')
json.dump(report,open(os.path.join(OUT,'validation.json'),'w'),indent=2)
print('VALIDATION',json.dumps(report))
script=open(os.path.join(ROOT,'blender/render_review.py')).read().replace("'//output/review/'",repr(os.path.join(OUT,'review/v2/')))
if not os.environ.get('S_SKIP_RENDER'):exec(compile(script,'render_review.py','exec'))
