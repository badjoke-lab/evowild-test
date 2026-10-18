"""Sculpt ONLY the six existing R3 crown meshes through Blender MCP.

Subdivide the existing main/blue cages without smoothing, then displace their
vertices into tapered, oblique lens sections. No object is regenerated. The
side outline above the root is retained; the root is seated into the forehead.
R3, its byte-identical copy and all other creature meshes remain untouched.
"""
import bpy
import bmesh
import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'verification/S_ZERO_R4_WORKING_COPY.blend'
TRIAL = globals().get('R4_TRIAL', 'A')
assert TRIAL in ['A', 'B', 'C', 'D']
OUT = ROOT / ('verification/S_ZERO_R4_TRIAL_' + TRIAL + '.blend')
REPORT = ROOT / ('evidence/REVISION_R4_TRIAL_' + TRIAL + '.json')
assert bpy.app.version == (4, 3, 2)
assert not OUT.exists() and not REPORT.exists()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'b3e1b1820c3019a7b466b81e06276d8585fdeb25ec425ac2a6219e55bd06a916'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False)


def signature(ob):
    h = hashlib.sha256()
    for v in ob.data.vertices:
        h.update(struct.pack('<3f', *v.co))
    for p in ob.data.polygons:
        h.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
        h.update(struct.pack('<I?', p.material_index, p.use_smooth))
    for row in ob.matrix_world:
        h.update(struct.pack('<4f', *row))
    for attr in ob.data.color_attributes:
        h.update(attr.name.encode())
        for el in attr.data:
            h.update(struct.pack('<4f', *el.color))
    return h.hexdigest()


objects = [o for o in bpy.data.collections['S_ZERO_CREATURE'].objects if o.type == 'MESH']
before = {o.name: signature(o) for o in objects}
outline = [(-2.19,2.19),(-1.98,2.43),(-1.65,2.64),(-1.18,2.83),(-.62,3.00),
           (-.08,3.11),(-.70,2.89),(-1.25,2.67),(-1.69,2.42),(-1.98,2.23)]
# Normalized height, forward edge Y, rear edge Y. Mirrored for the near crown.
sections = [(0,.080,.100),(.10,.115,.100),(.25,.170,.112),(.45,.239,.137),
            (.55,.233,.155),(.75,.211,.177),(1,.185,.185)]
if TRIAL in ['B', 'C', 'D']:
    sections = [(0,.078,.090),(.10,.115,.097),(.25,.166,.117),(.45,.222,.145),
                (.55,.226,.163),(.75,.210,.180),(1,.185,.185)]


def interp(t):
    t = min(1, max(0, t))
    for a,b in zip(sections, sections[1:]):
        if a[0] <= t <= b[0]:
            f = (t-a[0])/(b[0]-a[0])
            return a[1]*(1-f)+b[1]*f, a[2]*(1-f)+b[2]*f
    return sections[-1][1:]


def parameters(x,z):
    t = min(1, max(0, (z-2.19)/.92))
    hits = []
    for (x1,z1),(x2,z2) in zip(outline,outline[1:]+outline[:1]):
        if min(z1,z2)-1e-6 <= z <= max(z1,z2)+1e-6 and abs(z2-z1)>1e-7:
            hits.append(x1+(x2-x1)*(z-z1)/(z2-z1))
    lo,hi = (min(hits),max(hits)) if hits else (x,x)
    q = min(1, max(0, (x-lo)/max(1e-6,hi-lo)))
    return t,q


def base_y(t,q):
    # Reference R3 field on its outline, excluding its old lens relief.
    return .115 + .045*t + .065*math.sin(math.pi*t) + math.sin(math.pi*t)**1.35*(.005+.065*(.5-q))


