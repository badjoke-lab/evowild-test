// Experimental adapter for the existing integrated surface. No asset is written.
import {bytes} from '../s-pixel-lab/v3/surface.js';

function readBuffer(gl,buffer,Type){
  gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
  const out=new Type(gl.getBufferParameter(gl.ARRAY_BUFFER,gl.BUFFER_SIZE)/Type.BYTES_PER_ELEMENT);
  gl.getBufferSubData(gl.ARRAY_BUFFER,0,out);
  return out;
}
export async function prepareCandidate(surface,meta,mode){
  // Finish I/O before touching shared WebGL bindings. Three continues to
  // render while an await is pending and can bind another geometry's VAO.
  const paintData=(mode==='color'||mode==='both')
    ? await bytes(new URL('../s-pixel-lab/v3/assets/runtime/paint.gz',import.meta.url)):null;
  const geometryData=(mode==='group'||mode==='both')
    ? await bytes(new URL('../s-pixel-lab/v4.1/assets/geometry.gz',import.meta.url)):null;
  const gl=surface.gl, facing=surface.facing, info=surface.info;
  gl.bindVertexArray(surface.vao);
  const vertices=readBuffer(gl,surface.vb,Uint16Array);
  const shadeBuffer=gl.getVertexAttrib(3,gl.VERTEX_ATTRIB_ARRAY_BUFFER_BINDING);
  const shades=readBuffer(gl,shadeBuffer,Float32Array);
  const stats={mode,eligible:0,total:facing.faces.length/3,groups:0,groupsTested:0,groupBack:0,groupOutside:0,trianglesBefore:0,trianglesAfter:0};
  window.surfaceTrialStats=stats;
  if(mode==='color'||mode==='both'){
    const raw=new Uint8Array(paintData);
    const [sy,sz,sx]=info.paintSizeYZX,section=sy*sz*sx,origin=info.paintOriginYZX;
    const inkBounds=[], expanded=Array.from(vertices), shadeValues=Array.from(shades);
    const sourceIndices=facing.faces, indices=sourceIndices.slice(),assigned=new Map();
    for(let f=0;f<indices.length;f+=3){
      const ids=Array.from(sourceIndices.subarray(f,f+3));
      const lo=[],hi=[];
      for(const [k,axis] of [1,2,0].entries()){
        // One extra voxel on both sides absorbs quantization/interpolation error.
        lo[k]=Math.max(0,Math.min([sy,sz,sx][k]-1,Math.floor(Math.min(...ids.map(i=>vertices[i*4+axis]/info.quantization)))-1-origin[k]));
        hi[k]=Math.max(0,Math.min([sy,sz,sx][k]-1,Math.floor(Math.max(...ids.map(i=>vertices[i*4+axis]/info.quantization)))+1-origin[k]));
      }
      const pose=vertices[ids[0]*4+3];
      let ink=raw[pose*section+(lo[0]*sz+lo[1])*sx+lo[2]],same=shades[ids[2]]>0;
      scan:for(let y=lo[0];same&&y<=hi[0];y++)for(let z=lo[1];z<=hi[1];z++)for(let x=lo[2];x<=hi[2];x++){
        if(raw[pose*section+(y*sz+z)*sx+x]!==ink){same=false;break scan;}
      }
      if(!same)continue;
      stats.eligible++;
      const attributes=[...lo,ink,...hi];
      const source=ids[2],key=source+'/'+attributes.join('/');
      let target=assigned.get(key);
      if(target===undefined){
        target=expanded.length/4;assigned.set(key,target);
        expanded.push(...vertices.subarray(source*4,source*4+4));shadeValues.push(shades[source]);
        inkBounds.push(...attributes);
      }
      indices[f+2]=target;
    }
    const bounds=new Float32Array(expanded.length/4*7);
    for(let i=0;i<vertices.length/4;i++)bounds[i*7+3]=-1;
    bounds.set(inkBounds,vertices.length/4*7);
    gl.bindBuffer(gl.ARRAY_BUFFER,surface.vb);gl.bufferData(gl.ARRAY_BUFFER,new Uint16Array(expanded),gl.STATIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,shadeBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(shadeValues),gl.STATIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ARRAY_BUFFER,bounds,gl.STATIC_DRAW);
    gl.enableVertexAttribArray(4);gl.vertexAttribPointer(4,4,gl.FLOAT,false,28,0);
    gl.enableVertexAttribArray(5);gl.vertexAttribPointer(5,3,gl.FLOAT,false,28,16);
    facing.faces=indices;facing.compact=expanded.length/4<=65536;
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,surface.ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,indices,gl.STATIC_DRAW);
  }
  gl.bindVertexArray(null);
  let prepare=()=>{};
  if(mode==='group'||mode==='both'){
    // Bounds refer to original positions, even when colour attributes duplicate
    // a provoking vertex. Every vertex stays at exactly the same coordinate.
    const meshGroups=new Map(),limbs=['nearF','farF','nearH','farH'];
    const position=i=>{
      const x=meta.x0-385+vertices[i*4]/info.quantization*meta.sx;
      const y=vertices[i*4+1]/info.quantization*meta.height/128;
      const z=meta.z0+vertices[i*4+2]/info.quantization*meta.sz;
      const t=Math.max(0,Math.min(1,(y-54)/116));
      const contact=meta.poses[vertices[i*4+3]].feet[limbs[(x<35?0:2)+(z>0?0:1)]].contact;
      return [x,y,z,contact?meta.stride/meta.frames*(1-t*t*(3-2*t)):0];
    };
    // The pre-colour indices are needed only for startup bounds.
    const original=new Uint32Array(facing.faces.length);
    // Read the canonical triangle positions through the original provoking
    // mapping, retained by the shader-independent index ordering.
    const geo=geometryData;
    original.set(new Uint32Array(geo,info.vertexBytes));
    for(const pose of info.poses)for(const mesh of Object.values(pose)){
      const cells=new Map();
      for(let f=mesh.first;f<mesh.first+mesh.count;f+=3){
        const points=Array.from(original.subarray(f,f+3),position);
        const key=[0,1,2].map(k=>Math.floor(points.reduce((s,p)=>s+p[k],0)/3/64)).join('/');
        if(!cells.has(key))cells.set(key,[]);
        cells.get(key).push({f,points});
      }
      const groups=[];
      for(const list of cells.values())for(let start=0;start<list.length;start+=24){
        const group={faces:[],lo:[Infinity,Infinity,Infinity],hi:[-Infinity,-Infinity,-Infinity],
          normalLo:[Infinity,Infinity,Infinity],normalHi:[-Infinity,-Infinity,-Infinity],dMin:Infinity};
        for(const {f,points} of list.slice(start,start+24)){
          group.faces.push(f);
          for(const p of points)for(let k=0;k<3;k++){
            group.lo[k]=Math.min(group.lo[k],p[k]);
            group.hi[k]=Math.max(group.hi[k],p[k]+(k===0?p[3]:0));
          }
          for(let j=f/3*8;j<f/3*8+8;j+=4){
            for(let k=0;k<3;k++){
              group.normalLo[k]=Math.min(group.normalLo[k],facing.planes[j+k]);
              group.normalHi[k]=Math.max(group.normalHi[k],facing.planes[j+k]);
            }
            group.dMin=Math.min(group.dMin,facing.planes[j+3]);
          }
        }
        group.center=group.lo.map((v,k)=>(v+group.hi[k])/2);
        // Two canonical units and a world-space margin cover float roundoff.
        group.half=group.lo.map((v,k)=>(group.hi[k]-v)/2+2);
        groups.push(group);
      }
      meshGroups.set(mesh.first,groups);stats.groups+=groups.length;
    }
    let batchesByMesh,planes,unit;
    prepare=(batches,frustum,scale)=>{
      batchesByMesh=new Map([...batches.values()].map(b=>[info.poses[b.pose][b.level].first,b]));
      planes=frustum.planes;unit=scale;
      stats.groupsTested=stats.groupBack=stats.groupOutside=stats.trianglesBefore=stats.trianglesAfter=0;
    };
    const cache=new Map();let cacheBytes=0;
    facing.get=(mesh,eye)=>{
      const groupList=meshGroups.get(mesh.first),batch=batchesByMesh.get(mesh.first),places=batch.places;
      const flags=new Uint8Array(groupList.length),plane=facing.planes;
      const localPlanes=[];
      for(let j=0;j<places.length;j+=6){
        const x=places[j],z=places[j+1],c=places[j+2],s=places[j+3],local=[];
        for(const p of planes){
          const n=p.normal;
          local.push((n.x*c+n.z*s)*unit,n.y*unit,(-n.x*s+n.z*c)*unit,
            n.x*x*unit+n.z*z*unit+n.y*.034+p.constant);
        }
        localPlanes.push(local);
      }
      for(let n=0;n<groupList.length;n++){
        const group=groupList[n];stats.groupsTested++;
        let upper=-group.dMin;
        for(let k=0;k<3;k++)upper+=Math.max(
          group.normalLo[k]*eye[k]*512,group.normalLo[k]*eye[k+3]*512,
          group.normalHi[k]*eye[k]*512,group.normalHi[k]*eye[k+3]*512);
        if(upper < -2){flags[n]=1;stats.groupBack++;continue;}
        let outside=true;
        const [cx,cy,cz]=group.center,[hx,hy,hz]=group.half;
        for(const p of localPlanes){
          let rejected=false;
          for(let j=0;j<p.length;j+=4){
            const a=p[j],b=p[j+1],c=p[j+2];
            if(a*cx+b*cy+c*cz+p[j+3]+Math.abs(a)*hx+Math.abs(b)*hy+Math.abs(c)*hz<-.05){
              rejected=true;break;
            }
          }
          if(!rejected){outside=false;break;}
        }
        if(outside){flags[n]=1;stats.groupOutside++;}
      }
      const key=mesh.first+'/'+eye.join('/')+'/'+Array.from(flags).join('');
      let entry=cache.get(key);
      if(entry){cache.delete(key);cache.set(key,entry);}
      else{
        const kept=new Uint8Array(mesh.count/3);
        const center=eye.slice(0,3).map((v,k)=>(v+eye[k+3])*256);
        const half=eye.slice(0,3).map((v,k)=>(eye[k+3]-v)*256);
        for(let n=0;n<groupList.length;n++){
          if(flags[n])continue;
          // The existing triangle test runs only on groups that survived.
          for(const f of groupList[n].faces){
            for(let j=f/3*8;j<f/3*8+8;j+=4){
              const [nx,ny,nz,d]=plane.subarray(j,j+4);
              if(nx*center[0]+ny*center[1]+nz*center[2]-d+
                 Math.abs(nx)*half[0]+Math.abs(ny)*half[1]+Math.abs(nz)*half[2]>=-2){
                kept[(f-mesh.first)/3]=1;break;
              }
            }
          }
        }
        const indices=facing.compact?new Uint16Array(mesh.count):new Uint32Array(mesh.count);let size=0;
        for(let i=0;i<kept.length;i++)if(kept[i]){
          indices.set(facing.faces.subarray(mesh.first+i*3,mesh.first+i*3+3),size);size+=3;
        }
        const ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,indices.subarray(0,size),gl.STATIC_DRAW);
        entry={ib,count:size,type:facing.compact?gl.UNSIGNED_SHORT:gl.UNSIGNED_INT,bytes:size*indices.BYTES_PER_ELEMENT};
        cache.set(key,entry);cacheBytes+=entry.bytes;
        while(cacheBytes>8*1024*1024&&cache.size>1){
          const first=cache.keys().next().value,drop=cache.get(first);
          gl.deleteBuffer(drop.ib);cache.delete(first);cacheBytes-=drop.bytes;
        }
      }
      stats.trianglesBefore+=mesh.count/3*places.length/6;
      stats.trianglesAfter+=entry.count/3*places.length/6;
      return entry;
    };
  }
  return {prepare,shader(vs,fs){
    if(mode!=='color'&&mode!=='both')return [vs,fs];
    vs=vs.replace('void main(){',`layout(location=4) in vec4 inkLo;
layout(location=5) in vec3 inkHi;
flat out vec4 constantLo;
flat out vec3 constantHi;
void main(){constantLo=inkLo;constantHi=inkHi;`);
    fs=fs.replace('void main(){','flat in vec4 constantLo;flat in vec3 constantHi;\nvoid main(){')
      .replace('int ink=int(texelFetch(paint,at,0).r*255.+.5);',`int ink;
 bool stable=faceShade>0. && 2.*fwidth(gl_FragCoord.w)<gl_FragCoord.w;
 if(stable && constantLo.w>=0. && all(greaterThanEqual(vec3(cell),constantLo.xyz)) && all(lessThanEqual(vec3(cell),constantHi))){
   ink=int(constantLo.w);
 }else{ink=int(texelFetch(paint,at,0).r*255.+.5);}`);
    return [vs,fs];
  }};
}
