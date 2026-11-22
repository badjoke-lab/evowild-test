// Offline-only topology-aware collapse. Locked vertices retain the four feet,
// paired crest and tip extents found from the source occupancy bands.
import fs from 'node:fs';
import {MeshoptSimplifier} from 'meshoptimizer';

const [vertices, indices, ...targets] = process.argv.slice(2).map(Number);
const input = new Uint8Array(fs.readFileSync(0)).buffer;
const positions = new Float32Array(input, 0, vertices * 3);
const faces = new Uint32Array(input, positions.byteLength, indices);
const locks = new Uint8Array(input, positions.byteLength + faces.byteLength);
await MeshoptSimplifier.ready;
for (const target of targets) {
  const [mesh] = MeshoptSimplifier.simplifyWithAttributes(
    faces, positions, 3, new Float32Array(0), 0, [], locks, target * 3, 1
  );
  const count = Buffer.alloc(4);
  count.writeUInt32LE(mesh.length);
  fs.writeSync(1, count);
  fs.writeSync(1, Buffer.from(mesh.buffer, mesh.byteOffset, mesh.byteLength));
}
