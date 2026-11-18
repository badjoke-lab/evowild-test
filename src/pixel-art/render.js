import * as THREE from 'three';
import { FOG, SKY, SUN } from './landscape.js';
import { MESH_LAYER, POINT_LAYER } from './subjects.js';

const palette = [
  '#172922', '#465d42', '#698362', '#9aaa90', '#c6d0aa', '#796b57', '#b28f73', '#e0d2b4',
  '#2a4033', '#354e40', '#536b50', '#65704b', '#77835b', '#a6a775', '#6f7d72', '#b6c3bb',
  '#3d4443', '#586260', '#858f89', '#a6afaa', '#392c2a', '#564838', '#8b7965', '#f4ede0',
  '#566753', '#5e7560', '#849b80', '#bbc5a4', '#4a514a', '#947f73', '#c7ab89', '#f6e0be'
].map(value => {
  const { r, g, b } = new THREE.Color(value);
  return new THREE.Vector3(Math.sqrt(r), Math.sqrt(g), Math.sqrt(b));
});

export function makePointMaterial(mesh, vertices) {
  return new THREE.ShaderMaterial({
    glslVersion: THREE.GLSL3,
    uniforms: {
      uVertices: { value: vertices }, uBones: { value: mesh.skeleton.boneTexture },
      uBind: { value: mesh.bindMatrix }, uInverseBind: { value: mesh.bindMatrixInverse },
      uSun: { value: SUN }, uSky: { value: SKY }, uFog: { value: FOG }, uShading: { value: .65 },
      uSize: { value: .024 }, uViewport: { value: new THREE.Vector2() },
      uPointLimit: { value: 64 }, uGaussian: { value: false },
      uRadial: { value: false }, uHybrid: { value: false },
      uWorldDepth: { value: null }, uMeshDepth: { value: null }, uRange: { value: new THREE.Vector2() }
    },
    vertexShader: `
      in vec2 sampleUV;
      uniform highp sampler2D uVertices, uBones;
      uniform mat4 uBind, uInverseBind;
      uniform vec3 uSun, uSky;
      uniform float uShading, uSize, uPointLimit, uFog;
      uniform vec2 uViewport;
      uniform bool uGaussian, uHybrid;
      out vec3 vColor;
      out vec3 vInverseCovariance;
      out float vDepth;
      out float vDiameter;

      vec4 vertexData(int address) {
        return texelFetch(uVertices, ivec2(address % 256, address / 256), 0);
      }
      mat4 bone(int index) {
        int width = textureSize(uBones, 0).x;
        int start = index * 4;
        ivec2 p = ivec2(start % width, start / width);
        return mat4(texelFetch(uBones, p, 0), texelFetch(uBones, p + ivec2(1, 0), 0),
          texelFetch(uBones, p + ivec2(2, 0), 0), texelFetch(uBones, p + ivec2(3, 0), 0));
      }
      vec3 deform(float vertexId) {
        int address = int(vertexId) * 3;
        vec4 source = uBind * vertexData(address);
        ivec4 joints = ivec4(vertexData(address + 1));
        vec4 weights = vertexData(address + 2);
        vec4 transformed = weights.x * (bone(joints.x) * source);
        if (weights.y > 0.0) transformed += weights.y * (bone(joints.y) * source);
        if (weights.z > 0.0) transformed += weights.z * (bone(joints.z) * source);
        if (weights.w > 0.0) transformed += weights.w * (bone(joints.w) * source);
        return (uInverseBind * transformed).xyz;
      }
      vec2 projectOffset(vec4 at, vec3 axis) {
        vec4 d = projectionMatrix * vec4(mat3(modelViewMatrix) * axis, 0.0);
        // First-order perspective projection of the surface covariance.
        return (d.xy - at.xy * d.w / at.w) * uViewport * (0.5 / at.w);
      }
      void main() {
        vec3 a = deform(position.x);
        vec3 b = deform(position.y);
        vec3 c = deform(position.z);
        vec3 point = a + (b - a) * sampleUV.x + (c - a) * sampleUV.y;
        vec3 surfaceNormal = normalize(cross(b - a, c - a));
        vec4 view = modelViewMatrix * vec4(point, 1.0);
        vDepth = -view.z;
        gl_Position = projectionMatrix * view;
        // A small clip-depth offset separates surface points from the mesh underlay.
        if (uHybrid) gl_Position.z -= 0.00001 * gl_Position.w;
        vec3 normal = normalize(mat3(modelMatrix) * surfaceNormal);
        float bright = 0.28 + 1.42 * max(dot(normal, uSun), 0.0) + 0.20 * normal.y;
        vec3 lit = vec3(0.33, 0.35, 0.36) * mix(1.0, bright, uShading);
        float fog = 1.0 - exp(-uFog * uFog * view.z * view.z);
        vColor = mix(lit, uSky, fog);

        float projected = uViewport.y * projectionMatrix[1][1] * uSize / max(0.15, vDepth);
        vInverseCovariance = vec3(0.0);
        float requested = projected;
        if (uGaussian && vDepth > 0.15) {
          vec3 tangent = normalize(b - a);
          vec3 bitangent = cross(surfaceNormal, tangent);
          float localSize = uSize / length(modelMatrix[0].xyz);
          vec2 p = projectOffset(gl_Position, tangent * localSize * 0.52);
          vec2 q = projectOffset(gl_Position, bitangent * localSize * 0.46);
          vec2 n = projectOffset(gl_Position, surfaceNormal * localSize * 0.11);
          float xx = dot(vec3(p.x, q.x, n.x), vec3(p.x, q.x, n.x)) + 0.24;
          float yy = dot(vec3(p.y, q.y, n.y), vec3(p.y, q.y, n.y)) + 0.24;
          float xy = p.x * p.y + q.x * q.y + n.x * n.y;
          vInverseCovariance = vec3(yy, -xy, xx) / (xx * yy - xy * xy);
          requested = 5.6 * sqrt(max(xx, yy));
        }
        vDiameter = clamp(requested, uGaussian ? 3.0 : 1.0, uPointLimit);
        gl_PointSize = vDiameter;
      }`,
    fragmentShader: `
      uniform bool uGaussian, uRadial;
      uniform highp sampler2D uWorldDepth, uMeshDepth;
      uniform vec2 uRange;
      uniform float uSize;
      in vec3 vColor;
      in vec3 vInverseCovariance;
      in float vDepth;
      in float vDiameter;
      out vec4 fragmentColor;

      float viewDistance(float depth) {
        return uRange.x * uRange.y / (uRange.y - depth * (uRange.y - uRange.x));
      }
      void main() {
        vec2 p = gl_PointCoord - 0.5;
        if (uGaussian) {
          ivec2 pixel = ivec2(gl_FragCoord.xy);
          float world = viewDistance(texelFetch(uWorldDepth, pixel, 0).r);
          float surface = viewDistance(texelFetch(uMeshDepth, pixel, 0).r);
          if (vDepth > world + 0.01 || vDepth > surface + max(0.025, uSize * 1.55)) discard;
          p *= vec2(vDiameter, -vDiameter);
          float quadratic = dot(vInverseCovariance, vec3(p.x * p.x, 2.0 * p.x * p.y, p.y * p.y));
          if (quadratic > 7.84) discard;
          float alphaWeight = exp(-0.5 * quadratic);
          fragmentColor = vec4(vColor * alphaWeight, alphaWeight);
        } else {
          if (dot(p, p) > 0.25) discard;
          // Opaque isotropic Gaussian tonal profile; no alpha accumulation or depth sort.
          float shade = uRadial ? mix(0.68, 1.15, exp(-8.0 * dot(p, p))) : 1.0;
          fragmentColor = linearToOutputTexel(vec4(vColor * shade, 1.0));
        }
      }`
  });
}

