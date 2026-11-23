import {program} from '../renderer.js';
import {PaintedSurface,vertex,fragment} from '../v3/surface.js';
import {VisibleIndices} from './indices.js';

// Directional lighting divides by the L1 norm, which also cancels the
// Euclidean normalization of the cross product used in v3.
const lit=fragment.replace('normalize(cross(dFdx(grid*stepSize),dFdy(grid*stepSize)))',
                           'cross(dFdx(grid*stepSize),dFdy(grid*stepSize))');
const solidFragment=lit.replace('if(cover<1. && threshold()<1.-cover)discard;', '');
export class Surface extends PaintedSurface {
 static index=new URL('./assets/index.json',import.meta.url);
 static geometry=new URL('./assets/geometry.gz',import.meta.url);
 static fragment=lit;
 async load(){
  await super.load();
  this.solid=program(this.gl,vertex,solidFragment);this.configure(this.solid);
  this.facing=new VisibleIndices(this.gl,this.facing,this.info.vertexBytes/8);
 }
 draw(batches,use,drift){
  if(!batches.size)return 0;
  const g=this.gl,lists=[[],[]];let n=0,triangles=0;
  for(const b of batches.values()){
   let partial=false;
   for(let i=5;i<b.places.length;i+=6)if(b.places[i]<1){partial=true;break;}
   b.offset=n*4;this.scratch.set(b.places,n);n+=b.places.length;lists[Number(partial)].push(b);
  }
  g.activeTexture(g.TEXTURE2);g.bindTexture(g.TEXTURE_2D_ARRAY,this.paint);
  g.bindVertexArray(this.vao);g.bindBuffer(g.ARRAY_BUFFER,this.instances);
  g.bufferSubData(g.ARRAY_BUFFER,0,this.scratch,0,n);
  for(let i=0;i<lists.length;i++){
   if(!lists[i].length)continue;
   const pass=i?this.pass:this.solid;use(pass);g.uniform1f(pass.u.drift,drift);
   for(const b of lists[i]){
    const mesh=this.info.poses[b.pose][b.level],slice=b.direction==null?null:this.facing.get(mesh,b.direction);
    g.vertexAttribPointer(1,4,g.FLOAT,false,24,b.offset);g.vertexAttribPointer(2,2,g.FLOAT,false,24,b.offset+16);
    g.bindBuffer(g.ELEMENT_ARRAY_BUFFER,slice?slice.ib:this.ib);
    const size=slice?slice.count:mesh.count;
    g.drawElementsInstanced(g.TRIANGLES,size,slice?.type??g.UNSIGNED_INT,slice?0:mesh.first*4,b.places.length/6);
    triangles+=size/3*b.places.length/6;
   }
  }
  g.activeTexture(g.TEXTURE0);g.bindVertexArray(null);return triangles;
 }
}
