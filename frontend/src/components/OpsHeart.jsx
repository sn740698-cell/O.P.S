// Ops Heart — animated red/black/white/gray plasma brain (WebGL shader in a React component).
// Autonomous cognitive core of O.P.S.

import React, { useRef, useEffect, useState } from 'react';
import { Activity, Zap, Sparkles } from 'lucide-react';
import { retroSoundEngine } from '../utils/retroSounds';

const VERT = `attribute vec2 a; void main(){ gl_Position = vec4(a,0.,1.); }`;

const FRAG = `
precision highp float;
uniform vec2 uRes; uniform float uT; uniform vec2 uRot; uniform vec3 uClick;

float hash(vec3 p){ p = fract(p*0.3183099+.1); p *= 17.; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float noise(vec3 x){
  vec3 i = floor(x), f = fract(x); f = f*f*(3.-2.*f);
  return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x), mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
             mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x), mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y), f.z);
}
mat3 rotY(float a){ float c=cos(a), s=sin(a); return mat3(c,0,-s, 0,1,0, s,0,c); }
mat3 rotX(float a){ float c=cos(a), s=sin(a); return mat3(1,0,0, 0,c,s, 0,-s,c); }

void main(){
  vec2 p = (gl_FragCoord.xy - .5*uRes) / min(uRes.x, uRes.y);
  float t = uT;
  float beat = pow(max(0.,sin(t*1.7)),14.) + .6*pow(max(0.,sin(t*1.7-.8)),14.);
  float shock = exp(-pow((length(p-uClick.xy)-uClick.z*.7)/.07, 2.)) * exp(-uClick.z*1.1);
  mat3 R = rotY(uRot.x + t*.08) * rotX(uRot.y + .25);
  const int N = 56;
  float dz = 2.0 / float(N);
  float jit = hash(vec3(gl_FragCoord.xy, 1.0));
  vec3 col = vec3(0.);
  float T = 1.0;

  for(int i=0;i<N;i++){
    float z = 1.0 - (float(i)+jit)*dz;
    vec3 q = R * vec3(p, z);
    float d = length(q);
    if(abs(d-.5) > .2) continue;
    vec3 dir = q / d;

    // breathing, lumpy silhouette
    float lump = (noise(dir*2.0 + vec3(t*.12, 0., t*.08)) - .5) * .16
               + (noise(dir*4.5 - vec3(0., t*.2, 0.)) - .5) * .05;
    float Rd = .5 + lump + .012*sin(t*1.3) + .018*beat + .03*shock;
    float w = exp(-pow((d-Rd)/.04, 2.));
    if(w < .01) continue;

    // domain-warped ridged noise = glowing filaments
    vec3 s = dir*2.6;
    vec3 wp = s + .55*vec3(noise(s*1.3+vec3(t*.10,0,3.)), noise(s*1.3+vec3(7.,t*.12,0.)), noise(s*1.3+vec3(0.,5.,t*.09)));
    float r1 = 1. - abs(2.*noise(wp*1.4 + vec3(0., t*.15, 0.)) - 1.);
    float r2 = 1. - abs(2.*noise(wp*3.2 - vec3(t*.18, 0., 0.)) - 1.);
    float vein = pow(r1, 9.) + .45*pow(r2, 12.);

    // travelling electric pulses
    float pulse = pow(noise(dir*3.0 + vec3(0., 0., -t*.9)), 6.) * 3.0;
    float e = vein * (1.0 + pulse + beat*.9 + shock*4.);

    float haze = .06 + .18*noise(dir*3. + t*.05);
    vec3 grey = vec3(.42,.43,.46);
    vec3 red  = mix(vec3(.30,0.,.02), vec3(1.,.07,.1), clamp(e,0.,1.));
    vec3 white = vec3(1.,.93,.93) * pow(clamp(e,0.,1.), 3.);
    vec3 c = grey*haze + red*e*1.6 + white*1.4;

    col += T * c * w * dz * 9.0;
    T *= exp(-w*dz*2.2);
  }

  // outer glow + background
  float rr = length(p);
  vec3 bg = mix(vec3(.07,.07,.075), vec3(0.), smoothstep(0., .8, rr));
  float glow = exp(-pow(max(rr-.42, 0.)*5.0, 1.4));
  bg += vec3(.30,.02,.03) * glow * .22;

  col += vec3(.55,.03,.05) * exp(-pow(rr/.2, 2.)) * (.12 + .25*beat);

  // drifting embers
  vec3 em = vec3(0.);
  for(int L=0; L<3; L++){
    float fl = float(L);
    vec2 g = p*(9.+fl*6.) + vec2(sin(t*.2+fl)*.8, -t*(.18+fl*.08));
    vec2 cell = floor(g); float rn = hash(vec3(cell, fl+2.));
    vec2 off = fract(g) - .5 - (vec2(hash(vec3(cell,9.)), hash(vec3(cell,4.))) - .5)*.6;
    float dot_ = smoothstep(.07, 0., length(off)) * step(.9, rn) * (.5+.5*sin(t*2.+rn*40.));
    em += mix(vec3(.8,.08,.1), vec3(1.), rn) * dot_ * (.5 - fl*.1);
  }
  vec3 outc = bg + col + em*.6;
  outc = 1. - exp(-outc*1.3);          // tone map
  outc = pow(outc, vec3(.95));
  outc *= 1. - .55*smoothstep(.45, 1.0, rr);
  outc += (hash(vec3(gl_FragCoord.xy, floor(t*30.))) - .5) * .025;
  gl_FragColor = vec4(outc, 1.);
}
`;