function target(depth, type = THREE.UnsignedByteType) {
  return new THREE.WebGLRenderTarget(1, 1, {
    type,
    minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter,
    depthBuffer: depth, depthTexture: depth ? new THREE.DepthTexture(1, 1, THREE.UnsignedIntType) : null
  });
}

export function createRenderPipeline(renderer, scene, camera) {
  const gl = renderer.getContext();
  const pointLimit = gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE)[1];
  const canGaussian = pointLimit >= 3 && !!gl.getExtension('EXT_color_buffer_float');
  const color = target(true);
  const meshDepth = canGaussian ? target(true) : null;
  const accum = canGaussian ? target(false, THREE.HalfFloatType) : null;
  const depthMaterial = new THREE.MeshDepthMaterial({ colorWrite: false });
  const display = new THREE.Scene();
  const screenCamera = new THREE.Camera();
  const tri = new THREE.BufferGeometry();
  tri.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  const post = new THREE.ShaderMaterial({
    uniforms: {
      uColor: { value: color.texture }, uDepth: { value: color.depthTexture },
      uMeshDepth: { value: meshDepth?.depthTexture ?? color.depthTexture },
      uAccum: { value: accum?.texture ?? color.texture }, uGaussian: { value: false },
      uPalette: { value: palette }, uColors: { value: 24 }, uOutline: { value: .60 },
      uRange: { value: new THREE.Vector2(camera.near, camera.far) }, uStep: { value: new THREE.Vector2() }
    },
    depthTest: false, depthWrite: false,
    vertexShader: `varying vec2 vUV;
      void main() { vUV = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
    fragmentShader: `
      uniform sampler2D uColor, uDepth, uMeshDepth, uAccum;
      uniform vec3 uPalette[32];
      uniform bool uGaussian;
      uniform int uColors;
      uniform float uOutline;
      uniform vec2 uStep, uRange;
      varying vec2 vUV;
      float depthAt(vec2 uv) {
        float d = texture2D(uDepth, uv).r;
        if (uGaussian) d = min(d, texture2D(uMeshDepth, uv).r);
        return uRange.x * uRange.y / (uRange.y - d * (uRange.y - uRange.x));
      }
      void main() {
        vec3 rgb = texture2D(uColor, vUV).rgb;
        if (uGaussian) {
          vec4 splats = texture2D(uAccum, vUV);
          rgb = mix(rgb, splats.rgb / max(splats.a, 0.001), 1.0 - exp(-splats.a * 2.0));
        }
        float d = depthAt(vUV);
        float front = min(min(depthAt(vUV + vec2(uStep.x, 0.0)), depthAt(vUV - vec2(uStep.x, 0.0))),
          min(depthAt(vUV + vec2(0.0, uStep.y)), depthAt(vUV - vec2(0.0, uStep.y))));
        float threshold = 0.24 + front * 0.026;
        float edge = smoothstep(threshold, threshold * 1.65, d - front);
        rgb *= 1.0 - edge * uOutline * 0.73;
        vec3 perceptual = sqrt(max(rgb, 0.0));
        vec3 chosen = uPalette[0];
        float nearest = 99.0;
        for (int i = 0; i < 32; i++) {
          if (i >= uColors) break;
          vec3 diff = perceptual - uPalette[i];
          float error = dot(diff * diff, vec3(0.29, 0.52, 0.19));
          if (error < nearest) { nearest = error; chosen = uPalette[i]; }
        }
        gl_FragColor = vec4(chosen * chosen, 1.0);
        #include <colorspace_fragment>
      }`
  });
  const screen = new THREE.Mesh(tri, post);
  screen.frustumCulled = false;
  display.add(screen);
  const viewport = new THREE.Vector2();

  function draw(settings, subjects) {
    const gaussian = settings.mode === 'D';
    const radial = settings.mode === 'E' || settings.mode === 'F';
    const hybrid = settings.mode === 'F';
    const pixelated = settings.mode === 'C' || gaussian || radial;
    renderer.getDrawingBufferSize(viewport);
    if (pixelated) {
      viewport.set(Math.max(1, Math.round(viewport.x * settings.resolution / 100)),
        Math.max(1, Math.round(viewport.y * settings.resolution / 100)));
    }
    const { x: width, y: height } = viewport;
    if (settings.mode !== 'A') {
      scene.updateMatrixWorld(true);
      for (const { mesh, points } of subjects) {
        mesh.skeleton.update();
        const mat = points.material;
        const uniforms = mat.uniforms;
        uniforms.uSize.value = settings.size / 1000;
        uniforms.uShading.value = settings.shading / 100;
        uniforms.uViewport.value.copy(viewport);
        uniforms.uPointLimit.value = pointLimit;
        uniforms.uGaussian.value = gaussian;
        uniforms.uRadial.value = radial;
        uniforms.uHybrid.value = hybrid;
        uniforms.uWorldDepth.value = gaussian ? color.depthTexture : null;
        uniforms.uMeshDepth.value = gaussian ? meshDepth.depthTexture : null;
        uniforms.uRange.value.set(camera.near, camera.far);
        mat.depthTest = !gaussian;
        mat.depthWrite = !gaussian;
        mat.blending = gaussian ? THREE.CustomBlending : THREE.NoBlending;
        mat.blendEquation = THREE.AddEquation;
        mat.blendSrc = THREE.OneFactor;
        mat.blendDst = THREE.OneFactor;
        // WebGLRenderer disables blending for opaque NormalBlending, but honours CustomBlending.
        points.geometry.setDrawRange(0, settings.density);
      }
    }
    renderer.info.reset();
    camera.layers.set(0);
    if (settings.mode === 'A') camera.layers.enable(MESH_LAYER);
    else if (!gaussian) {
      camera.layers.enable(POINT_LAYER);
      if (hybrid) camera.layers.enable(MESH_LAYER);
    }
    if (!pixelated) {
      renderer.setRenderTarget(null);
      renderer.render(scene, camera);
      return { width, height, targetBytes: 0 };
    }
    color.setSize(width, height);
    renderer.setRenderTarget(color);
    renderer.render(scene, camera);
    if (gaussian) {
      const background = scene.background;
      scene.background = null;
      meshDepth.setSize(width, height);
      camera.layers.set(MESH_LAYER);
      scene.overrideMaterial = depthMaterial;
      renderer.setRenderTarget(meshDepth);
      renderer.render(scene, camera);
      scene.overrideMaterial = null;
      accum.setSize(width, height);
      camera.layers.set(POINT_LAYER);
      renderer.setRenderTarget(accum);
      renderer.setClearColor(0, 0);
      renderer.render(scene, camera);
      scene.background = background;
    }
    post.uniforms.uStep.value.set(1 / width, 1 / height);
    post.uniforms.uColors.value = settings.colors;
    post.uniforms.uOutline.value = settings.outline / 100;
    post.uniforms.uGaussian.value = gaussian;
    renderer.setRenderTarget(null);
    renderer.render(display, screenCamera);
    return { width, height, targetBytes: width * height * (gaussian ? 24 : 8) };
  }

  return { draw, canGaussian, pointLimit };
}
