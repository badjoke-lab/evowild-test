// Orthographic visibility is constant inside a cone for triangles whose normal
// stays strictly on its rear side. Test both ends of the linear support-foot
// displacement: a triangle's projected signed area is affine in this drift.
export class FacingIndices{
 constructor(gl,geo,info,meta){
  this.gl=gl;this.cache=new Map();this.bytes=0;this.maxBytes=8*1024*1024;
  const pos=new Uint16Array(geo,0,info.vertexBytes/2);
  this.indices=new Uint32Array(geo,info.vertexBytes);
  this.normals=new Int8Array(this.indices.length*2);
  const step=[meta.sx,meta.height/128,meta.sz],origin=[meta.x0-385,0,meta.z0];
  const vertices=new Float32Array(pos.length),limbs=['nearF','farF','nearH','farH'];
  for(let i=0;i<pos.length;i+=4){
   for(let k=0;k<3;k++)vertices[i+k]=pos[i+k]/info.quantization*step[k]+origin[k];
   const [x,y,z]=vertices.subarray(i,i+3),limb=(x<35?0:2)+(z>0?0:1);
   const t=Math.min(1,Math.max(0,(y-54)/116));
   vertices[i+3]=meta.poses[pos[i+3]].feet[limbs[limb]].contact?(1-t*t*(3-2*t))*meta.stride/24:0;
  }
  for(let f=0;f<this.indices.length;f+=3){
   const [a,b,c]=[this.indices[f]*4,this.indices[f+1]*4,this.indices[f+2]*4];
   const dy=vertices[b+1]-vertices[a+1],dz=vertices[b+2]-vertices[a+2],ey=vertices[c+1]-vertices[a+1],ez=vertices[c+2]-vertices[a+2];
   for(let drift=0;drift<2;drift++){
    const dx=vertices[b]-vertices[a]+drift*(vertices[b+3]-vertices[a+3]);
    const ex=vertices[c]-vertices[a]+drift*(vertices[c+3]-vertices[a+3]);
    const nx=dy*ez-dz*ey,ny=dz*ex-dx*ez,nz=dx*ey-dy*ex,n=Math.hypot(nx,ny,nz)||1;
    this.normals.set([Math.round(127*nx/n),Math.round(127*ny/n),Math.round(127*nz/n)],f*2+drift*3);
   }
  }
 }
 static direction(yaw,tilt){
  const az=(Math.round(yaw*8/Math.PI)%16+16)%16,el=Math.min(4,Math.max(0,Math.round(tilt/(Math.PI/8))));
  return el*16+az;
 }
 get(mesh,bin){
  const key=mesh.first*80+bin,old=this.cache.get(key);
  if(old){this.cache.delete(key);this.cache.set(key,old);return old;}
  const gl=this.gl,az=(bin%16)*Math.PI/8,el=Math.floor(bin/16)*Math.PI/8;
  const x=Math.sin(az)*Math.cos(el),y=Math.sin(el),z=Math.cos(az)*Math.cos(el);
  const n=this.normals,front=new Uint32Array(mesh.count);let length=0;
  // Two half-bin excursions ≤ 15.9° plus 8-bit coefficient rounding.
  const margin=-37;
  for(let i=mesh.first,end=i+mesh.count;i<end;i+=3){
   const k=i*2;
   if(n[k]*x+n[k+1]*y+n[k+2]*z<margin&&n[k+3]*x+n[k+4]*y+n[k+5]*z<margin)continue;
   front[length++]=this.indices[i];front[length++]=this.indices[i+1];front[length++]=this.indices[i+2];
  }
  const ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);
  gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,front.subarray(0,length),gl.STATIC_DRAW);
  const entry={ib,count:length};this.cache.set(key,entry);this.bytes+=length*4;
  while(this.bytes>this.maxBytes){const first=this.cache.keys().next().value,drop=this.cache.get(first);gl.deleteBuffer(drop.ib);this.bytes-=drop.count*4;this.cache.delete(first);}
  return entry;
 }
}