changes = []
for ob in objects:
    if not ob.name.startswith('CROWN_'):
        continue
    old_count = (len(ob.data.vertices),len(ob.data.polygons))
    old_xz = [(v.co.x,v.co.z) for v in ob.data.vertices]
    side = -1 if ob.name.endswith('_N') else 1
    kind = 'MAIN' if '_MAIN_' in ob.name else ('BLUE' if '_BLUE_' in ob.name else 'RIDGE')
    if kind in ['MAIN','BLUE']:
        bm=bmesh.new();bm.from_mesh(ob.data)
        layer=bm.verts.layers.float.new('R4_lens_depth')
        n=(len(bm.verts)-2)//2
        for v in bm.verts:
            v[layer]=0 if v.index<n else (.83 if v.index<2*n else (1 if v.index==2*n else -.30))
        if TRIAL == 'D':
            # The original radial fan crosses the concave side outline near
            # the tip. Keep every contour vertex; locally retopologize the
            # interior of this same object by concave-polygon triangulation.
            bm.verts.ensure_lookup_table()
            boundary=list(bm.verts)[:n]
            contour=[(v.co.x,v.co.z) for v in boundary]
            bmesh.ops.delete(bm,geom=list(bm.verts)[n:],context='VERTS')
            bm.faces.new(boundary)
            bmesh.ops.triangulate(bm,faces=list(bm.faces))
            bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True,smooth=0)
            bmesh.ops.triangulate(bm,faces=list(bm.faces))
            bmesh.ops.poke(bm,faces=list(bm.faces),offset=0)
            # An interior chord whose endpoints both lie on the contour must
            # receive an interior vertex before mirroring, or the two shells
            # would share that chord with four incident faces.
            for _ in range(8):
                border={v for e in bm.edges if e.is_boundary for v in e.verts}
                chords=[e for e in bm.edges if not e.is_boundary and all(v in border for v in e.verts)]
                if not chords:
                    break
                bmesh.ops.subdivide_edges(bm,edges=chords,cuts=1,use_grid_fill=True,smooth=0)
                bmesh.ops.triangulate(bm,faces=list(bm.faces))
            else:
                raise AssertionError('Unresolved interior contour chord')
            def edge_distance(v,a,b):
                x,z=v.co.x,v.co.z
                dx,dz=b[0]-a[0],b[1]-a[1]
                f=max(0,min(1,((x-a[0])*dx+(z-a[1])*dz)/(dx*dx+dz*dz)))
                return math.hypot(x-a[0]-f*dx,z-a[1]-f*dz)
            for v in bm.verts:
                distance=min(edge_distance(v,a,b) for a,b in zip(contour,contour[1:]+contour[:1]))
                v[layer]=0 if any(e.is_boundary for e in v.link_edges) else max(.001,min(1,distance/.075))
            front=list(bm.faces);rear={}
            for v in list(bm.verts):
                if v[layer]==0:
                    rear[v]=v
                else:
                    other=bm.verts.new(v.co);other[layer]=-v[layer]*.50;rear[v]=other
            for f in front:
                new=bm.faces.new([rear[v] for v in reversed(f.verts)])
                new.material_index=f.material_index;new.smooth=f.smooth
        elif TRIAL == 'C':
            # Retopologize only the existing rear fan. Front/back now have
            # corresponding triangles, avoiding crossed faces when twisted.
            bm.verts.ensure_lookup_table()
            back=bm.verts[2*n+1]
            bmesh.ops.delete(bm,geom=list(back.link_faces),context='FACES_ONLY')
            bmesh.ops.delete(bm,geom=[back],context='VERTS')
            bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='FIXED')
            front=list(bm.faces)
            rear={}
            for v in list(bm.verts):
                if abs(v[layer])<1e-8:
                    rear[v]=v
                else:
                    other=bm.verts.new(v.co)
                    other[layer]=-v[layer]*.42
                    rear[v]=other
            for f in front:
                new=bm.faces.new([rear[v] for v in reversed(f.verts)])
                new.material_index=f.material_index
                new.smooth=f.smooth
        if TRIAL != 'D':
            bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True,smooth=0)
        bm.verts.index_update()
        depth=[v[layer] for v in bm.verts]
        bm.verts.layers.float.remove(layer)
        bm.to_mesh(ob.data);bm.free()
    prior = [v.co.copy() for v in ob.data.vertices]
    for v in ob.data.vertices:
        x,y,z = v.co
        t,q = parameters(x,z)
        lead,trail = interp(t)
        if kind == 'MAIN':
            # Retain a volumetric lens, while rotating its broad face toward front.
            relief = (abs(y)-base_y(t,q))*.72
            if TRIAL in ['B', 'C', 'D']:
                # Exact interpolated cage depth replaces A's approximate Y field.
                # Convex lens stays volumetric throughout, tapering at both ends.
                relief = depth[v.index]*(.012+.024*math.sin(math.pi*t))
            yy = lead*(1-q)+trail*q+relief
        elif kind == 'BLUE':
            # Existing blue lower blade stays in its side silhouette; twist toward
            # the oblique lower face, with positive thickness retained.
            relief = (abs(y)-base_y(t,q)-.025)*.55
            if TRIAL in ['B', 'C', 'D']:
                relief = depth[v.index]*(.006+.009*math.sin(math.pi*t))
            yy = lead*(1-q)+trail*q + .018*math.sin(math.pi*t) + relief
        else:
            # Existing tubular ivory edge is flattened into a bevel, not a rail.
            # Ring coordinates are treated separately below.
            continue
        root = max(0,1-t/.22)**2
        v.co = (x-.018*root, side*yy, z-.045*root)
    if kind == 'RIDGE':
        assert len(ob.data.vertices) == 162
        for ring in range(16):
            verts = ob.data.vertices[ring*10:ring*10+10]
            center = sum((v.co for v in verts), __import__('mathutils').Vector())/10
            t,q = parameters(center.x,center.z)
            lead,_ = interp(t)
            root = max(0,1-t/.22)**2
            for v in verts:
                delta = v.co-center
                # A shallow ivory bevel grows out of the root then thins to tip.
                v.co = (v.co.x-.018*root,side*(lead+.004)+delta.y*.48,v.co.z-.045*root)
        for end,ring in [(160,0),(161,15)]:
            ob.data.vertices[end].co = sum((ob.data.vertices[ring*10+j].co for j in range(10)),__import__('mathutils').Vector())/10
    ob.data.update()
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),ob.name
    assert all(f.calc_area()>1e-12 for f in bm.faces),ob.name
    bm.to_mesh(ob.data);bm.free()
    changes.append({'name':ob.name,'before_vertices_faces':old_count,
                    'after_vertices_faces':[len(ob.data.vertices),len(ob.data.polygons)],
                    'max_displacement_after_subdivision':max((v.co-a).length for v,a in zip(ob.data.vertices,prior)),
                    'original_side_outline_xz':old_xz[:10] if kind=='MAIN' else None,
                    'before':before[ob.name],'after':signature(ob)})

after={o.name:signature(o) for o in objects}
changed=sorted(n for n in before if before[n]!=after[n])
assert changed==sorted(r['name'] for r in changes) and len(changed)==6
assert before['S_ZERO_BODY_CONTINUOUS']==after['S_ZERO_BODY_CONTINUOUS']
scene=bpy.context.scene
scene['stage']='R4_TRIAL_'+TRIAL
scene['candidate_status']='REVISE; crown section/root trial awaiting actual image review'
scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
REPORT.write_text(json.dumps({'source':str(SOURCE.relative_to(ROOT)),'output':str(OUT.relative_to(ROOT)),
    'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'sections':sections,'changes':changes,
    'unchanged_meshes':sorted(n for n in before if before[n]==after[n]),
    'scope':'Existing paired main, blue and ivory crown meshes only. Subdivision without smoothing then vertex displacement.',
    'root_displacement':'Up to -0.018 X and -0.045 Z, fading to zero at t=0.22; no head/body mesh changed.',
    'decision':'PENDING actual SIDE FRONT FRONT34 render review'},indent=2)+'\n')
print('R4_TRIAL_'+TRIAL+'_SAVED',len(changed),'changed;',len(before)-len(changed),'meshes protected')
