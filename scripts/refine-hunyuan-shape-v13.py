import math
import os
import sys
import json
import numpy as np
import trimesh


def args():
    xs=sys.argv
    if "--" not in xs:
        raise SystemExit("Expected input.glb output.glb metadata.json")
    user=xs[xs.index("--")+1:]
    if len(user)!=3:
        raise SystemExit("Expected 3 args")
    return [os.path.abspath(x) for x in user]


def tube_mesh(points,radii_x,radii_y=None,sections=12):
    pts=np.asarray(points,dtype=float)
    rx=np.asarray(radii_x,dtype=float)
    ry=rx if radii_y is None else np.asarray(radii_y,dtype=float)
    n=len(pts)
    verts=[]
    faces=[]
    for i,p in enumerate(pts):
        if i==0:
            tangent=pts[1]-pts[0]
        elif i==n-1:
            tangent=pts[-1]-pts[-2]
        else:
            tangent=pts[i+1]-pts[i-1]
        tangent=tangent/np.linalg.norm(tangent)
        e1=np.array([1.0,0.0,0.0])
        e1=e1-tangent*np.dot(e1,tangent)
        if np.linalg.norm(e1)<1e-8:
            e1=np.array([0.0,1.0,0.0])
            e1=e1-tangent*np.dot(e1,tangent)
        e1=e1/np.linalg.norm(e1)
        e2=np.cross(tangent,e1)
        e2=e2/np.linalg.norm(e2)
        for j in range(sections):
            a=2.0*math.pi*j/sections
            verts.append(p+e1*rx[i]*math.cos(a)+e2*ry[i]*math.sin(a))

    for i in range(n-1):
        for j in range(sections):
            a=i*sections+j
            b=i*sections+(j+1)%sections
            c=(i+1)*sections+(j+1)%sections
            d=(i+1)*sections+j
            faces.append([a,b,c])
            faces.append([a,c,d])

    verts.append(pts[0]); c0=len(verts)-1
    verts.append(pts[-1]); c1=len(verts)-1
    for j in range(sections):
        faces.append([c0,(j+1)%sections,j])
        a=(n-1)*sections+j
        b=(n-1)*sections+(j+1)%sections
        faces.append([c1,a,b])

    return trimesh.Trimesh(
        vertices=np.asarray(verts),
        faces=np.asarray(faces),
        process=False
    )


def main():
    input_path,output_path,meta_path=args()
    os.makedirs(os.path.dirname(output_path),exist_ok=True)
    os.makedirs(os.path.dirname(meta_path),exist_ok=True)

    scene=trimesh.load(input_path,force="scene")
    if len(scene.geometry)!=1:
        raise RuntimeError(f"Expected one source geometry, got {len(scene.geometry)}")
    source=next(iter(scene.geometry.values())).copy()

    v=np.asarray(source.vertices).copy()
    f=np.asarray(source.faces).copy()
    original=v.copy()

    x_min,y_min,z_min=v.min(axis=0)
    x_max,y_max,z_max=v.max(axis=0)
    cx=(x_min+x_max)*0.5

    # Verified raw GLB basis:
    # X lateral, Y vertical, +Z head, -Z tail.
    body=(
        (v[:,2]>-0.50)&(v[:,2]<0.45)&
        (v[:,1]>-0.18)&(v[:,1]<0.30)
    )
    v[body,2]=(v[body,2])*1.07
    v[body,0]=cx+(v[body,0]-cx)*0.93

    belly=(
        (v[:,2]>-0.45)&(v[:,2]<0.38)&
        (v[:,1]>-0.22)&(v[:,1]<0.06)
    )
    factor=np.clip((0.06-v[belly,1])/0.28,0.0,1.0)
    v[belly,1]+=0.035*factor

    head=(
        (v[:,2]>0.53)&(v[:,2]<1.01)&
        (v[:,1]>0.18)&(v[:,1]<0.52)
    )
    hx=float(np.median(v[head,0]))
    hy=0.34
    v[head,0]=hx+(v[head,0]-hx)*0.88
    v[head,1]=hy+(v[head,1]-hy)*0.94

    face_original=original[f]

    crest_vertex=(
        (face_original[:,:,1]>0.43)&
        (face_original[:,:,2]>0.40)&
        (face_original[:,:,2]<0.90)
    )
    remove_crest=(crest_vertex.sum(axis=1)>=2)

    tail_vertex=(
        (face_original[:,:,2]<-0.55)&
        (face_original[:,:,1]>-0.36)
    )
    remove_tail=(tail_vertex.sum(axis=1)>=2)

    keep=~(remove_crest|remove_tail)
    body_mesh=trimesh.Trimesh(
        vertices=v,
        faces=f[keep],
        process=False,
        visual=source.visual
    )
    body_mesh.remove_unreferenced_vertices()

    crest=[]
    for side in (-1.0,1.0):
        x0=cx+side*0.047
        points=np.array([
            [x0,0.44,0.61],
            [x0+side*0.005,0.52,0.54],
            [x0+side*0.008,0.61,0.44],
            [x0+side*0.007,0.70,0.31],
            [x0+side*0.004,0.78,0.17],
        ])
        crest.append(tube_mesh(
            points,
            [0.021,0.019,0.015,0.010,0.0025],
            [0.030,0.027,0.021,0.014,0.0025],
            sections=12
        ))

    tail=tube_mesh(
        np.array([
            [cx,0.05,-0.53],
            [cx,0.04,-0.66],
            [cx,0.02,-0.80],
            [cx,-0.01,-0.94],
            [cx,-0.04,-1.06],
        ]),
        [0.027,0.023,0.017,0.010,0.0025],
        [0.032,0.027,0.020,0.012,0.0025],
        sections=10
    )

    out=trimesh.Scene()
    out.add_geometry(body_mesh,geom_name="S_body",node_name="S_body")
    out.add_geometry(crest[0],geom_name="S_crest_L",node_name="S_crest_L")
    out.add_geometry(crest[1],geom_name="S_crest_R",node_name="S_crest_R")
    out.add_geometry(tail,geom_name="S_tail",node_name="S_tail")
    out.export(output_path)

    meta={
        "status":"shape_refine_v13_correct_raw_axes_candidate_not_canonical",
        "source_vertices":int(len(original)),
        "source_faces":int(len(f)),
        "body_vertices_after_surgery":int(len(body_mesh.vertices)),
        "body_faces_after_surgery":int(len(body_mesh.faces)),
        "removed_crest_faces":int(remove_crest.sum()),
        "removed_tail_faces":int(remove_tail.sum()),
        "new_crest_count":2,
        "new_tail_count":1,
        "coordinate_basis":"raw_glb_x_lateral_y_vertical_z_longitudinal_head_positive_z",
        "preview_rotation_y":"-pi/2",
        "source":os.path.basename(input_path),
        "output":os.path.basename(output_path)
    }
    with open(meta_path,"w",encoding="utf-8") as fh:
        json.dump(meta,fh,indent=2)

    if not os.path.exists(output_path) or os.path.getsize(output_path)<1024:
        raise RuntimeError("v13 GLB missing or too small")
    print("SHAPE_V13",json.dumps(meta,separators=(",",":")))


if __name__=="__main__":
    main()
