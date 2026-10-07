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

const CANONICAL_LAYERS = [2, 2, 9, 2];
const LAST_LAYER_IDX = CANONICAL_LAYERS.length - 1;

const STAGE_LABELS = [
  "STAGE 01: INGRESS & ROUTING",
  "STAGE 02: PLANNING & MISSION CONTROL",
  "STAGE 03: SPECIALIZED AGENT FLEET",
  "STAGE 04: VERIFICATION & RESPONSE"
];

const CANONICAL_AGENTS = [
  // Stage 01: Ingress & Routing
  [
    {
      id: "router",
      name: "Fast Router",
      tag: "INTENT CLASSIFIER",
      model: "Qwen3 0.6B Q8_0",
      type: "routing",
      role: "Classifies intent in <50ms across 5 modes: CHAT, TASK, MISSION, MEMORY, CLARIFICATION.",
      matchKeys: ["router", "fast router", "intent router", "classify"]
    },
    {
      id: "supervisor",
      name: "Canonical Supervisor",
      tag: "ORCHESTRATOR",
      model: "Qwen3 1.7B Q8_0",
      type: "supervisor",
      role: "Coordinates execution pipeline, delegates to specialists, and oversees mission execution.",
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
      role: "Tracks multi-step state, step dependencies, and manages 3-retry bounded recovery loops.",
      matchKeys: ["mission manager", "mission", "task manager", "mission engine"]
    },
    {
      id: "planner",
      name: "Lead Planner",
      tag: "TASK DECOMPOSER",
      model: "Qwen3 1.7B Q8_0",
      type: "planner",
      role: "Decomposes complex goals into explicit, ordered, verifiable plan steps with assigned tools.",
      matchKeys: ["planner", "lead planner", "task decomposition", "plan"]
    }
  ],
  // Stage 03: Specialized Agent Fleet
  [
    {
      id: "developer",
      name: "Developer Agent",
      tag: "CODE GEN & REFACTOR",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Repository inspection, code synthesis, refactoring, and filesystem operations.",
      capabilities: ["filesystem.read", "filesystem.write", "filesystem.create_directory", "filesystem.delete", "terminal.execute"],
      matchKeys: ["developer", "code", "dev", "scaffold", "refactor"]
    },
    {
      id: "debugger",
      name: "Debugger Agent",
      tag: "ROOT-CAUSE DIAGNOSIS",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Analyzes stack traces, identifies root causes, and generates automated remediation patches.",
      capabilities: ["terminal.execute", "filesystem.read", "filesystem.write"],
      matchKeys: ["debugger", "debug", "diagnose", "root cause", "patch"]
    },
    {
      id: "tester",
      name: "Tester Agent",
      tag: "TEST SUITE RUNNER",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Executes unit, integration, and end-to-end tests to verify assertions and exit codes.",
      capabilities: ["terminal.run_tests", "terminal.execute", "filesystem.read"],
      matchKeys: ["tester", "test", "pytest", "assertion", "test runner"]
    },
    {
      id: "reviewer",
      name: "Reviewer Agent",
      tag: "QUALITY & SECURITY",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Inspects code changes for architectural adherence, security guidelines, and safety policies.",
      capabilities: ["filesystem.read"],
      matchKeys: ["reviewer", "review", "audit", "compliance", "lint"]
    },
    {
      id: "web",
      name: "Web Agent",
      tag: "LIVE SEARCH & CRAWL",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Fetches live web content and documentation across the untrusted external boundary.",
      capabilities: ["web.search", "web.crawl", "web.extract_structured"],
      matchKeys: ["web", "web agent", "search", "crawl", "scrape"]
    },
    {
      id: "research",
      name: "Research Agent",
      tag: "SYNTHESIS & FACT-CHECK",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Synthesizes multi-source facts, combining live web search with internal RAG memory.",
      capabilities: ["web.search", "web.crawl", "rag.search"],
      matchKeys: ["research", "research agent", "fact check", "synthesis"]
    },
    {
      id: "automation",
      name: "Automation Agent",
      tag: "DESKTOP & OS ACTIONS",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Launches installed native desktop applications and interacts with OS files.",
      capabilities: ["desktop.launch_app", "desktop.open_file", "desktop.hotkey"],
      matchKeys: ["automation", "automation agent", "launch", "desktop", "os"]
    },
    {
      id: "browser",
      name: "Browser Agent",
      tag: "PLAYWRIGHT DOM",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Navigates browser DOM, fills forms, clicks elements, and executes web interaction flows.",
      capabilities: ["browser.open", "browser.navigate", "browser.click", "browser.type", "browser.extract"],
      matchKeys: ["browser", "browser agent", "playwright", "dom", "click"]
    },
    {
      id: "rag",
      name: "RAG / Knowledge Agent",
      tag: "CHROMA EMBEDDINGS",
      model: "Qwen3 1.7B Q8_0",
      type: "specialist",
      role: "Queries and indexes persistent ChromaDB vector collections and project documentation.",
      capabilities: ["rag.search", "rag.index", "rag.ingest"],
      matchKeys: ["rag", "rag agent", "knowledge", "chroma", "vector", "memory"]
    }
  ],
  // Stage 04: Verification & Response
  [
    {
      id: "verifier",
      name: "Ground-Truth Verifier",
      tag: "PHYSICAL CRITIC",
      model: "Deterministic Logic",
      type: "verifier",
      role: "Physical state validator. Asserts file existence, process health, and verified exit codes.",
      capabilities: ["filesystem.exists", "process.running", "tests.passed"],
      matchKeys: ["verifier", "ground truth", "critic", "verification", "physical state"]
    },
    {
      id: "response",
      name: "Response Engine",
      tag: "EVIDENCE SYNTHESIZER",
      model: "Llama 3.2 1B Instruct",
      type: "response",
      role: "Synthesizes final tactical responses strictly grounded in physically verified evidence.",
      matchKeys: ["response", "response engine", "synthesizer", "jarvis"]
    }
  ]
];

