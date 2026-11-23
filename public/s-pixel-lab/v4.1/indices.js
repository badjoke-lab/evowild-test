// Orthographic view sectors. Keep triangles visible anywhere in this sector
// at either end of the planted-foot translation interval (v3's normal table).
const azBins=48,elBins=9,azStep=2*Math.PI/azBins,elStep=Math.PI/(2*elBins);
const margin=-(127*Math.sin((azStep+elStep)/2)+Math.sqrt(3)/2);
export class VisibleIndices {
 constructor(gl,facing,vertexCount){
  this.gl=gl;this.faces=facing.indices;this.normals=facing.normals;
  this.cache=new Map();this.bytes=0;this.compact=vertexCount<=65536;
 }
 static direction(yaw,tilt){
  const az=(Math.round(yaw/azStep)%azBins+azBins)%azBins;
  return Math.min(elBins,Math.max(0,Math.round(tilt/elStep)))*azBins+az;
 }
 get(mesh,bin){
  const key=mesh.first*(elBins+1)*azBins+bin,cache=this.cache;
  if(cache.has(key)){const hit=cache.get(key);cache.delete(key);cache.set(key,hit);return hit;}
  const az=(bin%azBins)*azStep,el=Math.floor(bin/azBins)*elStep;
  const x=Math.sin(az)*Math.cos(el),y=Math.sin(el),z=Math.cos(az)*Math.cos(el);
  const g=this.gl,n=this.normals,src=this.faces;
  const out=this.compact?new Uint16Array(mesh.count):new Uint32Array(mesh.count);
  let size=0;
  for(let i=mesh.first,end=i+mesh.count;i<end;i+=3){
   const j=i*2;
   if(n[j]*x+n[j+1]*y+n[j+2]*z<margin&&n[j+3]*x+n[j+4]*y+n[j+5]*z<margin)continue;
   out[size++]=src[i];out[size++]=src[i+1];out[size++]=src[i+2];
  }
  const ib=g.createBuffer();g.bindBuffer(g.ELEMENT_ARRAY_BUFFER,ib);
  g.bufferData(g.ELEMENT_ARRAY_BUFFER,out.subarray(0,size),g.STATIC_DRAW);
  const slice={ib,count:size,type:this.compact?g.UNSIGNED_SHORT:g.UNSIGNED_INT,bytes:size*out.BYTES_PER_ELEMENT};
  cache.set(key,slice);this.bytes+=slice.bytes;
  while(this.bytes>8*1024*1024){
   const oldest=cache.keys().next().value,drop=cache.get(oldest);cache.delete(oldest);g.deleteBuffer(drop.ib);this.bytes-=drop.bytes;
  }
  return slice;
 }
}