export default function OpsHeart({ className = "" }) {
  const ref = useRef(null);
  const [err, setErr] = useState(false);
  const [shockwaveCount, setShockwaveCount] = useState(0);

  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;

    const gl = cv.getContext('webgl', { antialias: false, powerPreference: 'high-performance' });
    if (!gl) {
      setErr(true);
      return;
    }

    const sh = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    };

    const pr = gl.createProgram();
    gl.attachShader(pr, sh(gl.VERTEX_SHADER, VERT));
    gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(pr);
    gl.useProgram(pr);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(pr, 'a');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(pr, 'uRes');
    const uT = gl.getUniformLocation(pr, 'uT');
    const uRot = gl.getUniformLocation(pr, 'uRot');
    const uClick = gl.getUniformLocation(pr, 'uClick');

    const resize = () => {
      if (!cv) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      const width = Math.max(32, Math.floor(cv.clientWidth * dpr));
      const height = Math.max(32, Math.floor(cv.clientHeight * dpr));
      cv.width = width;
      cv.height = height;
      gl.viewport(0, 0, cv.width, cv.height);
    };

    resize();
    window.addEventListener('resize', resize);

    const ro = new ResizeObserver(() => {
      resize();
    });
    ro.observe(cv);

    let rx = 0, ry = 0, drag = false, lx = 0, ly = 0, sx = 0, sy = 0, cx = 0, cy = 0, ct = -99;

    const down = (e) => {
      drag = true;
      lx = sx = e.clientX;
      ly = sy = e.clientY;
      cv.style.cursor = 'grabbing';
    };

    const up = (e) => {
      if (drag && Math.hypot(e.clientX - sx, e.clientY - sy) < 6) {
        const r = cv.getBoundingClientRect();
        const m = Math.min(r.width, r.height);
        cx = (e.clientX - r.left - r.width / 2) / m;
        cy = -(e.clientY - r.top - r.height / 2) / m;
        ct = performance.now();
        setShockwaveCount(prev => prev + 1);
        try {
          retroSoundEngine.playKeystrokeBeep();
        } catch {}
      }
      drag = false;
      cv.style.cursor = 'grab';
    };

    const move = (e) => {
      if (!drag) return;
      rx += (e.clientX - lx) * 0.008;
      ry += (e.clientY - ly) * 0.008;
      lx = e.clientX;
      ly = e.clientY;
    };

    cv.addEventListener('pointerdown', down);
    window.addEventListener('pointerup', up);
    window.addEventListener('pointermove', move);

    let raf;
    const t0 = performance.now();

    const frame = (now) => {
      gl.uniform2f(uRes, cv.width, cv.height);
      gl.uniform1f(uT, (now - t0) / 1000);
      gl.uniform3f(uClick, cx, cy, (now - ct) / 1000);
      gl.uniform2f(uRot, rx, Math.max(-1.2, Math.min(1.2, ry)));
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      raf = requestAnimationFrame(frame);
    };

    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      ro.disconnect();
      window.removeEventListener('pointerup', up);
      window.removeEventListener('pointermove', move);
    };
  }, []);

  return (
    <div className={`retro-box-red p-2 flex flex-col justify-between shadow-xl relative overflow-hidden bg-black font-mono select-none ${className}`}>
      {/* Scanline HUD Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-1 mb-1 z-10 bg-black/80 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <span className="px-1.5 py-0.5 bg-red-600 text-white font-extrabold text-[9px] tracking-wider border border-red-500 shadow-sm animate-pulse">
            OPS HEART
          </span>
        </div>
      </div>

      {/* WebGL Shader Brain Container */}
      <div className="relative w-full flex-1 min-h-[135px] rounded border border-zinc-900 overflow-hidden bg-[#030303] group">
        {err ? (
          <div className="h-full flex items-center justify-center text-xs text-zinc-500 p-3 text-center">
            WebGL is not supported in this environment.
          </div>
        ) : (
          <canvas
            ref={ref}
            className="w-full h-full block"
            style={{ touchAction: 'none', cursor: 'grab', background: '#030303' }}
            title="O.P.S. Heart — Drag to rotate in 3D, click/tap to fire synaptic shockwave"
          />
        )}

        {/* Ambient CRT Vignette Overlay */}
        <div className="absolute inset-0 pointer-events-none border border-red-950/40 rounded shadow-[inset_0_0_20px_rgba(239,68,68,0.2)]" />
        
        {/* Subtle HUD crosshairs in corners */}
        <div className="absolute top-1 left-1 text-[7px] text-red-500/60 font-mono pointer-events-none">⌜ 45°N</div>
        <div className="absolute top-1 right-1 text-[7px] text-red-500/60 font-mono pointer-events-none">SYN-01 ⌝</div>
        <div className="absolute bottom-1 left-1 text-[7px] text-zinc-600 font-mono pointer-events-none">⌞ O.P.S.</div>
        <div className="absolute bottom-1 right-1 text-[7px] text-red-500/70 font-mono pointer-events-none">
          {shockwaveCount > 0 ? `PULSES: ${shockwaveCount} ⌟` : `READY ⌟`}
        </div>
      </div>

      {/* Bottom Telemetry Bar */}
      <div className="flex items-center justify-between text-[8px] text-zinc-500 pt-1 mt-1 border-t border-zinc-900 z-10">
        <span className="flex items-center gap-1 text-zinc-400">
          <Activity className="w-2.5 h-2.5 text-red-500 animate-pulse" />
          <span>HOMEOSTASIS: OPTIMAL</span>
        </span>
        <span className="text-zinc-500 uppercase tracking-tight">
          [ 3D PULSE ]
        </span>
      </div>
    </div>
  );
}
