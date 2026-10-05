"""Render B2a-v3 three-station proximal forelimb root and verify scope."""
import bpy,bmesh,os,json,hashlib,math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
REVIEW=os.path.join(OUT,'review','vibe-b2a-v3');os.makedirs(REVIEW,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data
rp=os.path.join(OUT,'S-vibe-b2a-v3-validation.json')
report=json.load(open(rp))

s=report['support'];sm1=report['station_minus1'];s0=report['station0'];s1=report['station1']
XMIN,XMAX=s['abs_x_min'],s['abs_x_max'];YMIN,YMAX=s['y_min'],s['y_max'];ZMIN,ZMAX=s['z_min'],s['z_max']
EPS=1e-5
preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]

def station_point(sign,d):
    return Vector((sign*d['abs_x'],d['y'],d['z']))

def valid_segment(co,a_dict,b_dict,eps=0.0):
    sign=1.0 if co.x>=0 else -1.0
    a=station_point(sign,a_dict);b=station_point(sign,b_dict)
    axis=b-a
    t=(co-a).dot(axis)/axis.length_squared
    return -eps<=t<=1.0+eps

def inside_local(co,eps=0.0):
    ax=abs(co.x)
    if not ((XMIN-eps)<=ax<=(XMAX+eps) and (YMIN-eps)<=co.y<=(YMAX+eps) and (ZMIN-eps)<=co.z<=(ZMAX+eps)):
        return False
    return valid_segment(co,sm1,s0,eps) or valid_segment(co,s0,s1,eps)

def outside_body_coords():
    return sorted(tuple(v.co) for v in mesh.vertices if not inside_local(v.co,EPS))

def fixed_hash():
    h=hashlib.sha256()
    for co in outside_body_coords():
        h.update(repr(co).encode())
    for o in sorted(preserved,key=lambda o:o.name):
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(o.name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

assert fixed_hash()==report['fixed_geometry_hash'],'B2a-v3 fixed-scope hash mismatch before render'
bm=bmesh.new();bm.from_mesh(mesh)
assert len([e for e in bm.edges if len(e.link_faces)!=2])==0
bm.free()

scene=bpy.context.scene
views=('side','front','front34','rear34','back')
for stem in views:
    scene.camera=bpy.data.objects['S_REBUILD_CAM_'+stem.upper()]
    scene.render.filepath=os.path.join(REVIEW,'S_vibe_b2a_v3_'+stem+'.png')
    bpy.ops.render.render(write_still=True)

assert fixed_hash()==report['fixed_geometry_hash']
report['rendered_views']=list(views)
report['render_fixed_geometry_unchanged']=True
report['render_non_manifold_edge_count']=0
report['status']='REVIEW_PENDING'
json.dump(report,open(rp,'w'),indent=2)

cp=os.path.join(ROOT,'CHECKPOINT.md')
lines=[]
for line in open(cp).read().splitlines():
    if line.startswith('current_stage:'):
        line='current_stage: experimental Vibe B2a-v3 three-station proximal forelimb root rendered; REVIEW_PENDING / STOPPED'
    elif line.startswith('current_model_file:'):
        line='current_model_file: output/S-vibe-b2a-v3.blend'
    elif line.startswith('next_action:'):
        line='next_action: Review B2a-v3 five views against B2a-v2/B2a-v1/B1c-v2 and approved S references. Decide KEEP/REVISE. Do not start B2b.'
    lines.append(line)
lines += [
 '',
 'vibe_gate_b2a_v3_status: REVIEW_PENDING',
 'vibe_gate_b2a_v3_scope: one local subdivision + station-1->0->1 three-station forelimb-root guide',
 'vibe_gate_b2a_v3_renders:',
 '- output/review/vibe-b2a-v3/S_vibe_b2a_v3_side.png',
 '- output/review/vibe-b2a-v3/S_vibe_b2a_v3_front.png',
 '- output/review/vibe-b2a-v3/S_vibe_b2a_v3_front34.png',
 '- output/review/vibe-b2a-v3/S_vibe_b2a_v3_rear34.png',
 '- output/review/vibe-b2a-v3/S_vibe_b2a_v3_back.png',
]
open(cp,'w').write('\n'.join(lines)+'\n')

hp=os.path.join(ROOT,'HANDOFF_STATE.json')
state=json.load(open(hp))
state.update(
 stage='VIBE_EXPERIMENT_B2A_V3_REVIEW',
 current_stage='B2a-v3 three-station proximal forelimb root rendered; review pending; modeling stopped',
 current_model_file='output/S-vibe-b2a-v3.blend',
 next_action='Review B2a-v3 against B2a-v2/B2a-v1/B1c-v2 and approved S references. Decide KEEP/REVISE. Do not start B2b.',
 accepted=False,modeling_status='STOPPED',editable_next=[],
 review_renders=[
  'output/review/vibe-b2a-v3/S_vibe_b2a_v3_side.png',
  'output/review/vibe-b2a-v3/S_vibe_b2a_v3_front.png',
  'output/review/vibe-b2a-v3/S_vibe_b2a_v3_front34.png',
  'output/review/vibe-b2a-v3/S_vibe_b2a_v3_rear34.png',
  'output/review/vibe-b2a-v3/S_vibe_b2a_v3_back.png'
 ],
 b2a_status='REVIEW_PENDING',b2b_status='BLOCKED'
)
json.dump(state,open(hp,'w'),ensure_ascii=False,indent=2)
print('VIBE_B2A_V3_RENDER_COMPLETE_STOPPED')
