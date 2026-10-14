# 3D P model recovery — separate v7b candidate, original Codex v8 unavailable

**Source:** intact `P-v7-reference-retopology.blend` and authoritative `public/concept/P.webp`, no v8 files were accessible. The local v8 commit `cc1dab8` was not on GitHub; its original files remain unavailable. **This new work is NOT a recovery or equivalent reproduction of that v8.**

Because the linked Codex exec-server rejects process startup, the rescue build is executed on GitHub Actions using Blender 4.3.2. It edits genuine polygon mesh vertices on the saved v7 static model (shoulder/scapula/pectoral surface and root tail cage). The tail is attempted as an exact static boolean union and accepted only if connected and manifold. If it cannot be joined, it is exported separately and the unresolved root remains explicitly documented.

Files: `art/p-creature/workspaces/P-v7b-rescue-static.blend`, `public/models/evowild-p/p-canonical-v7b-rescue.glb`, five genuinely re-imported GLB renders, comparison and validation. This experiment is **not rigged, not animated, not approved**, and not merged into production or the previous 3D development branch. v1–v7, main, canonical P reference, S/E/A and 2.5D remain untouched.

**Outcome must be reviewed by actual image.** The build being successful alone says nothing about anatomical match. If no meaningful improvement, REJECT the v7b model but keep the rescue process reproducible.
