export const COUNTS = [1, 10, 50, 100];

export function createGpuTimer(gl) {
  const ext = gl.getExtension('EXT_disjoint_timer_query_webgl2');
  const pending = [];
  return {
    available: !!ext,
    begin() {
      if (!ext || pending.length >= 6) return null;
      const query = gl.createQuery();
      if (query) gl.beginQuery(ext.TIME_ELAPSED_EXT, query);
      return query;
    },
    end(query, callback) {
      if (!query) return;
      gl.endQuery(ext.TIME_ELAPSED_EXT);
      pending.push({ query, callback });
    },
    poll() {
      if (!ext || !pending.length) return;
      if (gl.getParameter(ext.GPU_DISJOINT_EXT)) {
        for (const { query } of pending.splice(0)) gl.deleteQuery(query);
        return;
      }
      while (pending.length && gl.getQueryParameter(pending[0].query, gl.QUERY_RESULT_AVAILABLE)) {
        const { query, callback } = pending.shift();
        const ms = gl.getQueryParameter(query, gl.QUERY_RESULT) / 1e6;
        gl.deleteQuery(query);
        if (ms > 0) callback(ms);
      }
    }
  };
}

function percentile(values, q) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted.length ? sorted[Math.ceil(sorted.length * q) - 1] : null;
}

export function summarize(frames, gpu, durationMs) {
  const frameMs = frames.map(frame => frame.frameMs);
  const last = frames.at(-1);
  return {
    durationMs, frames: frames.length,
    fps: frames.length ? frames.length / (frameMs.reduce((sum, ms) => sum + ms, 0) / 1000) : null,
    p95FrameMs: percentile(frameMs, .95),
    cpuSubmitMedianMs: percentile(frames.map(frame => frame.cpuMs), .5),
    gpuMedianMs: percentile(gpu, .5), gpuP95Ms: percentile(gpu, .95), gpuSamples: gpu.length,
    pointCount: last?.points, drawCalls: last?.calls, triangles: last?.triangles,
    renderWidth: last?.width, renderHeight: last?.height,
    gpuBufferEstimateBytes: last?.gpuBufferEstimateBytes,
    jsHeapUsedBytes: performance.memory?.usedJSHeapSize ?? null
  };
}

export function geometryBytes(geometry) {
  const buffers = new Set(Object.values(geometry.attributes).map(attribute => attribute.array));
  if (geometry.index) buffers.add(geometry.index.array);
  return [...buffers].reduce((total, array) => total + array.byteLength, 0);
}

export function sceneGeometryBytes(scene) {
  const geometries = new Set();
  let bytes = 0;
  scene.traverse(object => {
    if (!object.geometry) return;
    geometries.add(object.geometry);
    bytes += (object.instanceMatrix?.array.byteLength ?? 0) + (object.instanceColor?.array.byteLength ?? 0);
  });
  return bytes + [...geometries].reduce((sum, geometry) => sum + geometryBytes(geometry), 0);
}
