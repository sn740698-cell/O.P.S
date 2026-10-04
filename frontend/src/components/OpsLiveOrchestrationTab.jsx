import React, { useState, useEffect, useRef } from 'react';
import {
  Play, Loader2, Globe, Terminal, Cpu, Activity, Info
} from 'lucide-react';
import { retroSoundEngine } from '../utils/retroSounds';

// ==================== O.P.S. MULTI-AGENT ARCHITECTURE TOPOLOGY ====================

// 5 Hierarchical Stages:
// Layer 0: Sensory Inputs (2 nodes: Hotkey/CLI, Wispr Voice)
// Layer 1: Fast Gateway & Memory (2 nodes: Supervisor Router, Workstation Vector Memory)
// Layer 2: Cognitive Core (2 nodes: Reasoning & DAG Planner, Safety Sentinel)
// Layer 3: Autonomous Action Fleet (6 nodes: Direct Tools, Developer, Crawler, Browser DOM, Desktop Automation, Content Writer)
// Layer 4: Executive Voice & Synthesis (1 node: J.A.R.V.I.S. Persona)
const LAYERS = [2, 2, 2, 6, 1];
const LAST = LAYERS.length - 1;
const LABELS = [
  "STAGE 01: SENSORY",
  "STAGE 02: GATEWAY & RAG",
  "STAGE 03: COGNITIVE CORE",
  "STAGE 04: ACTION FLEET",
  "STAGE 05: EXECUTIVE VOICE"
];

// Exact Agent Metadata matching O.P.S. architecture
const AGENT_NODES = [
  // Layer 0: Sensory Inputs
  [
    {
      id: "input_text",
      name: "Directive & Hotkey Ingestion",
      tag: "INPUT: KEY / CLI",
      model: "Win32 API (Ctrl+Alt / Terminal)",
      task: "Captures global hotkeys, shell directives, and workstation keystrokes without minimizing active windows.",
      category: "sensor",
      matchKeys: ["input", "user", "hotkey", "prompt", "cli", "cockpit", "desktop", "overlay", "directive", "sensory"]
    },
    {
      id: "input_voice",
      name: "Wispr Voice Dictation",
      tag: "INPUT: VOICE",
      model: "Wispr Flow Acoustic Stream (Ctrl+Win)",
      task: "Real-time acoustic listener streaming workstation microphone audio and wake directives ('Hey OPS').",
      category: "sensor",
      matchKeys: ["voice", "audio", "mic", "wispr", "dictation", "speech"]
    }
  ],
  // Layer 1: Fast Gateway & Memory
  [
    {
      id: "router",
      name: "Supervisor Router Node",
      tag: "FAST ROUTER",
      model: "Qwen3 0.6B (Local Ollama)",
      task: "Sub-50ms intent detection & parameter extraction. Bypasses heavy models for simple actions and routes complex tasks.",
      category: "router",
      matchKeys: ["router", "supervisor", "intent", "classify"]
    },
    {
      id: "memory",
      name: "Workstation Vector Memory",
      tag: "SEMANTIC RAG",
      model: "ChromaDB (all-MiniLM-L6-v2 384-d)",
      task: "Indexes conversation turns, codebase symbols, and user preferences locally with zero cloud data leakage.",
      category: "memory",
      matchKeys: ["memory", "vector", "chroma", "rag"]
    }
  ],
  // Layer 2: Cognitive Core
  [
    {
      id: "planner",
      name: "Reasoning & DAG Planner",
      tag: "DAG PLANNER",
      model: "Qwen3 1.7B (Local Ollama)",
      task: "Performs deep chain-of-thought task decomposition, builds ordered dependency DAGs, and oversees error recovery.",
      category: "cognitive",
      matchKeys: ["reasoning", "planner", "plan", "decompose", "dag"]
    },
    {
      id: "safety",
      name: "Safety Policy Sentinel",
      tag: "HITL SENTINEL",
      model: "Win32 Sandbox Gatekeeper",
      task: "Intercepts high-risk operations (file writes, app execution, terminal commands) and enforces mandatory human approval.",
      category: "security",
      matchKeys: ["safety", "permission", "gatekeeper", "sentinel"]
    }
  ],
  // Layer 3: Autonomous Action Fleet
  [
    {
      id: "direct_tool",
      name: "Direct Tool Runner",
      tag: "DIRECT TOOL",
      model: "OPS Native Sandbox (Sub-10ms)",
      task: "Instantly launches apps, manages directories, or runs calculator math without LLM overhead.",
      category: "action",
      matchKeys: ["tool", "direct", "open ", "launch", "calc"]
    },
    {
      id: "developer",
      name: "Autonomous Developer Agent",
      tag: "DEV AGENT",
      model: "Qwen3 1.7B (Local Ollama)",
      task: "Queries codebase context, generates code, fixes syntax errors, and validates execution in the sandboxed shell.",
      category: "action",
      matchKeys: ["developer", "dev", "code", "syntax", "refactor", "git"]
    },
    {
      id: "crawler",
      name: "Live Web Crawling Agent",
      tag: "WEB CRAWLER",
      model: "Crawlee 1.10 + ScrapeGraphAI",
      task: "Crawls web documentation, extracts LLM-ready markdown, and searches live information (person bios, theories, news).",
      category: "action",
      matchKeys: ["crawl", "crawlee", "scrape", "search", "who is", "news"]
    },
    {
      id: "browser",
      name: "Browser DOM Agent",
      tag: "PLAYWRIGHT DOM",
      model: "Playwright Headless/Headed",
      task: "Automates browser navigation, DOM button clicks, video searches (YouTube), and dynamic site interactions (Instagram).",
      category: "action",
      matchKeys: ["browser", "playwright", "instagram", "youtube", "dom"]
    },
    {
      id: "automation",
      name: "System Automation Agent",
      tag: "DESKTOP GUI",
      model: "PyAutoGUI + Win32 API",
      task: "Controls desktop GUI windows, clicks screen coordinates, simulates keystrokes, and switches active windows.",
      category: "action",
      matchKeys: ["automation", "gui", "pyautogui", "desktop", "window"]
    },
    {
      id: "writer",
      name: "Content Writer Agent",
      tag: "CONTENT WRITER",
      model: "Llama 3.2 1B Instruct (Local Ollama)",
      task: "Drafts formal emails, summaries, structured notes, and documents with clean tone and coherent structure.",
      category: "action",
      matchKeys: ["content", "writer", "email", "summary", "draft"]
    }
  ],
  // Layer 4: Executive Voice & Synthesis
  [
    {
      id: "jarvis",
      name: "J.A.R.V.I.S. Persona Synthesizer",
      tag: "JARVIS SYNTHESIZER",
      model: "Llama 3.2 1B Instruct + Piper Neural Voice",
      task: "Translates multi-agent tool telemetry into calm, dignified J.A.R.V.I.S. briefings formatted in '90s retro bullets.",
      category: "output",
      matchKeys: ["jarvis", "synthesizer", "response", "speech", "tts"]
    }
  ]
];