// Helper: match agent string or ID to node coordinates
function findAgentNode(agentIdentifier) {
  if (!agentIdentifier) return null;
  const lower = String(agentIdentifier).toLowerCase().trim();
  for (let l = 0; l < CANONICAL_AGENTS.length; l++) {
    for (let i = 0; i < CANONICAL_AGENTS[l].length; i++) {
      const node = CANONICAL_AGENTS[l][i];
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
    CANONICAL_AGENTS.forEach((layer) => {
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
        const matched = findAgentNode(agentId || evt.agent?.name || evt.agent_name || evt.agent);
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
          const reqAgent = findAgentNode(evt.agent_id || evt.agent?.name);
          if (reqAgent) {
            states[reqAgent.node.id].currentTool = evt.tool;
            states[reqAgent.node.id].status = 'RUNNING';
          }
        } else if (evt.event_type === 'TOOL_COMPLETED') {
          const reqAgent = findAgentNode(evt.agent_id || evt.agent?.name);
          if (reqAgent) {
            states[reqAgent.node.id].currentTool = null;
          }
        }
      });
    }

    // Reflect currently active agent if provided by parent
    if (activeAgent && isLoading) {
      const matched = findAgentNode(activeAgent);
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

  // ==================== NEURAL CANVAS LIVING TOPOLOGY GRAPH ====================
  useEffect(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return;
    const ctx = canvas.getContext("2d");

    let raf;
    let W = 0;
    let H = 0;
    let radius = 18;
    let nodes = [];
    let pulses = [];
    let mouse = { x: -999, y: -999 };

    const layout = () => {
      const rect = wrap.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      W = rect.width;
      H = rect.height;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      radius = Math.max(16, Math.min(22, W / 48));

      // Calculate node positions across 4 stages
      nodes = CANONICAL_LAYERS.map((count, layerIdx) => {
        const x = ((layerIdx + 0.5) / CANONICAL_LAYERS.length) * W;
        return Array.from({ length: count }, (_, nodeIdx) => {
          const y = ((nodeIdx + 0.5) / count) * (H - 80) + 45;
          return { x, y, layerIdx, nodeIdx };
        });
      });
    };

    triggerPulseRef.current = () => {
      const now = performance.now();
      for (let l = 0; l < LAST_LAYER_IDX; l++) {
        for (let i = 0; i < CANONICAL_LAYERS[l]; i++) {
          for (let j = 0; j < CANONICAL_LAYERS[l + 1]; j++) {
            if (Math.random() < 0.4) {
              pulses.push({
                l,
                i,
                j,
                born: now + l * 200,
                dur: 600,
                speed: 1.0
              });
            }
          }
        }
      }
    };

    const frame = (now) => {
      ctx.clearRect(0, 0, W, H);

      // Clean finished pulses
      pulses = pulses.filter((p) => now - p.born < p.dur);

      // Draw Axon Connections
      for (let l = 0; l < LAST_LAYER_IDX; l++) {
        for (let i = 0; i < CANONICAL_LAYERS[l]; i++) {
          const fromNode = nodes[l]?.[i];
          if (!fromNode) continue;
          const fromAgentId = CANONICAL_AGENTS[l][i].id;
          const isFromActive = agentStateMap[fromAgentId]?.status === 'RUNNING';

          for (let j = 0; j < CANONICAL_LAYERS[l + 1]; j++) {
            const toNode = nodes[l + 1]?.[j];
            if (!toNode) continue;
            const toAgentId = CANONICAL_AGENTS[l + 1][j].id;
            const isToActive = agentStateMap[toAgentId]?.status === 'RUNNING';

            const isPathActive = isFromActive || isToActive;

            // Draw connection line
            ctx.beginPath();
            ctx.moveTo(fromNode.x, fromNode.y);
            ctx.lineTo(toNode.x, toNode.y);

            ctx.strokeStyle = isPathActive
              ? "rgba(239, 68, 68, 0.7)"
              : "rgba(63, 63, 70, 0.25)";
            ctx.lineWidth = isPathActive ? 1.8 : 0.8;
            ctx.stroke();
          }
        }
      }

      // Draw Synaptic Sparks / Pulses
      ctx.globalCompositeOperation = "lighter";
      for (const p of pulses) {
        const t = (now - p.born) / p.dur;
        if (t < 0 || t > 1) continue;

        const fromNode = nodes[p.l]?.[p.i];
        const toNode = nodes[p.l + 1]?.[p.j];
        if (!fromNode || !toNode) continue;

        const px = fromNode.x + (toNode.x - fromNode.x) * t;
        const py = fromNode.y + (toNode.y - fromNode.y) * t;

        ctx.fillStyle = "rgba(255, 100, 120, 0.9)";
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalCompositeOperation = "source-over";

      // Draw Agent Nodes
      for (let l = 0; l < CANONICAL_LAYERS.length; l++) {
        for (let i = 0; i < CANONICAL_LAYERS[l]; i++) {
          const n = nodes[l]?.[i];
          if (!n) continue;

          const agentDef = CANONICAL_AGENTS[l][i];
          const state = agentStateMap[agentDef.id] || { status: 'IDLE' };
          const isNodeActive = state.status === 'RUNNING' || state.status === 'RECOVERING';
          const isCompleted = state.status === 'COMPLETED';
          const isFailed = state.status === 'FAILED';
          const isHovered = hoveredAgent && hoveredAgent.id === agentDef.id;

          const r = radius * (isNodeActive ? 1.25 : 1.0);

          // 1. Bloom Aura Glow for Active Nodes
          if (isNodeActive) {
            ctx.globalCompositeOperation = "lighter";
            const bloomRadius = r * 3.8;
            const bloom = ctx.createRadialGradient(n.x, n.y, r * 0.2, n.x, n.y, bloomRadius);
            bloom.addColorStop(0, "rgba(255, 60, 80, 0.95)");
            bloom.addColorStop(0.4, "rgba(239, 68, 68, 0.5)");
            bloom.addColorStop(1, "rgba(220, 38, 38, 0)");
            ctx.fillStyle = bloom;
            ctx.beginPath();
            ctx.arc(n.x, n.y, bloomRadius, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalCompositeOperation = "source-over";

            // Pulsing Reticle Ring
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.7 + 0.3 * Math.sin(now * 0.008)})`;
            ctx.lineWidth = 2.0;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 5 + Math.sin(now * 0.008) * 3, 0, Math.PI * 2);
            ctx.stroke();
          }

          // 2. Node Sphere Body
          const grad = ctx.createRadialGradient(n.x - r * 0.3, n.y - r * 0.3, r * 0.05, n.x, n.y, r);
          if (isNodeActive) {
            grad.addColorStop(0, "rgb(255, 240, 245)");
            grad.addColorStop(0.4, "rgb(239, 68, 68)");
            grad.addColorStop(1, "rgb(153, 27, 27)");
          } else if (isCompleted) {
            grad.addColorStop(0, "rgb(220, 252, 231)");
            grad.addColorStop(0.4, "rgb(34, 197, 94)");
            grad.addColorStop(1, "rgb(20, 83, 45)");
          } else if (isFailed) {
            grad.addColorStop(0, "rgb(254, 226, 226)");
            grad.addColorStop(0.4, "rgb(220, 38, 38)");
            grad.addColorStop(1, "rgb(127, 29, 29)");
          } else {
            grad.addColorStop(0, isHovered ? "rgb(225, 29, 72)" : "rgb(120, 20, 30)");
            grad.addColorStop(0.5, isHovered ? "rgb(159, 18, 57)" : "rgb(70, 10, 20)");
            grad.addColorStop(1, "rgb(24, 24, 27)");
          }

          ctx.fillStyle = grad;
          ctx.strokeStyle = isNodeActive
            ? "#ffffff"
            : (isCompleted ? "#4ade80" : (isHovered ? "#f43f5e" : "#52525b"));
          ctx.lineWidth = isNodeActive ? 2.2 : (isHovered ? 2.0 : 1.2);
          ctx.beginPath();
          ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();

          // 3. Specular Glint
          ctx.fillStyle = "#ffffff";
          ctx.beginPath();
          ctx.arc(n.x - r * 0.32, n.y - r * 0.32, r * 0.22, 0, Math.PI * 2);
          ctx.fill();

          // 4. Node Label Text
          ctx.textAlign = "center";
          ctx.font = `bold ${Math.max(9, Math.min(11, W / 100))}px 'JetBrains Mono', monospace`;
          ctx.fillStyle = isNodeActive ? "#ffffff" : (isCompleted ? "#86efac" : (isHovered ? "#ffffff" : "#a1a1aa"));
          ctx.fillText(agentDef.name, n.x, n.y + r + 13);

          // 5. Active Tool or Status Badge
          ctx.font = "8px 'JetBrains Mono', monospace";
          if (state.currentTool) {
            ctx.fillStyle = "#f87171";
            ctx.fillText(`⚡ ${state.currentTool}`, n.x, n.y + r + 24);
          } else if (isNodeActive) {
            ctx.fillStyle = "#ef4444";
            ctx.fillText("● RUNNING", n.x, n.y + r + 24);
          } else if (isCompleted) {
            ctx.fillStyle = "#4ade80";
            ctx.fillText("✓ DONE", n.x, n.y + r + 24);
          } else if (isFailed) {
            ctx.fillStyle = "#f87171";
            ctx.fillText("✗ FAILED", n.x, n.y + r + 24);
          }
        }
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

      // Find hovered node
      let found = null;
      nodes.forEach((layer, l) => {
        layer.forEach((n, i) => {
          if (Math.hypot(n.x - mx, n.y - my) < radius + 12) {
            found = CANONICAL_AGENTS[l][i];
          }
        });
      });
      setHoveredAgent(found);
    };

    const onLeave = () => {
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
            clicked = CANONICAL_AGENTS[l][i];
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
  }, [agentStateMap, hoveredAgent]);

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
        <div className="absolute top-10 left-0 right-0 grid grid-cols-4 px-4 text-center z-20 pointer-events-none">
          {STAGE_LABELS.map((lbl, idx) => (
            <div key={idx} className="text-[9px] font-extrabold text-zinc-500 uppercase tracking-wider">
              {lbl}
            </div>
          ))}
        </div>

        {/* The Live Canvas */}
        <div ref={wrapRef} className="w-full h-[580px] min-h-[540px] relative">
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
