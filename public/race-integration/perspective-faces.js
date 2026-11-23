// A ray from a perspective eye sees the front side of a triangle when
// dot(normal, eye - vertex) >= 0. Bound the eyes of the entire instance batch
// by one local-space box. Preserve triangle order and every ambiguous face.
const cell = 512;
export function includeEye(box,x,y,z){
  const a=Math.floor(x/cell), b=Math.floor(y/cell), c=Math.floor(z/cell);
  if(!box)return [a,b,c,a+1,b+1,c+1];
  box[0]=Math.min(box[0],a); box[1]=Math.min(box[1],b); box[2]=Math.min(box[2],c);
  box[3]=Math.max(box[3],a+1); box[4]=Math.max(box[4],b+1); box[5]=Math.max(box[5],c+1);
  return box;
}

export class PerspectiveFaces {
  constructor(gl,surface,meta) {
    this.gl=gl;
    this.faces=surface.facing.faces;
    this.compact=surface.info.vertexBytes/8<=65536;
    this.cache=new Map();
    this.bytes=0;
    // Same interleaved quantized vertices referenced by the frozen v4.1 EBO.
    const q=new Uint16Array(this.faces.buffer,0,surface.info.vertexBytes/2);
    const v=new Float64Array(q.length);
    const limbs=['nearF','farF','nearH','farH'];
    for(let i=0;i<q.length;i+=4){
      const k=surface.info.quantization;
      const x=meta.x0-385+q[i]/k*meta.sx, y=q[i+1]/k*meta.height/128, z=meta.z0+q[i+2]/k*meta.sz;
      const t=Math.max(0,Math.min(1,(y-54)/116));
      v[i]=x;v[i+1]=y;v[i+2]=z;
      v[i+3]=meta.poses[q[i+3]].feet[limbs[(x<35?0:2)+(z>0?0:1)]].contact ? meta.stride/meta.frames*(1-t*t*(3-2*t)):0;
    }
    this.planes=new Float32Array(this.faces.length/3*8);
    for(let i=0;i<this.faces.length;i+=3){
      const a=this.faces[i]*4,b=this.faces[i+1]*4,c=this.faces[i+2]*4;
      for(let end=0;end<=1;end++){
        const ax=v[a]+end*v[a+3],dx=v[b]+end*v[b+3]-ax,ex=v[c]+end*v[c+3]-ax;
        const dy=v[b+1]-v[a+1],ey=v[c+1]-v[a+1],dz=v[b+2]-v[a+2],ez=v[c+2]-v[a+2];
        const nx=dy*ez-dz*ey,ny=dz*ex-dx*ez,nz=dx*ey-dy*ex;
        const len=Math.hypot(nx,ny,nz)||1;
        this.planes.set([nx/len,ny/len,nz/len,(nx*ax+ny*v[a+1]+nz*v[a+2])/len],i/3*8+end*4);
      }
    }
    // A flat varying takes its value from the triangle's final index. Share
    // that vertex unless its other triangles require a different shade.
    const count=q.length/4, shades=new Array(count), alternatives=new Map();
    const vertices=Array.from(q), indices=this.faces.slice();
    for(let i=0;i<indices.length;i+=3){
      const j=i/3*8, x=this.planes[j],y=this.planes[j+1],z=this.planes[j+2];
      const sum=Math.abs(x)+Math.abs(y)+Math.abs(z);
      const shade=Math.fround(sum ? (Math.abs(x)*(x>0?.89:.95)+Math.abs(y)*(y>0?1.04:.78)+Math.abs(z)*(z>0?1:.88))/sum : 0);
      const source=indices[i+2];
      if(shades[source]===undefined)shades[source]=shade;
      else if(shades[source]!==shade){
        const key=source+'/'+shade;
        let variant=alternatives.get(key);
        if(variant===undefined){
          variant=shades.length;alternatives.set(key,variant);shades.push(shade);
          vertices.push(...q.subarray(source*4,source*4+4));
        }
        indices[i+2]=variant;
      }
    }
    gl.bindVertexArray(surface.vao);
    gl.bindBuffer(gl.ARRAY_BUFFER,surface.vb);
    gl.bufferData(gl.ARRAY_BUFFER,new Uint16Array(vertices),gl.STATIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER,Float32Array.from(shades,s=>s??0),gl.STATIC_DRAW);
    gl.enableVertexAttribArray(3);gl.vertexAttribPointer(3,1,gl.FLOAT,false,4,0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,surface.ib);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,indices,gl.STATIC_DRAW);gl.bindVertexArray(null);
    this.faces=indices;this.compact=shades.length<=65536;
  }

  get(mesh,box){
    const key=mesh.first+'/'+box.join('/');
    const existing=this.cache.get(key);
    if(existing){this.cache.delete(key);this.cache.set(key,existing);return existing;}
    const gl=this.gl, p=this.planes;
    const cx=(box[3]+box[0])*cell/2,cy=(box[4]+box[1])*cell/2,cz=(box[5]+box[2])*cell/2;
    const hx=(box[3]-box[0])*cell/2,hy=(box[4]-box[1])*cell/2,hz=(box[5]-box[2])*cell/2;
    const out=this.compact?new Uint16Array(mesh.count):new Uint32Array(mesh.count);
    let count=0;
    // Drift translates vertices only in X. The unnormalised oriented plane
    // test is affine in drift, so rejection at both ends covers the entire fractional pose interval.
    for(let i=mesh.first;i<mesh.first+mesh.count;i+=3){
      let keep=false;
      for(let j=i/3*8;j<i/3*8+8;j+=4){
        const x=p[j],y=p[j+1],z=p[j+2];
        if(x*cx+y*cy+z*cz-p[j+3]+Math.abs(x)*hx+Math.abs(y)*hy+Math.abs(z)*hz>=-2){keep=true;break;}
      }
      if(keep){out[count++]=this.faces[i];out[count++]=this.faces[i+1];out[count++]=this.faces[i+2];}
    }
    const ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,out.subarray(0,count),gl.STATIC_DRAW);
    const entry={ib,count,type:this.compact?gl.UNSIGNED_SHORT:gl.UNSIGNED_INT,bytes:count*out.BYTES_PER_ELEMENT};
    this.cache.set(key,entry);this.bytes+=entry.bytes;
    while(this.bytes>8*1024*1024){const first=this.cache.keys().next().value,drop=this.cache.get(first);gl.deleteBuffer(drop.ib);this.bytes-=drop.bytes;this.cache.delete(first);}
    return entry;
  }
}
