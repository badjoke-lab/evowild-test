# D3-C actual scapula-authoring experiment — unapproved
Original S skinned GLB has 21 joints and no independent scapular controls.
This candidate has 23 skinned joints (real left/right scapula), shoulder-adjacent skin weights
transferred from chest, and two native-cycle rotation channels. Existing upper-arm
translation keys are rebased to preserve the original bind/world locations.
- Original reference: \`?rig=contact-v3&toe=roll-v3&body=push-v5\`.
- New authored rig: \`?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v1\`.
- Neutral rig control: \`?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=neutral-v1\`.
- Five real WebGL videos from SIDE, FRONT, CHASE, LOW, REAR_3_4 (original versus authored).
- Full-cycle PNGs and desktop/Pixel7 emulated screenshots.
- Original model, manifest, unrelated lanes, branch PR#132 and main untouched.
- Numerical checks do not imply a visually acceptable gallop. Subjective visual gate remains **REVISE**.
