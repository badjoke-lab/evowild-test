// Appended by the evidence runner only; never shipped/executed by the game.
// Reads the actual articulated proxy transforms, not the solver's target-slip metric.
window.__gameStudioProbe = () => {
  const point = new THREE.Vector3();
  const feet = [];
  for (const runner of runners) {
    const root = runner.raceProxy;
    if (!root) continue;
    for (const [index, leg] of root.userData.legs.entries()) {
      point.setFromMatrixPosition(leg.footPart.matrixWorld);
      let soleY = Infinity;
      for (const [part, geometry] of [[leg.footPart, proxyFootGeometry], ...leg.toes.map(t => [t, proxyToeGeometry])]) {
        geometry.computeBoundingBox();
        const box = geometry.boundingBox;
        for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
          soleY = Math.min(soleY, new THREE.Vector3(x, y, z).applyMatrix4(part.matrixWorld).y);
        }
      }
      feet.push({id: runner.id, morph: runner.morph, leg: index, stance: leg.stanceActive,
        cycle: Math.floor((root.userData.phase + runner.phaseBias + leg.phaseOffset) / (Math.PI * 2)),
        x: point.x, z: point.z, soleWorldY: soleY, soleClearance: soleY});
    }
  }
  return {
    time: performance.now(), raceTime, paused, requestedCamera, actualCamera,
    focus: selectedRunner, rank: rankings().findIndex(r => r.id === selectedRunner) + 1,
    runners: runners.map(r => ({id:r.id, morph:r.morph, distance:r.distance, speed:r.speed})),
    feet, calls: renderer.info.render.calls, triangles: renderer.info.render.triangles,
    colorVersions: Object.fromEntries(Object.entries(simplifiedRaceProxyPool || {}).map(([key, mesh]) => [key, mesh.instanceColor?.version])),
    colors: Object.fromEntries(Object.entries(simplifiedRaceProxyPool || {}).map(([key, mesh]) => [key, Array.from(mesh.instanceColor?.array || []).reduce((sum, value, i) => sum + value * (i + 1), 0)])),
    dataset: {...canvas.dataset}
  };
};
