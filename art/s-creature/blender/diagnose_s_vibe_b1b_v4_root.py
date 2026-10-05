"""Diagnostic only: inspect B0-v025 fore-shoulder root local geometry.
No geometry is modified. Writes JSON only.
"""
import bpy, os, json, math, statistics
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

# Diagnostic shoulder/root window around both forelimb insertions.
verts=[]
for v in mesh.vertices:
    x,y,z=v.co
    if 0.055 <= abs(x) <= 0.20 and -0.16 <= y <= 0.16 and 0.82 <= z <= 1.16:
        verts.append((v.index,float(x),float(y),float(z)))

# Group into longitudinal bands to expose the upper/lower envelope.
bands=[]
edges=[-0.16,-0.12,-0.08,-0.04,0.0,0.04,0.08,0.12,0.16]
for a,b in zip(edges[:-1],edges[1:]):
    pts=[p for p in verts if a <= p[2] < b and p[1] > 0]
    if not pts:
        continue
    zs=[p[3] for p in pts]
    xs=[p[1] for p in pts]
    bands.append({
      'y_range':[a,b],
      'count':len(pts),
      'z_min':min(zs),'z_q25':statistics.quantiles(zs,n=4,method='inclusive')[0] if len(zs)>=4 else min(zs),
      'z_median':statistics.median(zs),
      'z_q75':statistics.quantiles(zs,n=4,method='inclusive')[2] if len(zs)>=4 else max(zs),
      'z_max':max(zs),
      'x_min':min(xs),'x_median':statistics.median(xs),'x_max':max(xs)
    })

# Top-envelope vertices: candidates responsible for the step.
top_candidates=[]
for a,b in zip(edges[:-1],edges[1:]):
    pts=[p for p in verts if a <= p[2] < b and p[1] > 0]
    if not pts:
        continue
    pts=sorted(pts,key=lambda p:p[3],reverse=True)[:10]
    top_candidates.extend([{'index':p[0],'x':p[1],'y':p[2],'z':p[3],'band':[a,b]} for p in pts])

report={
 'lane':'exp/s-creature-vibe-modeling',
 'source':'S-vibe-b0-v025.blend',
 'purpose':'diagnose shoulder-root Y/Z connection before B1b-v4',
 'window':{'abs_x':[0.055,0.20],'y':[-0.16,0.16],'z':[0.82,1.16]},
 'vertex_count':len(verts),
 'positive_side_bands':bands,
 'positive_side_top_candidates':top_candidates,
 'status':'DIAGNOSTIC_ONLY'
}
path=os.path.join(OUT,'S-vibe-b1b-v4-root-diagnostic.json')
with open(path,'w') as f: json.dump(report,f,indent=2)
print(json.dumps(report))
