import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Play,
  Square,
  RefreshCw,
  Loader2,
  Globe,
  Terminal,
  Cpu,
  Activity,
  Info,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ChevronRight,
  Layers,
  Database,
  Search,
  Code2,
  Wrench,
  CheckSquare,
  ShieldCheck,
  Radio,
  FileCode,
  Zap
} from 'lucide-react';
import { retroSoundEngine } from '../utils/retroSounds';

// ==================== O.P.S. CANONICAL AGENT TOPOLOGY (v3.0) ====================
// 4 Hierarchical Stages matching the Authoritative Specification:
// Stage 01: Ingress & Routing (Router Agent, Supervisor Agent)
// Stage 02: Planning & Mission Control (Mission Manager, Lead Planner)
// Stage 03: Specialized Agent Fleet (Developer, Debugger, Tester, Reviewer, Web, Research, Automation, Browser, RAG)
// Stage 04: Verification & Response (Ground-Truth Verifier, Response Engine)

// ==================== O.P.S. CANONICAL AGENT TOPOLOGY (v3.0) ====================
// Stage 01: Ingress & Routing (Fast Router, Canonical Supervisor)
// Stage 02: Planning & Mission Control (Mission Manager, Lead Planner)
// Stage 03: Specialized Agent Fleet (Developer, Debugger, Tester, Reviewer, Web, Research, Automation, Browser, RAG)
// Stage 04: Verification & Response (Ground-Truth Verifier, Response Engine)

const LAYERS = [2, 2, 9, 2];
const LAST = LAYERS.length - 1;

const STAGE_LABELS = [
  "STAGE 01: INGRESS & ROUTING",
  "STAGE 02: PLANNING & MISSION CONTROL",
  "STAGE 03: SPECIALIZED AGENT FLEET",
  "STAGE 04: VERIFICATION & RESPONSE"
];

const AGENT_NODES = [
  // Stage 01: Ingress & Routing
  [
    {
      id: "router",
      name: "Fast Router",
      tag: "FAST ROUTER",
      model: "Qwen3 0.6B Q8_0",
      type: "routing",
      task: "Classifies intent in <50ms across 5 modes: CHAT, TASK, MISSION, MEMORY, CLARIFICATION.",
      matchKeys: ["router", "fast router", "intent router", "classify", "mode"]
    },
    {
      id: "supervisor",
      name: "Canonical Supervisor",
      tag: "ORCHESTRATOR",
      model: "Qwen3 1.7B Q8_0",
      type: "supervisor",
      task: "Coordinates execution pipeline, delegates to specialists, and oversees mission execution.",
      matchKeys: ["supervisor", "orchestrator", "canonical supervisor", "lead supervisor"]
    }
  ],
  // Stage 02: Planning & Mission Control
  [
    {
      id: "mission_manager",
      name: "Mission Manager",
      tag: "MISSION ENGINE",
      model: "Stateful Core",
      type: "mission",
      task: "Tracks multi-step state, step dependencies, and manages 3-retry bounded recovery loops.",
      matchKeys: ["mission manager", "mission", "task manager", "mission engine"]
    },
    {
      id: "planner",
      name: "Lead Planner",
      tag: "DAG PLANNER",
      model: "Qwen3 1.7B Q8_0",
      type: "planner",
      task: "Decomposes complex goals into explicit, ordered, verifiable plan steps with assigned tools.",
      matchKeys: ["planner", "lead planner", "task decomposition", "plan", "dag planner"]
    }
  ],
  // Stage 03: Specialized Agent Fleet (9 Canonical Agents)
  [
    {
      id: "developer",
      name: "Developer Agent",
      tag: "DEV AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Repository inspection, code synthesis, refactoring, and filesystem operations.",
      capabilities: ["filesystem.read", "filesystem.write", "filesystem.create_directory", "filesystem.delete", "terminal.execute"],
      matchKeys: ["developer", "code", "dev", "scaffold", "refactor"]
    },
    {
      id: "debugger",
      name: "Debugger Agent",
      tag: "DEBUGGER AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Analyzes stack traces, identifies root causes, and generates automated remediation patches.",
      capabilities: ["terminal.execute", "filesystem.read", "filesystem.write"],
      matchKeys: ["debugger", "debug", "diagnose", "root cause", "patch"]
    },
    {
      id: "tester",
      name: "Tester Agent",
      tag: "TESTER AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Executes unit, integration, and end-to-end tests to verify assertions and exit codes.",
      capabilities: ["terminal.run_tests", "terminal.execute", "filesystem.read"],
      matchKeys: ["tester", "test", "pytest", "assertion", "test runner"]
    },
    {
      id: "reviewer",
      name: "Reviewer Agent",
      tag: "REVIEWER AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Inspects code changes for architectural adherence, security guidelines, and safety policies.",
      capabilities: ["filesystem.read"],
      matchKeys: ["reviewer", "review", "audit", "compliance", "lint"]
    },
    {
      id: "web",
      name: "Web Agent",
      tag: "WEB CRAWLER",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Fetches live web content, search results, and documentation across the untrusted boundary.",
      capabilities: ["web.search", "web.crawl", "web.extract_structured"],
      matchKeys: ["web", "web agent", "search", "crawl", "scrape", "crawlee", "beautifulsoup"]
    },
    {
      id: "research",
      name: "Research Agent",
      tag: "RESEARCH AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Synthesizes multi-source facts, combining live web search with internal RAG memory.",
      capabilities: ["web.search", "web.crawl", "rag.search"],
      matchKeys: ["research", "research agent", "fact check", "synthesis"]
    },
    {
      id: "automation",
      name: "Automation Agent",
      tag: "DESKTOP GUI",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Launches installed native desktop applications and interacts with OS files.",
      capabilities: ["desktop.launch_app", "desktop.open_file", "desktop.hotkey"],
      matchKeys: ["automation", "automation agent", "launch", "desktop", "os", "installed apps"]
    },
    {
      id: "browser",
      name: "Browser Agent",
      tag: "PLAYWRIGHT DOM",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Navigates browser DOM, fills forms, clicks elements, and executes web interaction flows.",
      capabilities: ["browser.open", "browser.navigate", "browser.click", "browser.type", "browser.extract"],
      matchKeys: ["browser", "browser agent", "playwright", "dom", "click", "open web"]
    },
    {
      id: "rag",
      name: "RAG / Knowledge Agent",
      tag: "SEMANTIC RAG",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      task: "Queries and indexes persistent ChromaDB vector collections and project documentation.",
      capabilities: ["rag.search", "rag.index", "rag.ingest"],
      matchKeys: ["rag", "rag agent", "knowledge", "chroma", "vector", "memory", "semantic rag"]
    }
  ],
  // Stage 04: Verification & Response
  [
    {
      id: "verifier",
      name: "Ground-Truth Verifier",
      tag: "GROUND-TRUTH VERIFIER",
      model: "Deterministic Logic",
      type: "verifier",
      task: "Physical state validator. Asserts file existence, process health, and verified exit codes.",
      capabilities: ["filesystem.exists", "process.running", "tests.passed"],
      matchKeys: ["verifier", "ground truth", "critic", "verification", "physical state"]
    },
    {
      id: "response",
      name: "Response Engine",
      tag: "JARVIS SYNTHESIZER",
      model: "Llama 3.2 1B Instruct",
      type: "response",
      task: "Synthesizes final tactical responses strictly grounded in physically verified evidence.",
      matchKeys: ["response", "response engine", "synthesizer", "jarvis", "executive voice"]
    }
  ]
];