// Canvas Neural Parameters
const TRAVEL = 800; // ms for an action potential to cross one gap
const TAU = Math.PI * 2;
const F = 6; // fine filaments per connection

const sigmoid = (x) => 1 / (1 + Math.exp(-x));
const randn = () => Math.sqrt(-2 * Math.log(1 - Math.random())) * Math.cos(TAU * Math.random());
const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));

// Helper: match which node corresponds to the activeAgent string
function findActiveNode(agentStr) {
  if (!agentStr) return null;
  const lower = agentStr.toLowerCase();
  for (let l = 0; l < AGENT_NODES.length; l++) {
    for (let i = 0; i < AGENT_NODES[l].length; i++) {
      const node = AGENT_NODES[l][i];
      if (node.matchKeys.some((k) => lower.includes(k))) {
        return { l, i, node };
      }
    }
  }
  return null;
}

export default function OpsLiveOrchestrationTab({
  activeAgent,
  currentThought,
  planSteps,
  isLoading,
  onDispatchPrompt,
  briefingText
}) {
  const [quickInput, setQuickInput] = useState('');
  const [, setActiveTaskQuery] = useState('');

  // Hover state for interactive HUD popup
  const [hoveredAgent, setHoveredAgent] = useState(null);

  // Canvas DOM refs
  const wrapRef = useRef(null);
  const canvasRef = useRef(null);
  const triggerPulseRef = useRef(null);

  // Automatically trigger synaptic pulse waves when a task starts or active agent transitions
  useEffect(() => {
    if (isLoading && triggerPulseRef.current) {
      triggerPulseRef.current();
    }
  }, [isLoading, activeAgent]);

  const handleQuickDispatch = (e) => {
    if (e) e.preventDefault();
    if (!quickInput.trim() || isLoading) return;
    setActiveTaskQuery(quickInput);
    if (onDispatchPrompt) onDispatchPrompt(quickInput);
    if (triggerPulseRef.current) triggerPulseRef.current();
    setQuickInput('');
  };

  const handleTestFlow = (prompt) => {
    setActiveTaskQuery(prompt);
    if (onDispatchPrompt) onDispatchPrompt(prompt);
    if (triggerPulseRef.current) triggerPulseRef.current();
  };

  // ==================== NEURAL CANVAS LIVING GRAPH ====================
  useEffect(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;
    const ctx = canvas.getContext("2d");

    // Weights: layer l to layer l+1
    const W = LAYERS.slice(1).map((n, l) =>
      Array.from({ length: n }, () =>
        Array.from({ length: LAYERS[l] }, () => randn() * Math.sqrt(2 / LAYERS[l]) * 1.3)
      )
    );
    const B = LAYERS.map((n) => Array.from({ length: n }, () => 0.15 + Math.random() * 0.2));

    // Organic axon shapes
    const C = LAYERS.slice(1).map((n, l) =>
      Array.from({ length: n }, () =>
        Array.from({ length: LAYERS[l] }, () => ({
          bend: (Math.random() - 0.5) * 24,
          ph: Math.random() * TAU,
          ph2: Math.random() * TAU,
          f: 1.2 + Math.random() * 1.1,
          sp: 0.0006 + Math.random() * 0.0005,
          b0: Math.random(),
          bs: 0.5 + Math.random(),
          dp: 0.6 + Math.random() * 0.4,
          hue: Math.random(),
          st: Array.from({ length: F }, (_, n) => ({
            k: (n / (F - 1) - 0.5) * 3.6 + (Math.random() - 0.5) * 0.5,
            ph: Math.random() * TAU,
            sp: 0.0004 + Math.random() * 0.0008,
            gl: Math.random(),
          })),
        }))
      )
    );

    const act = LAYERS.map((n) => new Array(n).fill(0));
    const glow = LAYERS.map((n) => new Array(n).fill(0));
    const heat = LAYERS.slice(1).map((n, l) =>
      Array.from({ length: n }, () => new Array(LAYERS[l]).fill(0))
    );

    // Cross-links matching O.P.S real-time architecture:
    const ARCHITECTURAL_CROSS_LINKS = [
      { l1: 1, i: 0, l2: 3, j: 0, bow: -35, f: 1.4, sp: 0.0007, ph: 0.5, hue: 0.1 }, // Router -> Direct Tool
      { l1: 1, i: 0, l2: 3, j: 5, bow: 40, f: 1.2, sp: 0.0006, ph: 1.2, hue: 0.2 },  // Router -> Writer
      { l1: 0, i: 0, l2: 1, j: 1, bow: 25, f: 1.5, sp: 0.0008, ph: 2.1, hue: 0.3 },  // Key Input -> Memory
      { l1: 0, i: 1, l2: 1, j: 1, bow: 20, f: 1.3, sp: 0.0007, ph: 0.8, hue: 0.4 },  // Voice Input -> Memory
      { l1: 2, i: 1, l2: 3, j: 1, bow: -25, f: 1.1, sp: 0.0006, ph: 3.0, hue: 0.5 }, // Sentinel -> Dev Agent
      { l1: 2, i: 1, l2: 3, j: 4, bow: 30, f: 1.2, sp: 0.0005, ph: 1.8, hue: 0.6 },  // Sentinel -> Desktop Auto
      { l1: 4, i: 0, l2: 1, j: 1, bow: 65, f: 0.9, sp: 0.0005, ph: 2.7, hue: 0.7 },  // Jarvis -> Memory context
    ];

    const G = [...ARCHITECTURAL_CROSS_LINKS];

    let nodes = [];
    let radius = 15;
    let width = 0;
    let height = 0;
    let pulses = [];
    let pm = new Map();
    let timers = [];
    let waves = [];
    let hover = null;
    let mouse = { x: -999, y: -999 };
    let raf;
    let last = performance.now();

    const layout = () => {
      const rect = wrap.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = Math.max(rect.height, 580);
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const maxLayerCount = Math.max(...LAYERS);
      const gap = Math.min(74, (height * 0.72) / maxLayerCount);
      radius = Math.max(13, Math.min(18, gap * 0.28));
      const padX = Math.max(70, width * 0.11);

      nodes = LAYERS.map((n, l) =>
        Array.from({ length: n }, (_, i) => ({
          bx: padX + ((width - padX * 2) * l) / LAST,
          by: height / 2 + 16 + (i - (n - 1) / 2) * gap,
          x: 0,
          y: 0,
          ph: Math.random() * TAU,
        }))
      );
    };

    const pointAt = (l, j, i, s, t, k = 0) => {
      const A = nodes[l][i];
      const Bn = nodes[l + 1][j];
      const c = C[l][j][i];
      const dx = (Bn.x - A.x) * 0.5;
      const x1 = A.x + dx, y1 = A.y, x2 = Bn.x - dx, y2 = Bn.y;
      const u = 1 - s;
      const x = u * u * u * A.x + 3 * u * u * s * x1 + 3 * u * s * s * x2 + s * s * s * Bn.x;
      const y = u * u * u * A.y + 3 * u * u * s * y1 + 3 * u * s * s * y2 + s * s * s * Bn.y;
      let tx = 3 * u * u * (x1 - A.x) + 6 * u * s * (x2 - x1) + 3 * s * s * (Bn.x - x2);
      let ty = 3 * u * u * (y1 - A.y) + 6 * u * s * (y2 - y1) + 3 * s * s * (Bn.y - y2);
      const m = Math.hypot(tx, ty) || 1;
      tx /= m; ty /= m;
      const h = heat[l][j][i];
      const env = Math.pow(Math.sin(Math.PI * s), 0.8);
      const wave =
        Math.sin(TAU * c.f * s - t * c.sp * 6 + c.ph) +
        0.45 * Math.sin(TAU * c.f * 2.3 * s - t * c.sp * 9 + c.ph2);
      let boost = 0;
      const ps = pm.get(l * 10000 + j * 100 + i);
      if (ps) for (const q of ps) { const d = (s - q.e) / 0.14; boost += q.s * Math.exp(-d * d); }
      const breathe = 1 + 0.25 * Math.sin(t * 0.0007 + c.ph);
      let off = env * ((2.0 * breathe + h * 5 + boost * 4) * wave + c.bend * Math.sin(Math.PI * s));
      if (k) off += env * k * 4 * (1 + h) * Math.sin(TAU * c.f * 1.6 * s - t * c.sp * 8 + c.ph2 * k + k * 2);
      return [x - ty * off, y + tx * off];
    };

    const prog = (t) => t * t * (3 - 2 * t);

    const ghostPoint = (g, sv, t, k) => {
      const A = nodes[g.l1][g.i], Bn = nodes[g.l2][g.j];
      const dx = Bn.x - A.x, dy = Bn.y - A.y;
      const len = Math.hypot(dx, dy) || 1;
      const u = 1 - sv;
      const x1 = A.x + dx * 0.33 + g.bow, y1 = A.y + dy * 0.33;
      const x2 = Bn.x - dx * 0.33 + g.bow, y2 = Bn.y - dy * 0.33;
      const x = u * u * u * A.x + 3 * u * u * sv * x1 + 3 * u * sv * sv * x2 + sv * sv * sv * Bn.x;
      const y = u * u * u * A.y + 3 * u * u * sv * y1 + 3 * u * sv * sv * y2 + sv * sv * sv * Bn.y;
      const env = Math.sin(Math.PI * sv);
      const off = env * (3.0 * Math.sin(TAU * g.f * sv - t * g.sp * 6 + g.ph + k) + k * 3);
      return [x - (dy / len) * off, y + (dx / len) * off];
    };

    // Vivid Crimson & Tactical Silver Synaptic Colors
    const tint = (hue, h) => {
      const base = mix([235, 45, 60], [255, 140, 160], hue);
      return mix(base, [255, 255, 255], Math.min(1, h * 0.7)).join(",");
    };

    const startWave = (now) => {
      const wave = {
        input: Array.from({ length: LAYERS[0] }, () => 0.8),
        values: LAYERS.map((n) => new Array(n).fill(0)),
        pending: LAYERS.map((n, l) => new Array(n).fill(l === 0 ? 0 : LAYERS[l - 1])),
      };
      waves.push(wave);
      wave.input.forEach((_, i) => timers.push({ t: now + 20 + Math.random() * 60, wave, l: 0, i }));
    };

    triggerPulseRef.current = () => {
      startWave(performance.now());
    };

    const fire = (wave, l, i, now) => {
      const z = wave.values[l][i] + B[l][i];
      const a = l === 0 ? wave.input[i] : l === LAST ? sigmoid(z) : Math.max(0, z);
      act[l][i] = a;
      glow[l][i] = Math.min(1, a / (l === LAST ? 1 : 1.1));
      if (l === LAST) return;
      for (let j = 0; j < LAYERS[l + 1]; j++) {
        pulses.push({
          wave,
          l,
          i,
          j,
          born: now + Math.random() * 30,
          dur: TRAVEL * (0.85 + Math.random() * 0.2),
          v: a * W[l][j][i]
        });
      }
    };

    // Frame Loop
    const frame = (now) => {
      const dt = Math.min(now - last, 50);
      last = now;

      // Identify currently executing agent (defaults to Fast Router if generic orchestrating)
      const activeTarget = findActiveNode(activeAgent) || (isLoading ? { l: 1, i: 0, node: AGENT_NODES[1][0] } : null);
      const isSystemWorking = Boolean(isLoading && activeTarget);

      // ACTIVE WORKING LOGIC: Continuous streams when working
      if (isSystemWorking && activeTarget) {
        glow[activeTarget.l][activeTarget.i] = 1.0;
        act[activeTarget.l][activeTarget.i] = 1.0;

        if (Math.random() < 0.25) {
          const l = activeTarget.l;
          const i = activeTarget.i;
          if (l < LAST) {
            const j = Math.floor(Math.random() * LAYERS[l + 1]);
            pulses.push({
              amb: true,
              wave: null,
              l,
              i,
              j,
              born: now,
              dur: TRAVEL * 0.85,
              v: 0.5 + Math.random() * 0.3
            });
          }
        }
      }

      // Gentle organic drift of nodes
      nodes.forEach((layer) =>
        layer.forEach((n) => {
          n.x = n.bx + Math.sin(now * 0.0006 + n.ph) * 1.5;
          n.y = n.by + Math.cos(now * 0.0005 + n.ph * 1.3) * 2.0;
        })
      );

      // Timers for wave execution
      timers = timers.filter((tm) => {
        if (now < tm.t) return true;
        fire(tm.wave, tm.l, tm.i, now);
        return false;
      });

      // Pulses
      pulses = pulses.filter((p) => {
        if (now - p.born < p.dur) return true;
        if (p.amb) {
          heat[p.l][p.j][p.i] = Math.max(heat[p.l][p.j][p.i], 0.35);
          return false;
        }
        const { wave, l, j } = p;
        heat[l][j][p.i] = Math.min(1, Math.abs(p.v) * 1.5 + 0.3);
        wave.values[l + 1][j] += p.v;
        if (--wave.pending[l + 1][j] === 0) {
          timers.push({ t: now + 20 + Math.random() * 60, wave, l: l + 1, i: j });
        }
        return false;
      });

      pm = new Map();
      for (const p of pulses) {
        const t = (now - p.born) / p.dur;
        if (t < 0 || t > 1) continue;
        const key = p.l * 10000 + p.j * 100 + p.i;
        const q = { e: prog(t), s: Math.min(1, Math.abs(p.v) * 1.6 + 0.2) };
        const arr = pm.get(key);
        arr ? arr.push(q) : pm.set(key, [q]);
      }
      waves = waves.filter((w) => w.pending.some((row, l) => l > 0 && row.some((c) => c > 0)));

      // Glow decay
      const decayRate = isSystemWorking ? 520 : 250;
      const gd = Math.exp(-dt / decayRate);
      const hd = Math.exp(-dt / 400);
      glow.forEach((r) => r.forEach((_, i) => (r[i] *= gd)));
      heat.forEach((a) => a.forEach((r) => r.forEach((_, i) => (r[i] *= hd))));

      // Hover check
      hover = null;
      let activeHoverNodeMeta = null;
      nodes.forEach((layer, l) =>
        layer.forEach((n, i) => {
          if (Math.hypot(n.x - mouse.x, n.y - mouse.y) < radius + 8) {
            hover = { l, i };
            if (AGENT_NODES[l] && AGENT_NODES[l][i]) {
              activeHoverNodeMeta = {
                ...AGENT_NODES[l][i],
                layerIdx: l,
                nodeIdx: i,
                x: n.x,
                y: n.y,
                activation: act[l][i]
              };
            }
          }
        })
      );
      setHoveredAgent(activeHoverNodeMeta);

      // ==================== DRAWING ====================
      ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = "#050508";
      ctx.fillRect(0, 0, width, height);

      // Radial backdrop
      const bg = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, Math.max(width, height) * 0.6);
      bg.addColorStop(0, "rgba(75, 10, 20, 0.22)");
      bg.addColorStop(1, "rgba(4, 4, 6, 0.98)");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);

      // Cybernetic grid lines
      ctx.strokeStyle = "rgba(45, 45, 55, 0.22)";
      ctx.lineWidth = 1;
      const step = 48;
      for (let gx = 0; gx < width; gx += step) {
        ctx.beginPath();
        ctx.moveTo(gx, 0);
        ctx.lineTo(gx, height);
        ctx.stroke();
      }
      for (let gy = 0; gy < height; gy += step) {
        ctx.beginPath();
        ctx.moveTo(0, gy);
        ctx.lineTo(width, gy);
        ctx.stroke();
      }

      // Draw Main Synaptic Connections (Filament Bundles) - CLEARLY VISIBLE!
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.globalCompositeOperation = "lighter";
      const SEG = 24;

      for (let l = 0; l < LAST; l++) {
        for (let j = 0; j < LAYERS[l + 1]; j++) {
          for (let i = 0; i < LAYERS[l]; i++) {
            const h = heat[l][j][i];
            const c = C[l][j][i];
            const related = hover && ((hover.l === l && hover.i === i) || (hover.l === l + 1 && hover.i === j));
            const isPathActive = isSystemWorking && activeTarget && ((activeTarget.l === l && activeTarget.i === i) || (activeTarget.l === l + 1 && activeTarget.i === j));
            
            // Clean, clearly visible base alpha
            const rgb = tint(c.hue, h);
            const baseAlpha = isPathActive ? 0.8 : related ? 0.6 : 0.22;
            const amp = baseAlpha + h * 0.45;

            for (const st of c.st) {
              const pts = [];
              for (let q = 0; q <= SEG; q++) pts.push(pointAt(l, j, i, q / SEG, now, st.k));
              const shimmer = 0.75 + 0.25 * Math.sin(now * st.sp * 3 + st.ph);
              ctx.strokeStyle = `rgba(${rgb}, ${Math.min(0.95, amp * shimmer)})`;
              ctx.lineWidth = isPathActive ? 1.2 : related ? 0.9 : 0.65;
              ctx.beginPath();
              pts.forEach(([x, y], q) => (q ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
              ctx.stroke();

              // Moving glint along axon
              const i0 = Math.floor(((now * 0.00012 * (1 + st.gl) + st.gl) % 1) * (SEG - 5));
              ctx.strokeStyle = `rgba(${rgb}, ${Math.min(0.9, amp * 2.8 * shimmer)})`;
              ctx.lineWidth = isPathActive ? 1.8 : 1.1;
              ctx.beginPath();
              for (let q = i0; q <= i0 + 4; q++) {
                q === i0 ? ctx.moveTo(pts[q][0], pts[q][1]) : ctx.lineTo(pts[q][0], pts[q][1]);
              }
              ctx.stroke();
            }
          }
        }
      }

      // Draw Architectural Cross-Links (Clearly visible skip connections)
      for (const g of G) {
        if (!nodes[g.l1] || !nodes[g.l1][g.i] || !nodes[g.l2] || !nodes[g.l2][g.j]) continue;
        const related = hover && ((hover.l === g.l1 && hover.i === g.i) || (hover.l === g.l2 && hover.i === g.j));
        const isPathActive = isSystemWorking && activeTarget && ((activeTarget.l === g.l1 && activeTarget.i === g.i) || (activeTarget.l === g.l2 && activeTarget.i === g.j));
        const rgb = tint(g.hue, 0.25);
        const alpha = isPathActive ? 0.75 : related ? 0.55 : 0.20;

        ctx.strokeStyle = `rgba(${rgb}, ${alpha})`;
        ctx.lineWidth = isPathActive ? 1.0 : 0.65;
        ctx.beginPath();
        for (let q = 0; q <= SEG; q++) {
          const [x, y] = ghostPoint(g, q / SEG, now, 0);
          q ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
        }
        ctx.stroke();
      }

      // Draw Travelling Action Potentials (Sparks)
      ctx.globalCompositeOperation = "lighter";
      for (const p of pulses) {
        const t = (now - p.born) / p.dur;
        if (t < 0) continue;
        const e = prog(t);
        const s = Math.min(1, Math.abs(p.v) * 1.6 + 0.2);
        const M = 9;
        const s0 = Math.max(0, e - 0.24);
        let prev = pointAt(p.l, p.j, p.i, s0, now);
        for (let k = 1; k <= M; k++) {
          const cur = pointAt(p.l, p.j, p.i, s0 + ((e - s0) * k) / M, now);
          ctx.strokeStyle = `rgba(255, 240, 240, ${s * (k / M) * (k / M)})`;
          ctx.lineWidth = 1.2 + s * 1.6 * (k / M);
          ctx.beginPath();
          ctx.moveTo(prev[0], prev[1]);
          ctx.lineTo(cur[0], cur[1]);
          ctx.stroke();
          prev = cur;
        }
        const halo = ctx.createRadialGradient(prev[0], prev[1], 0, prev[0], prev[1], 9);
        halo.addColorStop(0, `rgba(255, 245, 245, ${0.9 * s})`);
        halo.addColorStop(1, "rgba(235, 30, 45, 0)");
        ctx.fillStyle = halo;
        ctx.beginPath();
        ctx.arc(prev[0], prev[1], 9, 0, TAU);
        ctx.fill();
      }

      ctx.globalCompositeOperation = "source-over";

      // ==================== AGENT NODES RENDERING (VIBRANT & HIGH CONTRAST) ====================
      for (let l = 0; l < LAYERS.length; l++) {
        for (let i = 0; i < LAYERS[l]; i++) {
          const n = nodes[l][i];
          const isNodeActive = isSystemWorking && activeTarget && activeTarget.l === l && activeTarget.i === i;
          const isHovered = hover && hover.l === l && hover.i === i;
          const r = radius * (isNodeActive ? 1.2 : 1.0);

          // 1. ACTIVE WORKING BLOOM GLOW: ONLY WHEN WORKING!
          if (isNodeActive) {
            ctx.globalCompositeOperation = "lighter";
            const bloomRadius = r * 4.8;
            const bloom = ctx.createRadialGradient(n.x, n.y, r * 0.2, n.x, n.y, bloomRadius);
            bloom.addColorStop(0, "rgba(255, 70, 90, 0.95)");
            bloom.addColorStop(0.35, "rgba(239, 68, 68, 0.55)");
            bloom.addColorStop(1, "rgba(225, 29, 46, 0)");
            ctx.fillStyle = bloom;
            ctx.beginPath();
            ctx.arc(n.x, n.y, bloomRadius, 0, TAU);
            ctx.fill();
            ctx.globalCompositeOperation = "source-over";

            // Animated pulsing beacon reticle for working agent
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.8 + 0.2 * Math.sin(now * 0.009)})`;
            ctx.lineWidth = 2.0;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 6 + Math.sin(now * 0.008) * 3, 0, TAU);
            ctx.stroke();
          }

          // 2. TACTICAL HOVER RETICLE
          if (isHovered && !isNodeActive) {
            ctx.strokeStyle = "rgba(255, 255, 255, 0.95)";
            ctx.lineWidth = 1.6;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 4, 0, TAU);
            ctx.stroke();
          }

          // 3. NODE SPHERE BODY (RICH, CRISP, VISIBLE RUBY-CRIMSON)
          if (isNodeActive) {
            // Working State: Electrified White-Hot Neon Core
            const body = ctx.createRadialGradient(n.x - r * 0.25, n.y - r * 0.25, r * 0.05, n.x, n.y, r);
            body.addColorStop(0, "rgb(255, 245, 248)");
            body.addColorStop(0.35, "rgb(255, 80, 100)");
            body.addColorStop(1, "rgb(190, 12, 28)");
            ctx.fillStyle = body;
            ctx.strokeStyle = "rgb(255, 200, 210)";
            ctx.lineWidth = 2.0;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, TAU);
            ctx.fill();
            ctx.stroke();

            // Specular Glint
            ctx.fillStyle = "#ffffff";
            ctx.beginPath();
            ctx.arc(n.x - r * 0.3, n.y - r * 0.3, r * 0.28, 0, TAU);
            ctx.fill();
          } else {
            // Standby State: Distinct, Vibrant Polished Ruby Sphere (NOT DARK / NOT INVISIBLE!)
            const body = ctx.createRadialGradient(n.x - r * 0.35, n.y - r * 0.35, r * 0.08, n.x, n.y, r);
            body.addColorStop(0, isHovered ? "rgb(240, 50, 75)" : "rgb(175, 25, 42)");
            body.addColorStop(0.5, isHovered ? "rgb(185, 25, 42)" : "rgb(115, 12, 22)");
            body.addColorStop(1, isHovered ? "rgb(100, 10, 18)" : "rgb(55, 5, 10)");
            ctx.fillStyle = body;
            ctx.strokeStyle = isHovered ? "rgb(255, 120, 140)" : "rgba(244, 63, 94, 0.85)";
            ctx.lineWidth = isHovered ? 2.0 : 1.6;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, TAU);
            ctx.fill();
            ctx.stroke();

            // Crisp Specular Glint
            ctx.fillStyle = isHovered ? "rgba(255, 255, 255, 0.9)" : "rgba(255, 255, 255, 0.75)";
            ctx.beginPath();
            ctx.arc(n.x - r * 0.3, n.y - r * 0.3, r * 0.22, 0, TAU);
            ctx.fill();
          }

          // 4. CRISP HIGH-CONTRAST TACTICAL BADGE UNDER EACH NODE (100% VISIBLE!)
          const agentMeta = AGENT_NODES[l]?.[i];
          if (agentMeta) {
            const tagText = agentMeta.tag;
            ctx.font = "bold 10px 'JetBrains Mono', 'Geist Mono', monospace";
            const textMetrics = ctx.measureText(tagText);
            const pillW = textMetrics.width + 12;
            const pillH = 17;
            const pillX = n.x - pillW / 2;
            const pillY = n.y + r + 6;

            // Translucent glass pill background
            ctx.fillStyle = isNodeActive
              ? "rgba(220, 20, 40, 0.95)"
              : isHovered
              ? "rgba(35, 8, 14, 0.92)"
              : "rgba(16, 16, 22, 0.88)";
            ctx.strokeStyle = isNodeActive
              ? "#ffffff"
              : isHovered
              ? "#ef4444"
              : "rgba(239, 68, 68, 0.65)";
            ctx.lineWidth = 1;
            ctx.fillRect(pillX, pillY, pillW, pillH);
            ctx.strokeRect(pillX, pillY, pillW, pillH);

            // High contrast text
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = isNodeActive ? "#ffffff" : isHovered ? "#ffffff" : "#f4f4f5";
            ctx.fillText(tagText, n.x, pillY + pillH / 2);
          }
        }
      }

      // ==================== STAGE HEADER TITLES (TOP OF CANVAS) ====================
      const stageY = 46;
      LABELS.forEach((t, l) => {
        if (nodes[l] && nodes[l][0]) {
          const colX = nodes[l][0].bx;
          ctx.font = "bold 10px 'JetBrains Mono', 'Geist Mono', monospace";
          const titleWidth = ctx.measureText(t).width;
          const badgeW = titleWidth + 14;
          const badgeH = 18;

          // Header Badge
          ctx.fillStyle = "rgba(14, 14, 20, 0.9)";
          ctx.strokeStyle = "rgba(239, 68, 68, 0.45)";
          ctx.lineWidth = 1;
          ctx.fillRect(colX - badgeW / 2, stageY - badgeH / 2, badgeW, badgeH);
          ctx.strokeRect(colX - badgeW / 2, stageY - badgeH / 2, badgeW, badgeH);

          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillStyle = "#fca5a5";
          ctx.fillText(t, colX, stageY);
        }
      });

      // Canvas Tooltip Render for Hovered Agent
      if (hover && AGENT_NODES[hover.l]?.[hover.i]) {
        const meta = AGENT_NODES[hover.l][hover.i];
        const n = nodes[hover.l][hover.i];
        const isHoverActive = isSystemWorking && activeTarget && activeTarget.l === hover.l && activeTarget.i === hover.i;

        const badgeW = 175;
        const badgeH = 36;
        const boxX = Math.max(10, Math.min(width - badgeW - 10, n.x - badgeW / 2));
        const boxY = Math.max(10, n.y - radius - badgeH - 12);

        ctx.fillStyle = "rgba(5, 5, 8, 0.95)";
        ctx.strokeStyle = isHoverActive ? "#ef4444" : "#f43f5e";
        ctx.lineWidth = 1.4;
        ctx.fillRect(boxX, boxY, badgeW, badgeH);
        ctx.strokeRect(boxX, boxY, badgeW, badgeH);

        ctx.textAlign = "left";
        ctx.font = "bold 10px 'JetBrains Mono', 'Geist Mono', monospace";
        ctx.fillStyle = "#ffffff";
        ctx.fillText(meta.name.slice(0, 24), boxX + 8, boxY + 12);

        ctx.font = "9px 'JetBrains Mono', 'Geist Mono', monospace";
        ctx.fillStyle = isHoverActive ? "#ef4444" : "#fca5a5";
        ctx.fillText(`⚡ ${meta.model.slice(0, 26)}`, boxX + 8, boxY + 25);
      }

      raf = requestAnimationFrame(frame);
    };

    const ro = new ResizeObserver(layout);
    ro.observe(wrap);
    layout();
    raf = requestAnimationFrame(frame);

    const onMove = (e) => {
      const r = canvas.getBoundingClientRect();
      const mx = e.clientX - r.left;
      const my = e.clientY - r.top;
      mouse = { x: mx, y: my };
    };
    const onLeave = () => {
      mouse = { x: -999, y: -999 };
      setHoveredAgent(null);
    };
    const onDown = (e) => {
      const r = canvas.getBoundingClientRect();
      const mx = e.clientX - r.left;
      const my = e.clientY - r.top;

      let clickedNode = null;
      nodes.forEach((layer, l) =>
        layer.forEach((n, i) => {
          if (Math.hypot(n.x - mx, n.y - my) < radius + 10) {
            clickedNode = { l, i };
          }
        })
      );

      const now = performance.now();
      if (clickedNode) {
        retroSoundEngine.playKeyClick();
        glow[clickedNode.l][clickedNode.i] = 1.0;
        act[clickedNode.l][clickedNode.i] = 1.0;
        if (clickedNode.l < LAST) {
          for (let j = 0; j < LAYERS[clickedNode.l + 1]; j++) {
            pulses.push({
              wave: null,
              amb: true,
              l: clickedNode.l,
              i: clickedNode.i,
              j,
              born: now,
              dur: TRAVEL * 0.85,
              v: 0.6
            });
          }
        }
      } else {
        retroSoundEngine.playKeyClick();
        startWave(now);
      }
    };

    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerleave", onLeave);
    canvas.addEventListener("pointerdown", onDown);

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerleave", onLeave);
      canvas.removeEventListener("pointerdown", onDown);
    };
  }, [activeAgent, isLoading]);

  // Identify active agent coordinates for UI indicators
  const activeAgentNode = findActiveNode(activeAgent);

  return (
    <div className="space-y-4 font-mono select-none">
      
      {/* ==================== 1. TOP INTERACTIVE BENCHMARK & DISPATCH BAR ==================== */}
      <div className="retro-box p-3 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <form onSubmit={handleQuickDispatch} className="flex items-center gap-2 flex-1 max-w-xl">
            <span className="text-red-500 font-bold text-xs">&gt; RUN DIRECTIVE:</span>
            <input
              type="text"
              value={quickInput}
              onChange={(e) => setQuickInput(e.target.value)}
              placeholder="e.g. 'Who is Virat Kohli?', 'Open Calculator', 'In terminal run Claude'..."
              disabled={isLoading}
              className="flex-1 bg-black border border-zinc-700 px-3 py-1.5 text-xs text-white placeholder-zinc-500 outline-none focus:border-red-500"
            />
            <button
              type="submit"
              disabled={!quickInput.trim() || isLoading}
              className="retro-btn-red px-3 py-1.5 text-xs flex items-center gap-1 disabled:opacity-40"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>DISPATCH</span>
            </button>
          </form>

          {/* Active Agent Telemetry Badge */}
          <div className="flex items-center gap-2 text-xs">
            <span className={`w-2 h-2 rounded-full ${isLoading ? 'bg-red-500 animate-ping' : 'bg-emerald-500'}`} />
            <span className="text-zinc-400 text-[11px]">ACTIVE MULTI-AGENT STATE:</span>
            <span className={`font-bold px-2 py-0.5 border text-[11px] ${
              isLoading
                ? 'bg-red-950 text-red-300 border-red-600 animate-pulse'
                : 'bg-black text-emerald-400 border-emerald-900/60'
            }`}>
              {isLoading ? (activeAgent || 'ORCHESTRATING...') : 'STANDBY READY'}
            </span>
          </div>
        </div>

        {/* Real-time Agent Test Presets */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t border-zinc-800">
          {/* Preset Bank A: Research & Crawling */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs bg-zinc-950/70 p-1.5 border border-zinc-800">
            <span className="text-red-400 font-bold text-[10px] flex items-center gap-1">
              <Globe className="w-3 h-3 text-red-500" />
              <span>LIVE WEB RESEARCH:</span>
            </span>
            <button
              onClick={() => handleTestFlow('Who is Virat Kohli?')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [1. Virat Kohli Bio]
            </button>
            <button
              onClick={() => handleTestFlow('Explain quantum computing')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [2. Quantum Theory]
            </button>
            <button
              onClick={() => handleTestFlow('Latest news on AI')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [3. Live AI News]
            </button>
          </div>

          {/* Preset Bank B: DOM & Desktop System Automation */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs bg-zinc-950/70 p-1.5 border border-zinc-800">
            <span className="text-zinc-300 font-bold text-[10px] flex items-center gap-1">
              <Terminal className="w-3 h-3 text-red-500" />
              <span>DOM &amp; DESKTOP ACTIONS:</span>
            </span>
            <button
              onClick={() => handleTestFlow('In terminal run Claude')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [4. Terminal Claude CLI]
            </button>
            <button
              onClick={() => handleTestFlow('Open Calculator')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [5. Open Calculator]
            </button>
            <button
              onClick={() => handleTestFlow('Go to Instagram and search for the song')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [6. Instagram Playwright]
            </button>
          </div>
        </div>
      </div>

      {/* ==================== REAL-TIME MULTI-AGENT TELEMETRY & DIRECTIVE STREAM ==================== */}
      {(isLoading || currentThought) && (
        <div className="retro-box p-2.5 bg-black/95 border-red-600/80 shadow-[0_0_15px_rgba(239,68,68,0.25)] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 overflow-hidden flex-1 min-w-[280px]">
            <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${isLoading ? 'bg-red-500 animate-ping' : 'bg-emerald-500'}`} />
            <span className="text-red-400 font-bold flex-shrink-0 text-[11px] uppercase">
              {isLoading ? '⚡ LIVE MULTI-AGENT WORKING:' : '● LAST TELEMETRY:'}
            </span>
            <span className="text-zinc-200 truncate font-mono text-[11px]">
              {currentThought || (isLoading ? 'Multi-agent orchestration in progress...' : 'Task execution complete.')}
            </span>
          </div>
          {planSteps && planSteps.length > 0 && (
            <div className="flex items-center gap-1.5 flex-shrink-0 text-[10px] text-zinc-400">
              <span className="text-red-500 font-bold">[DAG PLAN:</span>
              <span className="text-white font-bold">{planSteps.length} Steps</span>
              <span className="text-red-500 font-bold">]</span>
            </div>
          )}
        </div>
      )}

      {/* ==================== 2. MAIN LIVING NEURAL TOPOLOGY CANVAS ==================== */}
      <div className="relative bg-black border-2 border-zinc-800 rounded-lg shadow-2xl overflow-hidden min-h-[580px]">
        {/* Subtle retro scanlines */}
        <div className="absolute inset-0 pointer-events-none opacity-20 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px] z-10" />

        {/* Top Header Overlay with LIVE PREVIEW status */}
        <div className="absolute top-2.5 left-4 right-4 flex items-center justify-between z-20 pointer-events-none">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-red-600 text-white font-black text-[11px] border border-red-500 shadow">
              O.P.S. MULTI-AGENT SYNAPTIC GRAPH
            </span>
            <span className="text-[10px] text-emerald-400 bg-black/90 px-2 py-0.5 border border-emerald-800/80 font-bold hidden sm:inline-block">
              ● LIVE PREVIEW ACTIVE [PORT 3000]
            </span>
          </div>

          <div className="flex items-center gap-2 text-[10px] bg-black/85 px-2.5 py-1 border border-zinc-800 text-zinc-300">
            <Activity className={`w-3.5 h-3.5 ${isLoading ? 'text-red-500 animate-pulse' : 'text-zinc-500'}`} />
            <span>GLOW MODE:</span>
            <span className={isLoading ? "text-red-400 font-bold" : "text-zinc-400 font-bold"}>
              {isLoading ? "ACTIVE WORKSTATION GLOW" : "STANDBY (READY)"}
            </span>
          </div>
        </div>

        {/* The Live Canvas Wrapper */}
        <div ref={wrapRef} className="w-full h-[580px] min-h-[540px] relative">
          <canvas
            ref={canvasRef}
            className="block w-full h-full cursor-crosshair"
          />
        </div>

        {/* ==================== REAL-TIME NODE HOVER HUD CARD ==================== */}
        {hoveredAgent ? (
          <div className="absolute bottom-3 left-4 right-4 z-20 pointer-events-none">
            <div className="bg-black/95 border-2 border-red-600 rounded p-3 shadow-[0_0_20px_rgba(239,68,68,0.45)] backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <span className="px-1.5 py-0.2 bg-red-600 text-white font-black text-[10px] uppercase">
                    {hoveredAgent.tag}
                  </span>
                  <span className="text-white font-black text-sm tracking-wide">
                    {hoveredAgent.name}
                  </span>
                  <span className="text-zinc-500 text-[10px]">
                    (Stage {hoveredAgent.layerIdx + 1})
                  </span>
                </div>
                
                {/* Agent Task (Simple & Clear) */}
                <p className="text-zinc-300 text-[11px] leading-snug">
                  <strong className="text-red-400">Simple Task: </strong>
                  {hoveredAgent.task}
                </p>
              </div>

              {/* Model & Live Status Badges */}
              <div className="flex flex-wrap items-center gap-2 md:border-l md:border-zinc-800 md:pl-4">
                <div className="bg-zinc-950 px-2.5 py-1 border border-zinc-700 rounded text-left">
                  <span className="text-zinc-500 text-[9px] uppercase block">ASSIGNED MODEL / ENGINE</span>
                  <span className="text-white font-bold text-[11px] flex items-center gap-1">
                    <Cpu className="w-3 h-3 text-red-500" />
                    {hoveredAgent.model}
                  </span>
                </div>

                <div className="bg-zinc-950 px-2.5 py-1 border border-zinc-700 rounded text-left">
                  <span className="text-zinc-500 text-[9px] uppercase block">LIVE RUNTIME STATUS</span>
                  <span className={`font-bold text-[11px] flex items-center gap-1.5 ${
                    isLoading && activeAgentNode && activeAgentNode.node.id === hoveredAgent.id
                      ? 'text-red-400 animate-pulse'
                      : 'text-zinc-400'
                  }`}>
                    <span className={`w-2 h-2 rounded-full ${
                      isLoading && activeAgentNode && activeAgentNode.node.id === hoveredAgent.id
                        ? 'bg-red-500 animate-ping'
                        : 'bg-zinc-600'
                    }`} />
                    {isLoading && activeAgentNode && activeAgentNode.node.id === hoveredAgent.id
                      ? '⚡ EXECUTING DIRECTIVE'
                      : '● STANDBY (IDLE)'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Default Status Bar when not hovering */
          <div className="absolute bottom-3 left-4 right-4 z-20 pointer-events-none">
            <div className="bg-black/85 border border-zinc-800 rounded px-3 py-2 text-xs flex items-center justify-between text-zinc-400">
              <div className="flex items-center gap-2 text-[11px] truncate">
                <Info className={`w-3.5 h-3.5 flex-shrink-0 ${isLoading ? 'text-red-500 animate-pulse' : 'text-zinc-500'}`} />
                <span className="truncate">
                  {isLoading
                    ? `⚡ [EXECUTING]: Active node ${activeAgent || 'ORCHESTRATING'} is glowing and processing directive.`
                    : "Nodes are in active standby. Nodes glow intensely with action potential pulses when working on any directive."}
                </span>
              </div>
              <div className="text-[10px] text-zinc-400 hidden sm:block flex-shrink-0 font-bold">
                <span>[ POP-UP COCKPIT &amp; HOTKEY SYNC ACTIVE ]</span>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
