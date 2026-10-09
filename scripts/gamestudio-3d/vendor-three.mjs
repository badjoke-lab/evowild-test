// Supply a clean official npm three@0.181.0 directory; do not silently upgrade.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
const source = process.argv[2];
if (!source) throw new Error('Usage: node scripts/gamestudio-3d/vendor-three.mjs /path/to/node_modules/three');
const pkg = JSON.parse(await fs.readFile(path.join(source, 'package.json')));
if (pkg.version !== '0.181.0') throw new Error('This lane is pinned to Three.js 0.181.0');
const dest = 'public/preview-motion-first/vendor/three';
const files = ['LICENSE','build/three.module.js','build/three.core.js','examples/jsm/loaders/GLTFLoader.js','examples/jsm/utils/SkeletonUtils.js','examples/jsm/utils/BufferGeometryUtils.js'];
const manifest = {package:'three',version:pkg.version,source:'https://registry.npmjs.org/three/-/three-0.181.0.tgz',files:[]};
for (const file of files) {
  const data=await fs.readFile(path.join(source,file));
  await fs.mkdir(path.dirname(path.join(dest,file)),{recursive:true});
  await fs.writeFile(path.join(dest,file),data);
  manifest.files.push({path:file,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')});
}
await fs.writeFile(path.join(dest,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify(manifest,null,2));