// Canvas Neural Parameters
const TRAVEL = 750; // ms for an action potential to cross one gap
const TAU = Math.PI * 2;
const F = 6; // 6 fine filaments per connection for organic sinewave bundle effect

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
      if (node.id === lower || node.matchKeys.some((k) => lower.includes(k))) {
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
  briefingText,
  sessionId,
  onClearMemory,
  onStopExecution,
  liveEvents = []
}) {
  const [quickInput, setQuickInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [hoveredAgent, setHoveredAgent] = useState(null);

  // Derived Real-Time Agent State Map derived from actual backend events
  const agentStateMap = useMemo(() => {
    const states = {};

    // Default all agents to IDLE
    AGENT_NODES.forEach((layer) => {
      layer.forEach((agent) => {
        states[agent.id] = {
          status: 'IDLE',
          currentTool: null,
          lastMessage: null,
          lastUpdated: null,
          error: null,
          executions: 0
        };
      });
    });

    // Reduce live events into canonical agent states
    if (liveEvents && liveEvents.length > 0) {
      liveEvents.forEach((evt) => {
        const agentId = evt.agent?.id || evt.agent_id;
        const matched = findActiveNode(agentId || evt.agent?.name || evt.agent_name || evt.agent);
        if (matched) {
          const id = matched.node.id;
          const status = evt.status || 'RUNNING';
          states[id] = {
            ...states[id],
            status: status,
            currentTool: evt.tool || evt.capability || states[id].currentTool,
            lastMessage: evt.message || evt.thought || states[id].lastMessage,
            lastUpdated: evt.timestamp || Date.now(),
            error: status === 'FAILED' ? (evt.message || evt.error) : null,
            executions: states[id].executions + 1
          };
        }

        // Check if tool events belong to an active agent
        if (evt.event_type === 'TOOL_STARTED' && evt.tool) {
          const reqAgent = findActiveNode(evt.agent_id || evt.agent?.name);
          if (reqAgent) {
            states[reqAgent.node.id].currentTool = evt.tool;
            states[reqAgent.node.id].status = 'RUNNING';
          }
        } else if (evt.event_type === 'TOOL_COMPLETED') {
          const reqAgent = findActiveNode(evt.agent_id || evt.agent?.name);
          if (reqAgent) {
            states[reqAgent.node.id].currentTool = null;
          }
        }
      });
    }

    // Reflect currently active agent if provided by parent
    if (activeAgent && isLoading) {
      const matched = findActiveNode(activeAgent);
      if (matched) {
        states[matched.node.id] = {
          ...states[matched.node.id],
          status: 'RUNNING',
          lastMessage: currentThought,
          lastUpdated: Date.now()
        };
      }
    }

    return states;
  }, [liveEvents, activeAgent, currentThought, isLoading]);

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
    if (onDispatchPrompt) onDispatchPrompt(quickInput);
    if (triggerPulseRef.current) triggerPulseRef.current();
    setQuickInput('');
  };

  const handleTestFlow = (prompt) => {
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

    // Organic axon shapes (sinewave bundles with 6 harmonic filaments)
    const C = LAYERS.slice(1).map((n, l) =>
      Array.from({ length: n }, () =>
        Array.from({ length: LAYERS[l] }, () => ({
          bend: (Math.random() - 0.5) * 22,
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

    // Cross-links and quality loops matching canonical specification:
    // Ground-Truth Verifier (Stage 3, index 0) loops back to Debugger (Stage 2, index 1)
    // Tester (Stage 2, index 2) loops back to Debugger (Stage 2, index 1)
    const ARCHITECTURAL_CROSS_LINKS = [
      { l1: 3, i: 0, l2: 2, j: 1, bow: -45, f: 1.6, sp: 0.0010, ph: 0.5, hue: 0.95, isLoop: true }, // Verifier -> Debugger Recovery loop
      { l1: 2, i: 2, l2: 2, j: 1, bow: -25, f: 1.4, sp: 0.0009, ph: 0.8, hue: 0.85, isLoop: true }, // Tester -> Debugger Remediate loop
      { l1: 0, i: 0, l2: 1, j: 1, bow: 12, f: 1.3, sp: 0.0008, ph: 1.1, hue: 0.2 },  // Fast Router -> Lead Planner
      { l1: 1, i: 0, l2: 2, j: 0, bow: -10, f: 1.3, sp: 0.0008, ph: 1.4, hue: 0.3 }, // Mission Manager -> Developer
      { l1: 1, i: 0, l2: 2, j: 4, bow: 0, f: 1.3, sp: 0.0008, ph: 1.7, hue: 0.4 },   // Mission Manager -> Web Agent
      { l1: 1, i: 0, l2: 2, j: 6, bow: 10, f: 1.3, sp: 0.0008, ph: 2.0, hue: 0.5 },  // Mission Manager -> Automation Agent
      { l1: 1, i: 0, l2: 2, j: 8, bow: 20, f: 1.3, sp: 0.0008, ph: 2.3, hue: 0.6 },  // Mission Manager -> RAG Agent
    ];

    const G = [...ARCHITECTURAL_CROSS_LINKS];

    let nodes = [];
    let radius = 14;
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
      height = Math.max(rect.height, 680);
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const maxLayerCount = Math.max(...LAYERS);
      const gap = Math.min(58, (height * 0.84) / maxLayerCount);
      radius = Math.max(12, Math.min(16, gap * 0.26));
      const padX = Math.max(65, width * 0.11);

      // Node placement with diamond curved arc bulge for Stage 03 fleet
      nodes = LAYERS.map((n, l) =>
        Array.from({ length: n }, (_, i) => {
          const arcOffset = l === 2 ? Math.sin((i / (n - 1 || 1)) * Math.PI) * 45 : 0;
          return {
            bx: padX + ((width - padX * 2) * l) / LAST + arcOffset,
            by: height / 2 + 16 + (i - (n - 1) / 2) * gap,
            x: 0,
            y: 0,
            ph: Math.random() * TAU,
          };
        })
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
      let off = env * ((2.2 * breathe + h * 5 + boost * 4) * wave + c.bend * Math.sin(Math.PI * s));
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

      // Identify currently executing agent from props / live state
      const activeTarget = findActiveNode(activeAgent) || (isLoading ? { l: 0, i: 0, node: AGENT_NODES[0][0] } : null);
      const isSystemWorking = Boolean(isLoading && activeTarget);

      // Active working continuous stream
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

      // Drift of nodes
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

      // 1. Draw Tactical Grid Background
      ctx.strokeStyle = "rgba(220, 38, 38, 0.08)";
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

      // 2. Draw Main Synaptic Connections (Multi-strand sinewave tendril bundles)
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
            
            const rgb = tint(c.hue, h);
            const baseAlpha = isPathActive ? 0.85 : related ? 0.65 : 0.24;
            const amp = baseAlpha + h * 0.45;

            for (const st of c.st) {
              const pts = [];
              for (let q = 0; q <= SEG; q++) pts.push(pointAt(l, j, i, q / SEG, now, st.k));
              const shimmer = 0.75 + 0.25 * Math.sin(now * st.sp * 3 + st.ph);
              ctx.strokeStyle = `rgba(${rgb}, ${Math.min(0.95, amp * shimmer)})`;
              ctx.lineWidth = isPathActive ? 1.4 : related ? 1.0 : 0.75;
              ctx.beginPath();
              pts.forEach(([x, y], q) => (q ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
              ctx.stroke();

              // Moving glint along axon
              const i0 = Math.floor(((now * 0.00012 * (1 + st.gl) + st.gl) % 1) * (SEG - 5));
              ctx.strokeStyle = `rgba(${rgb}, ${Math.min(0.9, amp * 2.8 * shimmer)})`;
              ctx.lineWidth = isPathActive ? 2.0 : 1.2;
              ctx.beginPath();
              for (let q = i0; q <= i0 + 4; q++) {
                q === i0 ? ctx.moveTo(pts[q][0], pts[q][1]) : ctx.lineTo(pts[q][0], pts[q][1]);
              }
              ctx.stroke();
            }
          }
        }
      }

      // 3. Draw Architectural Cross-Links (Quality loops and recovery dispatches)
      for (const g of G) {
        if (!nodes[g.l1] || !nodes[g.l1][g.i] || !nodes[g.l2] || !nodes[g.l2][g.j]) continue;
        const related = hover && ((hover.l === g.l1 && hover.i === g.i) || (hover.l === g.l2 && hover.i === g.j));
        const isPathActive = isSystemWorking && activeTarget && ((activeTarget.l === g.l1 && activeTarget.i === g.i) || (activeTarget.l === g.l2 && activeTarget.i === g.j));
        
        const rgb = g.isLoop ? "245, 158, 11" : tint(g.hue, 0.25);
        const alpha = g.isLoop ? 0.85 : isPathActive ? 0.75 : related ? 0.55 : 0.22;

        ctx.strokeStyle = `rgba(${rgb}, ${alpha})`;
        ctx.lineWidth = g.isLoop ? 1.4 : isPathActive ? 1.2 : 0.75;
        if (g.isLoop) {
          ctx.setLineDash([4, 4]);
        } else {
          ctx.setLineDash([]);
        }
        ctx.beginPath();
        for (let q = 0; q <= SEG; q++) {
          const [x, y] = ghostPoint(g, q / SEG, now, 0);
          q ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
        }
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // 4. Draw Electric Wave Sparks & Radiant Halos
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
        const halo = ctx.createRadialGradient(prev[0], prev[1], 0, prev[0], prev[1], 10);
        halo.addColorStop(0, `rgba(255, 245, 245, ${0.9 * s})`);
        halo.addColorStop(1, "rgba(235, 30, 45, 0)");
        ctx.fillStyle = halo;
        ctx.beginPath();
        ctx.arc(prev[0], prev[1], 10, 0, TAU);
        ctx.fill();
      }

      ctx.globalCompositeOperation = "source-over";

      // 5. Draw 3D Agent Spheres with Scanlines & Specular Glints
      for (let l = 0; l < LAYERS.length; l++) {
        for (let i = 0; i < LAYERS[l]; i++) {
          const n = nodes[l][i];
          const isNodeActive = isSystemWorking && activeTarget && activeTarget.l === l && activeTarget.i === i;
          const isHovered = hover && hover.l === l && hover.i === i;
          const r = radius * (isNodeActive ? 1.25 : 1.0);

          // A. Bloom Glow for Active Nodes
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

            // Pulsing reticle
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.8 + 0.2 * Math.sin(now * 0.009)})`;
            ctx.lineWidth = 2.0;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 6 + Math.sin(now * 0.008) * 3, 0, TAU);
            ctx.stroke();
          }

          // B. Hover Reticle
          if (isHovered && !isNodeActive) {
            ctx.strokeStyle = "rgba(255, 255, 255, 0.95)";
            ctx.lineWidth = 1.6;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 4, 0, TAU);
            ctx.stroke();
          }

          // C. Node Sphere Body
          if (isNodeActive) {
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

          // D. Tactical Badge Under Each Node (Exact Rectangular HUD Style from photo)
          const agentMeta = AGENT_NODES[l]?.[i];
          if (agentMeta) {
            const tagText = agentMeta.tag;
            ctx.font = "bold 9px 'JetBrains Mono', 'Geist Mono', monospace";
            const textMetrics = ctx.measureText(tagText);
            const pillW = textMetrics.width + 10;
            const pillH = 15;
            const pillX = n.x - pillW / 2;
            const pillY = n.y + r + 5;

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

            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = isNodeActive ? "#ffffff" : isHovered ? "#ffffff" : "#f4f4f5";
            ctx.fillText(tagText, n.x, pillY + pillH / 2);
          }
        }
      }

      // 6. Canvas Tooltip Render for Hovered Agent
      if (hover && AGENT_NODES[hover.l]?.[hover.i]) {
        const meta = AGENT_NODES[hover.l][hover.i];
        const n = nodes[hover.l][hover.i];
        const isHoverActive = isSystemWorking && activeTarget && activeTarget.l === hover.l && activeTarget.i === hover.i;

        const badgeW = 200;
        const badgeH = 40;
        const boxX = Math.max(10, Math.min(width - badgeW - 10, n.x - badgeW / 2));
        const boxY = Math.max(10, n.y - radius - badgeH - 12);

        ctx.fillStyle = "rgba(5, 5, 8, 0.95)";
        ctx.strokeStyle = isHoverActive ? "#ef4444" : "#f43f5e";
        ctx.lineWidth = 1.4;
        ctx.fillRect(boxX, boxY, badgeW, badgeH);
        ctx.strokeRect(boxX, boxY, badgeW, badgeH);

        ctx.textAlign = "left";
        ctx.textBaseline = "alphabetic";
        ctx.font = "bold 10px 'JetBrains Mono', 'Geist Mono', monospace";
        ctx.fillStyle = "#ffffff";
        ctx.fillText(meta.name.slice(0, 26), boxX + 8, boxY + 14);

        ctx.font = "9px 'JetBrains Mono', 'Geist Mono', monospace";
        ctx.fillStyle = isHoverActive ? "#ef4444" : "#fca5a5";
        ctx.fillText(`⚡ ${meta.model.slice(0, 28)}`, boxX + 8, boxY + 28);
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

      let clicked = null;
      nodes.forEach((layer, l) => {
        layer.forEach((n, i) => {
          if (Math.hypot(n.x - mx, n.y - my) < radius + 12) {
            clicked = AGENT_NODES[l][i];
          }
        });
      });

      if (clicked) {
        retroSoundEngine.playKeyClick();
        setSelectedAgent(clicked);
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

  // Active Mission Progress Extraction
  const activeMission = useMemo(() => {
    const missionEvt = [...liveEvents].reverse().find((e) => e.event_type === 'MISSION_CREATED' || e.mission_id);
    if (!missionEvt) return null;

    const plan = missionEvt.metadata?.plan || (planSteps && planSteps.length > 0 ? { steps: planSteps } : null);
    const steps = plan?.steps || [];
    return {
      mission_id: missionEvt.mission_id,
      goal: missionEvt.metadata?.goal || missionEvt.message || 'Executing Autonomous Mission',
      steps: steps,
      status: missionEvt.status || 'RUNNING'
    };
  }, [liveEvents, planSteps]);

  return (
    <div className="space-y-4 font-mono select-none">

      {/* ==================== 1. TOP INTERACTIVE DISPATCH & REAL-TIME CONTROLS ==================== */}
      <div className="retro-box p-3 space-y-2 bg-[#09090b] border-zinc-800">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <form onSubmit={handleQuickDispatch} className="flex items-center gap-2 flex-1 max-w-2xl">
            <span className="text-red-500 font-bold text-xs flex items-center gap-1">
              <Zap className="w-3.5 h-3.5 text-red-500 fill-red-500" />
              <span>DIRECTIVE:</span>
            </span>
            <input
              type="text"
              value={quickInput}
              onChange={(e) => setQuickInput(e.target.value)}
              placeholder="Enter directive (e.g. 'Open Chrome', 'Build React dashboard', 'Where is my API code?')..."
              disabled={isLoading}
              className="flex-1 bg-black border border-zinc-700 px-3 py-1.5 text-xs text-white placeholder-zinc-500 outline-none focus:border-red-500 transition"
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

          {/* STOP & REFRESH Real-Time Control Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onStopExecution && onStopExecution()}
              disabled={!isLoading}
              title="STOP execution (Preserves session and dialogue context)"
              className="px-2.5 py-1.5 text-xs bg-zinc-900 border border-zinc-700 hover:border-amber-500 hover:text-amber-400 text-zinc-300 flex items-center gap-1 font-bold disabled:opacity-40 transition"
            >
              <Square className="w-3.5 h-3.5 text-amber-500 fill-current" />
              <span>[ ⏹ STOP ]</span>
            </button>

            <button
              onClick={() => onClearMemory && onClearMemory()}
              title="REFRESH session (Clears volatile context, creates new session ID, preserves ChromaDB)"
              className="px-2.5 py-1.5 text-xs bg-zinc-900 border border-zinc-700 hover:border-red-500 hover:text-red-400 text-zinc-300 flex items-center gap-1 font-bold transition"
            >
              <RefreshCw className="w-3.5 h-3.5 text-red-500" />
              <span>[ ↻ REFRESH ]</span>
            </button>
          </div>
        </div>

        {/* Real-time Preset Scenarios */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t border-zinc-800">
          <div className="flex flex-wrap items-center gap-1.5 text-xs bg-black/60 p-1.5 border border-zinc-800/80">
            <span className="text-red-400 font-bold text-[10px] flex items-center gap-1">
              <Terminal className="w-3 h-3 text-red-500" />
              <span>CORE TASKS:</span>
            </span>
            <button
              onClick={() => handleTestFlow('Open Chrome.')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [1. Open Chrome]
            </button>
            <button
              onClick={() => handleTestFlow('Where is my API code?')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [2. RAG Code Search]
            </button>
            <button
              onClick={() => handleTestFlow('Search the latest React documentation.')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [3. Web Research]
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-1.5 text-xs bg-black/60 p-1.5 border border-zinc-800/80">
            <span className="text-zinc-300 font-bold text-[10px] flex items-center gap-1">
              <Layers className="w-3 h-3 text-red-500" />
              <span>COMPLEX MISSIONS:</span>
            </span>
            <button
              onClick={() => handleTestFlow('Build a React dashboard.')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [4. Build React Dashboard]
            </button>
            <button
              onClick={() => handleTestFlow('Fix the failing login tests.')}
              disabled={isLoading}
              className="retro-btn px-2 py-0.5 text-[10px] hover:border-red-600 hover:text-white"
            >
              [5. Debug Failing Tests]
            </button>
          </div>
        </div>
      </div>

      {/* ==================== 2. MAIN AUTHORITATIVE AGENT TOPOLOGY CANVAS ==================== */}
      <div className="relative bg-[#050505] border-2 border-zinc-800 rounded shadow-2xl overflow-hidden min-h-[580px]">
        {/* Subtle scanline overlay */}
        <div className="absolute inset-0 pointer-events-none opacity-20 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px] z-10" />

        {/* Top Header Overlay with LIVE TOPOLOGY status */}
        <div className="absolute top-2.5 left-4 right-4 flex items-center justify-between z-20 pointer-events-none">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-red-600 text-white font-black text-[11px] border border-red-500 shadow">
              O.P.S. v3.0 ORCHESTRATION TOPOLOGY
            </span>
            <span className="text-[10px] text-emerald-400 bg-black/90 px-2 py-0.5 border border-emerald-800/80 font-bold hidden sm:inline-block">
              ● 15 SPECIALIZED AGENTS ACTIVE
            </span>
          </div>

          <div className="flex items-center gap-2 text-[10px] bg-black/90 px-2.5 py-1 border border-zinc-800 text-zinc-300">
            <Activity className={`w-3.5 h-3.5 ${isLoading ? 'text-red-500 animate-pulse' : 'text-zinc-500'}`} />
            <span>PIPELINE STATUS:</span>
            <span className={isLoading ? "text-red-400 font-bold" : "text-emerald-400 font-bold"}>
              {isLoading ? "LIVE ORCHESTRATION ACTIVE" : "STANDBY READY"}
            </span>
          </div>
        </div>

        {/* Stage Column Labels Header */}
        <div className="absolute top-10 left-0 right-0 grid grid-cols-5 px-4 text-center z-20 pointer-events-none">
          {STAGE_LABELS.map((lbl, idx) => (
            <div key={idx} className="text-[9px] font-extrabold text-zinc-400 uppercase tracking-wider">
              {lbl}
            </div>
          ))}
        </div>

        {/* The Live Canvas */}
        <div ref={wrapRef} className="w-full h-[600px] min-h-[560px] relative">
          <canvas ref={canvasRef} className="block w-full h-full cursor-pointer" />
        </div>

        {/* Bottom Hover HUD Indicator */}
        <div className="absolute bottom-3 left-4 right-4 z-20 pointer-events-none">
          {hoveredAgent ? (
            <div className="bg-black/95 border border-red-600 rounded p-2.5 shadow-xl flex items-center justify-between gap-3 text-xs">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="px-1.5 py-0.2 bg-red-600 text-white font-black text-[10px]">{hoveredAgent.tag}</span>
                  <span className="text-white font-bold text-sm">{hoveredAgent.name}</span>
                  <span className="text-zinc-500 text-[10px]">({hoveredAgent.model})</span>
                </div>
                <p className="text-zinc-300 text-[11px] leading-tight">{hoveredAgent.role}</p>
              </div>
              <div className="text-right">
                <span className="text-zinc-500 text-[9px] uppercase block">LIVE STATE</span>
                <span className={`font-bold text-[11px] ${
                  agentStateMap[hoveredAgent.id]?.status === 'RUNNING' ? 'text-red-400 animate-pulse' : 'text-zinc-400'
                }`}>
                  {agentStateMap[hoveredAgent.id]?.status || 'IDLE'}
                </span>
              </div>
            </div>
          ) : (
            <div className="bg-black/85 border border-zinc-800 rounded px-3 py-1.5 text-xs flex items-center justify-between text-zinc-400">
              <div className="flex items-center gap-2 text-[11px]">
                <Info className={`w-3.5 h-3.5 ${isLoading ? 'text-red-500 animate-pulse' : 'text-zinc-500'}`} />
                <span>
                  {isLoading
                    ? `⚡ Active Directive processing: ${currentThought || 'Executing...'}`
                    : "Click or hover any agent node to inspect real-time telemetry, model assignments, and capability tools."}
                </span>
              </div>
              <span className="text-[10px] text-zinc-500 font-bold hidden md:inline">
                SESSION: {sessionId?.slice(0, 15)}...
              </span>
            </div>
          )}
        </div>
      </div>

      {/* ==================== 3. DUAL WORKSTATION: MISSION PROGRESS & LIVE EVENT TIMELINE ==================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        
        {/* Left Column (5 Cols): Active Mission & Verification Progress */}
        <div className="lg:col-span-5 flex flex-col space-y-2">
          <div className="retro-box p-3 flex-1 flex flex-col bg-[#09090b] border-zinc-800">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2 mb-2">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-red-500" />
                <span className="font-bold text-xs text-white">MISSION & VERIFICATION ENGINE</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 bg-zinc-900 border border-zinc-700 text-zinc-300 font-bold">
                {activeMission ? activeMission.status : 'STANDBY'}
              </span>
            </div>

            {activeMission && activeMission.steps.length > 0 ? (
              <div className="space-y-2 flex-1 overflow-y-auto max-h-[300px] pr-1">
                <div className="text-xs text-zinc-300 font-bold bg-zinc-950 p-2 border border-zinc-800">
                  <span className="text-red-500">GOAL: </span>
                  <span>{activeMission.goal}</span>
                </div>

                <div className="space-y-1.5">
                  {activeMission.steps.map((step, idx) => {
                    const stepAgent = findAgentNode(step.assigned_agent);
                    const isStepRunning = agentStateMap[stepAgent?.node.id || '']?.status === 'RUNNING';
                    const isStepDone = agentStateMap[stepAgent?.node.id || '']?.status === 'COMPLETED';

                    return (
                      <div
                        key={idx}
                        className={`p-2 border text-xs flex items-start justify-between gap-2 ${
                          isStepRunning
                            ? 'bg-red-950/30 border-red-600/80 text-white animate-pulse'
                            : (isStepDone ? 'bg-zinc-950/80 border-emerald-900/60 text-zinc-300' : 'bg-black/60 border-zinc-800 text-zinc-400')
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <span className="font-black text-red-500 text-[11px] mt-0.5">[{idx + 1}]</span>
                          <div>
                            <div className="font-bold text-white text-[11px]">{step.description || `Step ${idx + 1}`}</div>
                            <div className="text-[10px] text-zinc-400 mt-0.5 flex items-center gap-1.5">
                              <span className="text-red-400 font-bold">{step.assigned_agent?.toUpperCase()}</span>
                              <span>•</span>
                              <span className="font-mono text-zinc-300">{step.capability}</span>
                            </div>
                          </div>
                        </div>

                        <div>
                          {isStepDone ? (
                            <span className="text-emerald-400 font-bold text-[10px] flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                              <span>VERIFIED</span>
                            </span>
                          ) : isStepRunning ? (
                            <span className="text-red-400 font-bold text-[10px] flex items-center gap-1 animate-pulse">
                              <Loader2 className="w-3.5 h-3.5 animate-spin text-red-500" />
                              <span>RUNNING</span>
                            </span>
                          ) : (
                            <span className="text-zinc-600 font-bold text-[10px]">QUEUED</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-zinc-500 text-xs">
                <CheckSquare className="w-8 h-8 text-zinc-700 mb-2" />
                <p>No active multi-step mission executing.</p>
                <p className="text-[11px] text-zinc-600 mt-1">Dispatching a complex goal (e.g. 'Build React dashboard') generates an explicit verifiable plan here.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (7 Cols): Real-Time Live Event Stream & Timeline */}
        <div className="lg:col-span-7 flex flex-col space-y-2">
          <div className="retro-box p-3 flex-1 flex flex-col bg-[#09090b] border-zinc-800">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2 mb-2">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-red-500 animate-pulse" />
                <span className="font-bold text-xs text-white">REAL-TIME EXECUTION EVENT STREAM</span>
              </div>
              <span className="text-[10px] text-zinc-400">
                {liveEvents.length} Events Logged
              </span>
            </div>

            <div className="space-y-1.5 flex-1 overflow-y-auto max-h-[300px] pr-1 font-mono text-xs">
              {liveEvents.length > 0 ? (
                liveEvents.slice().reverse().map((evt, idx) => {
                  const time = new Date(evt.timestamp * 1000 || Date.now()).toLocaleTimeString();
                  const isErr = evt.status === 'FAILED' || evt.event_type?.includes('FAILED') || evt.event_type === 'ERROR_OCCURRED';
                  const isSucc = evt.status === 'COMPLETED' || evt.event_type?.includes('PASSED') || evt.event_type?.includes('COMPLETED');

                  return (
                    <div
                      key={idx}
                      className={`p-1.5 border text-[11px] flex items-start gap-2 ${
                        isErr
                          ? 'bg-red-950/40 border-red-800 text-red-300'
                          : (isSucc ? 'bg-zinc-950 border-zinc-800/80 text-zinc-300' : 'bg-black border-zinc-800 text-zinc-400')
                      }`}
                    >
                      <span className="text-zinc-500 text-[10px] font-mono flex-shrink-0 mt-0.5">{time}</span>
                      <span className={`px-1 py-0.2 text-[9px] font-bold flex-shrink-0 ${
                        isErr ? 'bg-red-600 text-white' : (isSucc ? 'bg-emerald-900/60 text-emerald-300' : 'bg-zinc-800 text-zinc-300')
                      }`}>
                        {evt.event_type || 'EVENT'}
                      </span>
                      <div className="flex-1 truncate">
                        <span className="text-red-400 font-bold mr-1.5">[{evt.agent?.name || evt.agent_id || 'OPS'}]</span>
                        <span className="text-zinc-200">{evt.message || evt.thought || (evt.tool ? `Tool: ${evt.tool}` : 'Executing directive')}</span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-zinc-500 text-xs">
                  <Activity className="w-8 h-8 text-zinc-700 mb-2" />
                  <p>Event stream idle.</p>
                  <p className="text-[11px] text-zinc-600 mt-1">Real-time structured events from the backend router, agents, tools, and verifiers stream live here.</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* ==================== 4. AGENT ACTIVITY DETAILS MODAL (WHEN NODE CLICKED) ==================== */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#09090b] border-2 border-red-600 max-w-xl w-full p-4 rounded shadow-[0_0_30px_rgba(239,68,68,0.5)] space-y-3 font-mono">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-red-600 text-white font-bold text-xs">{selectedAgent.tag}</span>
                <span className="text-white font-bold text-base">{selectedAgent.name}</span>
              </div>
              <button
                onClick={() => setSelectedAgent(null)}
                className="text-zinc-400 hover:text-white text-xs px-2 py-1 bg-zinc-900 border border-zinc-700"
              >
                [ ✕ CLOSE ]
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">ASSIGNED MODEL</span>
                <span className="text-white font-bold flex items-center gap-1 mt-0.5">
                  <Cpu className="w-3.5 h-3.5 text-red-500" />
                  {selectedAgent.model}
                </span>
              </div>

              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">LIVE STATUS</span>
                <span className={`font-bold text-xs mt-0.5 block ${
                  agentStateMap[selectedAgent.id]?.status === 'RUNNING' ? 'text-red-400 animate-pulse' : 'text-zinc-300'
                }`}>
                  {agentStateMap[selectedAgent.id]?.status || 'IDLE'}
                </span>
              </div>
            </div>

            <div className="bg-black p-2 border border-zinc-800 text-xs">
              <span className="text-zinc-500 text-[10px] block uppercase">RESPONSIBILITY</span>
              <p className="text-zinc-200 mt-0.5 leading-relaxed">{selectedAgent.role}</p>
            </div>

            {selectedAgent.capabilities && (
              <div className="bg-black p-2 border border-zinc-800 text-xs">
                <span className="text-zinc-500 text-[10px] block uppercase">ALLOWED CAPABILITIES</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedAgent.capabilities.map((cap, idx) => (
                    <span key={idx} className="px-1.5 py-0.5 bg-zinc-900 border border-zinc-700 text-zinc-300 text-[10px]">
                      {cap}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {agentStateMap[selectedAgent.id]?.lastMessage && (
              <div className="bg-zinc-950 p-2 border border-red-900/60 text-xs">
                <span className="text-red-400 text-[10px] block uppercase font-bold">LATEST AGENT TELEMETRY</span>
                <p className="text-white mt-0.5 text-[11px] font-mono">{agentStateMap[selectedAgent.id].lastMessage}</p>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
