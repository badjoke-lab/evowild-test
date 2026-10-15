"""A deliberate frontal taper of the shoulder block, checked in three views."""
import bpy,bmesh,json
pilot=bpy.app.driver_namespace['shoulder_pilot'];body=pilot['body'];OUT=pilot['OUT']
SIDE=globals().get('SIDE',1);STAGE=globals().get('STAGE','11_FRONTAL_TAPER')
pilot['before_taper']=body.data.copy()
def ramp(a,b,t):
    q=max(0,min(1,(t-a)/(b-a)));return q*q*(3-2*q)
bm=bmesh.new();bm.from_mesh(body.data)
count=0
for v in bm.verts:
    x,y,z=v.co;mid=-.03588832542300224;xlocal=mid+SIDE*(x-mid)
    side=ramp(mid+.012,mid+.055,xlocal)
    length=ramp(-.63,-.48,y)*(1-ramp(-.16,-.05,y))
    height=ramp(-.24,-.12,z)*(1-ramp(.15,.24,z))
    w=side*length*height
    if w:
        v.co.x-=SIDE*.12*(xlocal-mid)*w
        count+=1
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data);bm.free();body.data.update()
(OUT/(STAGE+'_OPERATION.json')).write_text(json.dumps({'operation':'12 percent lateral anatomical taper including rear shoulder support; no superior shearing','side':SIDE,'vertices_shaped':count},indent=2))
pilot['view']('SIDE' if SIDE==1 else 'LEFT_SIDE',STAGE)
