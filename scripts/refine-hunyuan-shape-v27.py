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


def tube_mesh(points, radii_x, radii_y=None, sections=12):
    pts=np.asarray(points,dtype=float)
    rx=np.asarray(radii_x,dtype=float)
    ry=rx if radii_y is None else np.asarray(radii_y,dtype=float)
    verts=[]; faces=[]
    for i,p in enumerate(pts):
        if i==0:
            tangent=pts[1]-pts[0]
        elif i==len(pts)-1:
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
        e2=np.cross(tangent,e1); e2=e2/np.linalg.norm(e2)
        for j in range(sections):
            a=2.0*math.pi*j/sections
            verts.append(p+e1*rx[i]*math.cos(a)+e2*ry[i]*math.sin(a))
    for i in range(len(pts)-1):
        for j in range(sections):
            a=i*sections+j
            b=i*sections+(j+1)%sections
            c=(i+1)*sections+(j+1)%sections
            d=(i+1)*sections+j
            faces.append([a,b,c]); faces.append([a,c,d])
    verts.append(pts[0]); c0=len(verts)-1
    verts.append(pts[-1]); c1=len(verts)-1
    for j in range(sections):
        faces.append([c0,(j+1)%sections,j])
        a=(len(pts)-1)*sections+j
        b=(len(pts)-1)*sections+(j+1)%sections
        faces.append([c1,a,b])
    return trimesh.Trimesh(vertices=np.asarray(verts),faces=np.asarray(faces),process=False)


def blade_mesh(points, half_widths, half_thicknesses):
    pts=np.asarray(points,dtype=float)
    widths=np.asarray(half_widths,dtype=float)
    thickness=np.asarray(half_thicknesses,dtype=float)
    verts=[]; faces=[]
    for i,p in enumerate(pts):
        if i==0:
            tangent=pts[1]-pts[0]
        elif i==len(pts)-1:
            tangent=pts[-1]-pts[-2]
        else:
            tangent=pts[i+1]-pts[i-1]
        tangent=tangent/np.linalg.norm(tangent)
        yz=np.array([0.0,-tangent[2],tangent[1]])
        if np.linalg.norm(yz)<1e-8:
            yz=np.array([0.0,1.0,0.0])
        yz=yz/np.linalg.norm(yz)
        xaxis=np.array([1.0,0.0,0.0])
        n=yz*widths[i]; t=xaxis*thickness[i]
        verts.extend([p-t-n,p+t-n,p+t+n,p-t+n])
    for i in range(len(pts)-1):
        a=i*4; b=(i+1)*4
        faces += [
            [a+0,b+0,b+3],[a+0,b+3,a+3],
            [a+1,a+2,b+2],[a+1,b+2,b+1],
            [a+3,b+3,b+2],[a+3,b+2,a+2],
            [a+0,a+1,b+1],[a+0,b+1,b+0],
        ]
    faces += [[0,3,2],[0,2,1]]
    e=(len(pts)-1)*4
    faces += [[e+0,e+1,e+2],[e+0,e+2,e+3]]
    return trimesh.Trimesh(vertices=np.asarray(verts),faces=np.asarray(faces),process=False)


def keep_largest_component(mesh):
    parts=mesh.split(only_watertight=False)
    if not parts:
        return mesh,0,0
    parts=sorted(parts,key=lambda m:len(m.faces),reverse=True)
    removed=sum(len(p.faces) for p in parts[1:])
    return parts[0],len(parts),int(removed)


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
    cx=float((v[:,0].min()+v[:,0].max())*0.5)

    # Preserve the source Hunyuan body and all four legs exactly.
    # Only remove the legacy fan crest and feather tail.
    fo=original[f]

    crest_vertex=(
        (fo[:,:,1] > 0.40) &
        (fo[:,:,2] > 0.08) &
        (fo[:,:,2] < 0.92)
    )
    remove_crest=(crest_vertex.sum(axis=1)>=2)

    tail_vertex=(
        (fo[:,:,2] < -0.55) &
        (fo[:,:,1] > -0.36)
    )
    remove_tail=(tail_vertex.sum(axis=1)>=2)

    keep=~(remove_crest|remove_tail)
    body=trimesh.Trimesh(
        vertices=v.copy(),
        faces=f[keep].copy(),
        process=False,
        visual=source.visual,
    )
    body.remove_unreferenced_vertices()
    body,component_count,detached_removed=keep_largest_component(body)

    # Repair only surgery boundaries; do not globally smooth or reshape.
    holes_filled=bool(trimesh.repair.fill_holes(body))
    trimesh.repair.fix_normals(body,multibody=True)

    # Two integrated, swept blade crests. Slightly thicker at root than v22
    # and shorter at tip so they read as skull-integrated racing structures.
    crests=[]
    for side in (-1.0,1.0):
        x0=cx+side*0.034
        pts=np.array([
            [x0,0.397,0.615],
            [x0+side*0.0015,0.428,0.535],
            [x0+side*0.0025,0.462,0.445],
            [x0+side*0.0020,0.495,0.345],
            [x0,0.520,0.245],
        ])
        crests.append(blade_mesh(
            pts,
            [0.023,0.024,0.020,0.013,0.0028],
            [0.0070,0.0062,0.0052,0.0036,0.0013],
        ))

    # One streamlined balancing tail. Much shorter/thicker than the v22
    # needle-tail, while keeping the source rear body untouched.
    tail=tube_mesh(
        np.array([
            [cx,0.030,-0.515],
            [cx,0.028,-0.635],
            [cx,0.020,-0.765],
            [cx,0.006,-0.890],
            [cx,-0.010,-0.995],
        ]),
        [0.034,0.031,0.024,0.014,0.0030],
        [0.037,0.034,0.026,0.015,0.0030],
        sections=12,
    )

    out=trimesh.Scene()
    out.add_geometry(body,geom_name="S_body_source_preserved",node_name="S_body_source_preserved")
    out.add_geometry(crests[0],geom_name="S_crest_L",node_name="S_crest_L")
    out.add_geometry(crests[1],geom_name="S_crest_R",node_name="S_crest_R")
    out.add_geometry(tail,geom_name="S_tail",node_name="S_tail")
    out.export(output_path)

    meta={
        "status":"shape_refine_v27_conservative_appendage_surgery_candidate_not_canonical",
        "source_vertices":int(len(original)),
        "source_faces":int(len(f)),
        "body_vertices_after_surgery":int(len(body.vertices)),
        "body_faces_after_surgery":int(len(body.faces)),
        "removed_crest_faces":int(remove_crest.sum()),
        "removed_tail_faces":int(remove_tail.sum()),
        "source_component_count_after_cut":int(component_count),
        "detached_faces_removed":int(detached_removed),
        "holes_filled":holes_filled,
        "body_and_limbs_modified":False,
        "new_crest_count":2,
        "crest_geometry":"swept_blade_prism",
        "new_tail_count":1,
        "tail_geometry":"short_tapered_balance_tube",
        "coordinate_basis":"raw_glb_x_lateral_y_vertical_z_longitudinal_head_positive_z",
        "preview_rotation_y":"-pi/2",
        "reference":"public/concept/S.webp",
        "source":os.path.basename(input_path),
        "output":os.path.basename(output_path),
    }
    with open(meta_path,"w",encoding="utf-8") as fh:
        json.dump(meta,fh,indent=2)

    if not os.path.exists(output_path) or os.path.getsize(output_path)<1024:
        raise RuntimeError("v27 GLB missing or too small")
    print("SHAPE_V27",json.dumps(meta,separators=(",",":")))


if __name__=="__main__":
    main()
