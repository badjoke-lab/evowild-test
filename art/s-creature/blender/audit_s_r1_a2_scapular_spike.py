"""Read-only shoulder ridge survey from real EvoWild S R1-A2 mesh.

Measure actual vertices to avoid guessing scapular apex coordinates.
The accepted and experimental geometry are not edited.
"""
import bpy,json,math
from pathlib import Path
ROOT=Path(bpy.path.abspath("//")).resolve()
OUT=ROOT/"art/s-creature/output/review/authority-r1-a2-anatomy"
OUT.mkdir(parents=True,exist_ok=True)
body=bpy.data.objects["S_B2a_v5_continuous_body"]
verts=body.data.vertices
res={"source":"R1-A2 actual Blender editable geometry","bins":{},"tips":{},"candidate_spikes":{}}
for side in (-1,1):
    label="L" if side<0 else "R"
    subset=[(v.index,v.co) for v in verts
            if .065<=abs(v.co.x)<=.235 and -.22<v.co.y<.30 and .78<v.co.z<1.23
            and v.co.x*side>0]
    buckets=[]
    for i in range(13):
        y0=-.22+i*.04;y1=y0+.04
        values=sorted([(p.z,j,p.x,p.y) for j,p in subset if y0<=p.y<y1],reverse=True)
        buckets.append({"y_range":[round(y0,4),round(y1,4)],"count":len(values),
          "top_z":round(values[0][0],5) if values else None,
          "top_vertices":[{"index":j,"x":round(float(x),5),"y":round(float(y),5),"z":round(float(z),5)}
                 for z,j,x,y in values[:5]]})
    # We search a relatively broad shoulder roof. Some samples may be neck
    # not scapula: keep all data rather than claiming perfect identification.
    top=sorted([(p.z,j,p.x,p.y) for j,p in subset if -.1<p.y<.20],reverse=True)[:50]
    res["bins"][label]=buckets
    res["tips"][label]=[{"index":j,"x":round(float(x),6),
                  "y":round(float(y),6),"z":round(float(z),6)} for z,j,x,y in top]
with open(OUT/"R1_A2_SCAPULAR_APEX_SURVEY.json","w") as f:json.dump(res,f,indent=2)
print(json.dumps({side:[x for x in res["bins"][side] if x["top_z"] is not None] for side in ("L","R")},indent=2))
