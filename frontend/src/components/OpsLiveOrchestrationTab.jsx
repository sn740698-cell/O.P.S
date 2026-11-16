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
  Zap,
  Sparkles,
  Copy,
  Check,
  Volume2
} from 'lucide-react';
import MarkdownRenderer from './MarkdownRenderer';
import CockpitLoadingSkeleton from './skeletons/CockpitLoadingSkeleton';
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

const LAYERS = [2, 4, 8, 8, 3];
const LAST = LAYERS.length - 1;

const STAGE_LABELS = [
  "GROUP 01: GLOBAL INTELLIGENCE",
  "GROUP 02: ANSWERING ENGINE",
  "GROUP 03: BROWSER SPECIALIST FLEET",
  "GROUP 04: DESKTOP SPECIALIST FLEET",
  "GROUP 05: COORDINATION & DELIVERY"
];

const AGENT_NODES = [
  // Group 01: Global Intelligence (2 Reasoning Agents)
  [
    {
      id: "global_intent_router",
      name: "Global Intent Router",
      tag: "INTENT ROUTER",
      model: "Qwen3 0.6B Q8_0",
      type: "reasoning_agent",
      role: "Determines directive category (ANSWER, AUTOMATION, COMPOSITE, CLARIFICATION) and response mode in <100ms.",
      tool: "Ollama Qwen3 0.6B Fast Classifier",
      parent: "USER DIRECTIVE",
      child: "Task Understanding & Planner",
      matchKeys: ["global_intent_router", "router", "intent", "request_understanding", "request_router", "fast_route"]
    },
    {
      id: "task_understanding_planner",
      name: "Task Understanding & Planner",
      tag: "SUPERVISOR AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "reasoning_agent",
      role: "Decomposes directives into execution plans, subtasks, agent dependencies, and approval gates.",
      tool: "Ollama Qwen3 1.7B Orchestrator",
      parent: "Global Intent Router",
      child: "Group 2 / Group 3 / Group 4 / Group 5",
      matchKeys: ["task_understanding_planner", "task_planner", "supervisor", "research_planner", "planner"]
    }
  ],
  // Group 02: Answering Engine (4 Agents)
  [
    {
      id: "local_reasoning_agent",
      name: "Local Reasoning Agent",
      tag: "REASONING AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "reasoning_agent",
      role: "Direct LLM reasoning for coding, logic, conceptual queries, and prior context synthesis.",
      tool: "Ollama Qwen3 1.7B Local Reasoner",
      parent: "Task Understanding & Planner",
      child: "Answer Synthesis / Result Formatter",
      matchKeys: ["local_reasoning_agent", "fast_route", "local_reasoning", "reasoning_engine"]
    },
    {
      id: "web_research_agent",
      name: "Web Research Agent",
      tag: "RESEARCH FLEET",
      model: "HTTPX, Crawlee, BS4, Playwright",
      type: "execution_worker",
      role: "Executes search query generation, URL discovery, concurrent crawling, and HTML extraction.",
      tool: "Brave Search, Crawlee, Playwright, BS4",
      parent: "Task Understanding & Planner",
      child: "Evidence Validation Agent",
      matchKeys: ["web_research_agent", "web_prep", "search_worker", "crawling_worker", "browser_rendering_worker", "content_extraction_worker", "content_processing_worker"]
    },
    {
      id: "evidence_validation_agent",
      name: "Evidence Validation Agent",
      tag: "VERIFICATION AGENT",
      model: "Fact & Grounding Verifier",
      type: "reasoning_agent",
      role: "Validates retrieved claims against scraped passages, filters contradictions, and scores evidence sufficiency.",
      tool: "Evidence Grounding Engine",
      parent: "Web Research Agent",
      child: "Answer Synthesis Agent",
      matchKeys: ["evidence_validation_agent", "evidence_analysis", "evidence_retrieval_worker", "adaptive_controller"]
    },
    {
      id: "answer_synthesis_agent",
      name: "Answer Synthesis Agent",
      tag: "SYNTHESIS AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "reasoning_agent",
      role: "Synthesizes multi-source evidence with bracketed citations [1], [2] into unified answers.",
      tool: "Ollama Qwen3 1.7B Synthesizer",
      parent: "Evidence Validation Agent",
      child: "Result Formatter Agent",
      matchKeys: ["answer_synthesis_agent", "answer_generation", "citation_result_worker"]
    }
  ],
  // Group 03: Browser Specialist Fleet (8 Specialist Agents B01-B08)
  [
    {
      id: "b1_lifecycle_agent",
      name: "Browser Lifecycle Agent",
      tag: "B1: LIFECYCLE",
      model: "Playwright Headed/Headless",
      type: "execution_worker",
      role: "Manages Chromium instance lifecycle, process flags, persistent contexts, and clean shutdowns.",
      tool: "Playwright Browser Launcher",
      parent: "Task Understanding & Planner",
      child: "Tab Management Agent",
      matchKeys: ["b1_lifecycle", "browser_lifecycle", "lifecycle_agent", "playwright_browser", "browser_automation_executor"]
    },
    {
      id: "b2_tab_agent",
      name: "Tab Management Agent",
      tag: "B2: TAB MGR",
      model: "Playwright Context",
      type: "execution_worker",
      role: "Controls multi-tab sessions, opening, closing, switching, and tracking active tabs across operations.",
      tool: "Playwright Page Controller",
      parent: "Browser Lifecycle Agent",
      child: "Website Resolution Agent",
      matchKeys: ["b2_tab", "tab_management", "tab_agent"]
    },
    {
      id: "b3_resolution_agent",
      name: "Website Resolution Agent",
      tag: "B3: RESOLUTION",
      model: "Fast URL Resolver",
      type: "reasoning_agent",
      role: "Resolves natural-language requests and service names (e.g. 'Spotify', 'GitHub') into validated URLs.",
      tool: "DNS & URL Resolution Protocol",
      parent: "Tab Management Agent",
      child: "Browser Navigation Agent",
      matchKeys: ["b3_resolution", "website_resolution", "resolution_agent"]
    },
    {
      id: "b4_navigation_agent",
      name: "Browser Navigation Agent",
      tag: "B4: NAVIGATION",
      model: "Playwright Router",
      type: "execution_worker",
      role: "Handles URL loads, dynamic SPA transitions, HTTP redirects, and network-idle wait states.",
      tool: "Playwright Goto & Wait State",
      parent: "Website Resolution Agent",
      child: "Web Interaction Agent",
      matchKeys: ["b4_navigation", "browser_navigation", "navigation_agent"]
    },
    {
      id: "b5_interaction_agent",
      name: "Web Interaction Agent",
      tag: "B5: INTERACTION",
      model: "DOM Accessibility Tree",
      type: "execution_worker",
      role: "Executes element clicks, scrolling, hover actions, typing, and DOM event dispatching.",
      tool: "Playwright Pointer & Click Engine",
      parent: "Browser Navigation Agent",
      child: "Form & Transfer Agent",
      matchKeys: ["b5_interaction", "web_interaction", "interaction_agent"]
    },
    {
      id: "b6_form_agent",
      name: "Form & Transfer Agent",
      tag: "B6: FORM & DATA",
      model: "Form Fill & Extract Engine",
      type: "execution_worker",
      role: "Handles input fields, credential autofill, file uploads, and downloaded web artifacts.",
      tool: "Playwright Input & File Handler",
      parent: "Web Interaction Agent",
      child: "Browser Verification Agent",
      matchKeys: ["b6_form", "form_extraction", "b6_transfer", "transfer_agent"]
    },
    {
      id: "b7_verification_agent",
      name: "Browser Verification Agent",
      tag: "B7: VERIFICATION",
      model: "DOM & Visual Asserter",
      type: "reasoning_agent",
      role: "Verifies page title, URL destinations, selector presence, and screenshot visual proofs.",
      tool: "Playwright Assertion Engine",
      parent: "Form & Transfer Agent",
      child: "Browser Recovery Agent / Task Bridger",
      matchKeys: ["b7_verification", "browser_verification", "verification_agent"]
    },
    {
      id: "b8_recovery_agent",
      name: "Browser Recovery Agent",
      tag: "B8: RECOVERY",
      model: "Self-Healing Overlay Healer",
      type: "reasoning_agent",
      role: "Recovers broken pages, handles popups, cookie consent overlays, and auto-retries failed steps.",
      tool: "Playwright Dialog & Healer",
      parent: "Browser Verification Agent",
      child: "Composite Task Coordinator",
      matchKeys: ["b8_recovery", "browser_recovery", "recovery_agent"]
    }
  ],
  // Group 04: Desktop Specialist Fleet (8 Specialist Agents D01-D08)
  [
    {
      id: "d1_discovery_agent",
      name: "App Discovery Agent",
      tag: "D1: DISCOVERY",
      model: "Win32 Registry & System Path",
      type: "execution_worker",
      role: "Discovers installed Windows apps, executable paths, UWP apps, and active system processes.",
      tool: "Windows System Registry Scanner",
      parent: "Task Understanding & Planner",
      child: "App Lifecycle Agent",
      matchKeys: ["d1_discovery", "app_discovery", "application_discovery"]
    },
    {
      id: "d2_app_agent",
      name: "App Lifecycle Agent",
      tag: "D2: APP LIFECYCLE",
      model: "Subprocess & Win32 Process",
      type: "execution_worker",
      role: "Launches native applications, manages PID tracking, and graceful application termination.",
      tool: "Process Execution Controller",
      parent: "App Discovery Agent",
      child: "Window Management Agent",
      matchKeys: ["d2_app", "app_lifecycle", "application_lifecycle"]
    },
    {
      id: "d3_window_agent",
      name: "Window Management Agent",
      tag: "D3: WINDOW MGR",
      model: "Win32 DWM Controller",
      type: "execution_worker",
      role: "Focuses, minimizes, maximizes, positions, and brings native windows to foreground.",
      tool: "win32gui & win32process",
      parent: "App Lifecycle Agent",
      child: "GUI Interaction Agent",
      matchKeys: ["d3_window", "window_management", "window_agent"]
    },
    {
      id: "d4_gui_agent",
      name: "GUI Interaction Agent",
      tag: "D4: GUI INTERACTION",
      model: "Pywinauto UIA / Win32",
      type: "execution_worker",
      role: "Interacts with native desktop UI elements, buttons, menus, and controls via UIA.",
      tool: "Pywinauto Accessibility Tree",
      parent: "Window Management Agent",
      child: "Keyboard & Input Agent",
      matchKeys: ["d4_gui", "gui_interaction", "pywinauto", "desktop_automation_executor"]
    },
    {
      id: "d5_input_agent",
      name: "Keyboard & Input Agent",
      tag: "D5: KEYBOARD & INPUT",
      model: "Win32 SendInput / PyAutoGUI",
      type: "execution_worker",
      role: "Synthesizes native keystrokes, shortcuts, hotkeys, text typing, and mouse coordinates.",
      tool: "Low-Level Input Driver",
      parent: "GUI Interaction Agent",
      child: "File & Explorer Agent",
      matchKeys: ["d5_input", "keyboard_input", "input_agent"]
    },
    {
      id: "d6_file_agent",
      name: "File & Explorer Agent",
      tag: "D6: FILE & EXPLORER",
      model: "Shell32 / Explorer Engine",
      role: "Navigates directories, opens folders in Explorer, manages paths, and file dialogues.",
      tool: "Windows Shell32 / Path Resolver",
      parent: "Keyboard & Input Agent",
      child: "Code Injection Agent",
      matchKeys: ["d6_file", "file_explorer", "file_agent"]
    },
    {
      id: "d7_code_agent",
      name: "Code Injection Agent",
      tag: "D7: CODE GENERATOR",
      model: "Qwen3 1.7B Code Typist",
      type: "execution_worker",
      role: "Generates and injects clean code, scripts, and documentation into editors and IDEs.",
      tool: "Editor Clipboard & Type Engine",
      parent: "File & Explorer Agent",
      child: "Desktop Verification Agent",
      matchKeys: ["d7_code", "code_injection", "code_agent"]
    },
    {
      id: "d8_verification_agent",
      name: "Desktop Verification Agent",
      tag: "D8: VERIFICATION",
      model: "Process & Window Verifier",
      type: "reasoning_agent",
      role: "Inspects process existence, window titles, UI states, and verifies desktop postconditions.",
      tool: "AutomationVerifier Engine",
      parent: "Code Injection Agent",
      child: "Composite Task Coordinator / Safety Gate",
      matchKeys: ["d8_verification", "desktop_verification", "verification_recovery_agent", "verifier"]
    }
  ],
  // Group 05: Composite Coordination & Delivery (3 Agents)
  [
    {
      id: "hitl_safety_controller",
      name: "HITL & Safety Controller",
      tag: "SAFETY GATE",
      model: "SafetyPolicy Gatekeeper",
      type: "adaptive_controller",
      role: "Enforces non-bypassable human approval for destructive operations and system actions.",
      tool: "SafetyPolicy Risk Evaluator",
      parent: "Supervisor / Fleets",
      child: "Composite Task Coordinator",
      matchKeys: ["hitl_safety_controller", "safety_controller", "safety_gate", "safety_policy"]
    },
    {
      id: "composite_task_coordinator",
      name: "Composite Task Coordinator",
      tag: "TASK BRIDGER",
      model: "Cross-Engine Coordinator",
      type: "reasoning_agent",
      role: "Bridges multi-phase directives combining web research, browser automation, and desktop actions.",
      tool: "Composite Directive Coordinator",
      parent: "Browser & Desktop Fleets",
      child: "Result Formatter Agent",
      matchKeys: ["composite_task_coordinator", "composite_coordinator", "task_coordinator", "hybrid_coordinator"]
    },
    {
      id: "result_formatter_agent",
      name: "Result Formatter (Output Engine)",
      tag: "DELIVERY AGENT",
      model: "Qwen3 1.7B Q8_0",
      type: "reasoning_agent",
      role: "Delivers the final output in articulate O.P.S. synthesis, compiles bibliographies, and appends telemetry.",
      tool: "Ollama Qwen3 1.7B Delivery Engine",
      parent: "Composite Task Coordinator / Synthesis Agent",
      child: "END",
      matchKeys: ["result_formatter_agent", "result_formatter", "chat_manager", "output_engine"]
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

const findAgentNode = findActiveNode;

export default function OpsLiveOrchestrationTab({
  activeAgent,
  currentThought,
  planSteps,
  isLoading,
  onDispatchPrompt,
  briefingText,
  streamingChunk = '',
  activeTaskPrompt = '',
  conversationHistory = [],
  onSpeakText,
  sessionId,
  onClearMemory,
  onStopExecution,
  liveEvents = []
}) {
  const [quickInput, setQuickInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [hoveredAgent, setHoveredAgent] = useState(null);
  const lastHoverIdRef = useRef(null);
  const [copied, setCopied] = useState(false);

  // Derived Real-Time Agent State Map derived from actual backend events
  const agentStateMap = useMemo(() => {
    const states = {};

    // Default all agents to IDLE
    AGENT_NODES.forEach((layer) => {
      layer.forEach((agent) => {
        states[agent.id] = {
          status: 'IDLE',
          currentTool: agent.tool || null,
          taskSummary: agent.role || null,
          outputSummary: null,
          startTimestamp: null,
          completionTimestamp: null,
          duration: null,
          lastMessage: null,
          lastUpdated: null,
          error: null,
          retryCount: 0,
          executions: 0
        };
      });
    });

    // Reduce live events into canonical agent states
    if (liveEvents && liveEvents.length > 0) {
      liveEvents.forEach((evt) => {
        const agentKey = evt.node_id || evt.component_name || evt.agent?.id || evt.agent_id || evt.agent?.name || evt.agent;
        const matched = findActiveNode(agentKey);
        if (matched) {
          const id = matched.node.id;
          const status = evt.execution_status || evt.status || 'RUNNING';
          const prev = states[id];

          const startTs = evt.event_type === 'NODE_STARTED' ? evt.timestamp : prev.startTimestamp;
          const endTs = (evt.event_type === 'NODE_COMPLETED' || evt.event_type === 'NODE_SKIPPED') ? evt.timestamp : prev.completionTimestamp;
          let dur = prev.duration;
          if (startTs && endTs && endTs >= startTs) {
            dur = (endTs - startTs).toFixed(2) + 's';
          }

          states[id] = {
            ...prev,
            status: status,
            currentTool: evt.tool_name || evt.tool || prev.currentTool,
            taskSummary: evt.safe_task_summary || evt.message || prev.taskSummary,
            outputSummary: evt.safe_output_summary || prev.outputSummary,
            startTimestamp: startTs,
            completionTimestamp: endTs,
            duration: dur,
            lastMessage: evt.safe_task_summary || evt.safe_output_summary || evt.message || prev.lastMessage,
            lastUpdated: evt.timestamp || Date.now(),
            error: status === 'FAILED' ? (evt.error_details || evt.message || 'Execution error') : null,
            retryCount: evt.event_type === 'ROUTING_DECISION' ? (prev.retryCount + 1) : prev.retryCount,
            executions: prev.executions + 1
          };
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

  // Canvas DOM refs and execution state tracking
  const wrapRef = useRef(null);
  const canvasRef = useRef(null);
  const triggerPulseRef = useRef(null);
  const activeAgentRef = useRef(activeAgent);
  const isLoadingRef = useRef(isLoading);

  useEffect(() => {
    activeAgentRef.current = activeAgent;
    isLoadingRef.current = isLoading;
  }, [activeAgent, isLoading]);

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

    // Canonical O.P.S. Architectural Pathways (Clean, purposeful connections - zero chaotic clutter)
    const CANONICAL_PATHWAYS = [
      // 1. Group 01: Global Intelligence Ingress
      { l1: 0, i: 0, l2: 0, j: 1, type: "ingress" }, // Intent Router -> Supervisor Agent

      // 2. Supervisor Dispatches to Answering Engine
      { l1: 0, i: 1, l2: 1, j: 0, type: "dispatch" }, // Supervisor -> Reasoning Agent
      { l1: 0, i: 1, l2: 1, j: 1, type: "dispatch" }, // Supervisor -> Web Research Fleet

      // 3. Group 02: Answering Engine Pipeline
      { l1: 1, i: 0, l2: 1, j: 3, type: "reasoning", bow: -22 }, // Reasoning -> Synthesis
      { l1: 1, i: 1, l2: 1, j: 2, type: "pipeline" },            // Web Research -> Evidence Validation
      { l1: 1, i: 2, l2: 1, j: 3, type: "pipeline" },            // Evidence Validation -> Synthesis
      { l1: 1, i: 3, l2: 4, j: 2, type: "delivery", bow: 18 },   // Synthesis -> Delivery Agent

      // 4. Supervisor Dispatches to Automation Fleets & Safety
      { l1: 0, i: 1, l2: 2, j: 0, type: "dispatch" },           // Supervisor -> B1 Lifecycle
      { l1: 0, i: 1, l2: 3, j: 0, type: "dispatch", bow: 22 },  // Supervisor -> D1 Discovery
      { l1: 0, i: 1, l2: 4, j: 0, type: "safety", bow: -26 },   // Supervisor -> Safety Gate

      // 5. Group 03: Browser Specialist Fleet Sequential Pipeline (B1 -> B2 -> ... -> B8)
      { l1: 2, i: 0, l2: 2, j: 1, type: "fleet" },
      { l1: 2, i: 1, l2: 2, j: 2, type: "fleet" },
      { l1: 2, i: 2, l2: 2, j: 3, type: "fleet" },
      { l1: 2, i: 3, l2: 2, j: 4, type: "fleet" },
      { l1: 2, i: 4, l2: 2, j: 5, type: "fleet" },
      { l1: 2, i: 5, l2: 2, j: 6, type: "fleet" },
      { l1: 2, i: 6, l2: 2, j: 7, type: "fleet" },

      // 6. Group 04: Desktop Specialist Fleet Sequential Pipeline (D1 -> D2 -> ... -> D8)
      { l1: 3, i: 0, l2: 3, j: 1, type: "fleet" },
      { l1: 3, i: 1, l2: 3, j: 2, type: "fleet" },
      { l1: 3, i: 2, l2: 3, j: 3, type: "fleet" },
      { l1: 3, i: 3, l2: 3, j: 4, type: "fleet" },
      { l1: 3, i: 4, l2: 3, j: 5, type: "fleet" },
      { l1: 3, i: 5, l2: 3, j: 6, type: "fleet" },
      { l1: 3, i: 6, l2: 3, j: 7, type: "fleet" },

      // 7. Cross-Fleet Automation Bridge (Browser Download -> Desktop Explorer)
      { l1: 2, i: 5, l2: 3, j: 5, type: "bridge", bow: 0 },

      // 8. Fleets Convergence into Delivery & Safety
      { l1: 2, i: 6, l2: 4, j: 1, type: "delivery" }, // B7 Browser Verifier -> Task Bridger
      { l1: 2, i: 7, l2: 4, j: 1, type: "delivery" }, // B8 Recovery -> Task Bridger
      { l1: 3, i: 7, l2: 4, j: 0, type: "safety" },   // D8 Desktop Verifier -> Safety Gate
      { l1: 3, i: 7, l2: 4, j: 1, type: "delivery" }, // D8 Desktop Verifier -> Task Bridger

      // 9. Coordination & Delivery Pipeline
      { l1: 4, i: 0, l2: 4, j: 1, type: "pipeline" }, // Safety Gate -> Task Bridger
      { l1: 4, i: 1, l2: 4, j: 2, type: "pipeline" }, // Task Bridger -> Delivery Agent

      // 10. Adaptive Quality & Self-Healing Feedback Loops (Dashed curves)
      { l1: 2, i: 7, l2: 2, j: 3, bow: -36, type: "loop", isLoop: true }, // B8 Recovery -> B4 Navigation Retry
      { l1: 3, i: 7, l2: 3, j: 1, bow: 36, type: "loop", isLoop: true },  // D8 Verifier -> D2 App Lifecycle Retry
    ];

    // Initialize pathway channel aesthetics (3 living harmonic filaments & quantum packet streams)
    const pathwayMeta = CANONICAL_PATHWAYS.map((p, idx) => ({
      ...p,
      idx,
      hue: (idx / CANONICAL_PATHWAYS.length),
      speedMult: 0.85 + ((idx * 7) % 5) * 0.15,
      // Continuous quantum photon stream phases along each pathway
      quantaPhases: [
        ((idx * 0.29) % 1),
        ((idx * 0.29 + 0.5) % 1)
      ],
      // 3 living harmonic filaments with organic phase velocities
      filaments: [
        { offset: -2.0, ph: (idx * 0.9), amp: 2.8, freq: 2.0, speed: 0.0016 },
        { offset: 0.0, ph: (idx * 1.5 + Math.PI * 0.5), amp: 4.2, freq: 2.8, speed: 0.0024 },
        { offset: 2.0, ph: (idx * 2.3 + Math.PI), amp: 2.8, freq: 2.2, speed: 0.0019 }
      ]
    }));

    let nodes = [];
    let radius = 11;
    let width = 0;
    let height = 0;
    let pulses = [];
    let hover = null;
    let mouse = { x: -999, y: -999 };
    let raf;
    let last = performance.now();

    // Responsive layout calculation with guaranteed vertical clearances
    const layout = () => {
      const rect = wrap.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = Math.max(rect.height, 780);
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // 68px vertical gap guarantees >28px clean buffer between every badge and adjacent node
      const gap = 68;
      radius = 11;

      // 5 evenly distributed horizontal stage anchors across the canvas
      const xPercents = [0.09, 0.28, 0.49, 0.70, 0.90];

      nodes = LAYERS.map((n, l) =>
        Array.from({ length: n }, (_, i) => {
          const bx = width * xPercents[l];
          const by = height / 2 + 10 + (i - (n - 1) / 2) * gap;
          return {
            bx,
            by,
            x: bx,
            y: by,
            ph: Math.random() * TAU,
            hoverProgress: 0,
            activation: 0,
            glow: 0
          };
        })
      );
    };

    // Point on pathway generator (smooth cubic Bézier across stages, vertical spinal curve within fleets)
    const getPathwayPoint = (p, s, now, fl = null) => {
      const A = nodes[p.l1]?.[p.i];
      const B = nodes[p.l2]?.[p.j];
      if (!A || !B) return [0, 0];

      // Envelope: strictly 0 at s=0 and s=1, mathematically guaranteeing endpoints NEVER detach from node centers
      const env = Math.sin(Math.PI * s);
      const flOffset = fl ? fl.offset : 0;
      const flAmp = fl ? fl.amp : 3.0;
      const flPh = fl ? fl.ph : 0;
      const flSpeed = fl ? fl.speed : 0.002;
      const flFreq = fl ? fl.freq : 2.5;

      // Intra-column vertical pipeline flow (e.g. B1 -> B2 or self-healing loops)
      if (p.l1 === p.l2) {
        const xBase = A.x;
        const yBase = A.y + (B.y - A.y) * s;
        const lateralBow = p.bow || (p.isLoop ? (p.l1 === 2 ? -36 : 36) : 0);
        // Harmonic waves undulating horizontally: never disturbs y, so 0% vertical collision risk
        const wave1 = Math.sin(s * Math.PI * flFreq - now * flSpeed + flPh) * flAmp;
        const wave2 = Math.cos(s * Math.PI * 1.6 + now * 0.0012) * 1.4;
        const lateral = env * (lateralBow + wave1 + wave2) + flOffset * 0.8 * env;
        return [xBase + lateral, yBase];
      }

      // Inter-column horizontal flow (smooth cubic Bézier)
      const dx = (B.x - A.x) * 0.46;
      const x1 = A.x + dx, y1 = A.y;
      const x2 = B.x - dx, y2 = B.y;
      const u = 1 - s;
      const bx = u * u * u * A.x + 3 * u * u * s * x1 + 3 * u * s * s * x2 + s * s * s * B.x;
      const by = u * u * u * A.y + 3 * u * u * s * y1 + 3 * u * s * s * y2 + s * s * s * B.y;

      // Organic living fluid sinewave undulation with dual harmonics
      const wave1 = Math.sin(s * Math.PI * flFreq - now * flSpeed + flPh) * flAmp;
      const wave2 = Math.cos(s * Math.PI * 3.8 + now * (flSpeed * 0.8) + flPh) * 1.2;
      const lateralBow = (p.bow || 0) * env;
      return [bx, by + env * (wave1 + wave2) + lateralBow + flOffset * 0.6 * env];
    };

    // Color Tinting
    const tint = (hue, h) => {
      const base = mix([235, 45, 60], [255, 140, 160], hue);
      return mix(base, [255, 255, 255], Math.min(1, h * 0.7)).join(",");
    };

    // Trigger action potential pulse wave through active pathways
    const startPulseWave = (customL = null, customI = null) => {
      const activeAgent = activeAgentRef.current;
      const activeTarget = findActiveNode(activeAgent);
      const targetL = customL !== null ? customL : (activeTarget ? activeTarget.l : 0);
      const targetI = customI !== null ? customI : (activeTarget ? activeTarget.i : 0);

      // Find outgoing or incoming pathways from target
      const relevant = pathwayMeta.filter(p => 
        (p.l1 === targetL && p.i === targetI) ||
        (p.l2 === targetL && p.j === targetI)
      );
      const targets = relevant.length > 0 ? relevant : pathwayMeta.slice(0, 3);

      const now = performance.now();
      targets.forEach((path) => {
        pulses.push({
          path,
          born: now + Math.random() * 30,
          dur: TRAVEL * (0.75 + Math.random() * 0.25),
          v: 0.8
        });
      });
    };

    triggerPulseRef.current = startPulseWave;

    // Frame Animation Loop (Silky 60 FPS)
    const frame = (now) => {
      const dt = Math.min(now - last, 50);
      last = now;

      const activeAgent = activeAgentRef.current;
      const isLoading = isLoadingRef.current;
      const activeTarget = findActiveNode(activeAgent) || (isLoading ? { l: 0, i: 0, node: AGENT_NODES[0][0] } : null);
      const isSystemWorking = Boolean(isLoading && activeTarget);

      // Stable micro-breathing (horizontal sway <= 0.6px, zero vertical drift to avoid label jitter)
      nodes.forEach((layer) =>
        layer.forEach((n) => {
          n.x = n.bx + Math.sin(now * 0.0004 + n.ph) * 0.6;
          n.y = n.by; // Fixed vertical anchor guarantees zero vertical overlap!
        })
      );

      // Continuous pulse generation during active execution
      if (isSystemWorking && Math.random() < 0.08) {
        startPulseWave();
      }

      // Filter active pulses
      pulses = pulses.filter((p) => now - p.born < p.dur);

      // Stable Hit Test against fixed node anchor coordinates (eliminates hover strobing)
      hover = null;
      let activeHoverNodeMeta = null;
      nodes.forEach((layer, l) =>
        layer.forEach((n, i) => {
          if (Math.hypot(n.bx - mouse.x, n.by - mouse.y) < radius + 10) {
            hover = { l, i };
            if (AGENT_NODES[l] && AGENT_NODES[l][i]) {
              activeHoverNodeMeta = {
                ...AGENT_NODES[l][i],
                layerIdx: l,
                nodeIdx: i,
                x: n.x,
                y: n.y
              };
            }
          }
        })
      );

      // Smooth Spring Lerp for hover transitions on all nodes
      nodes.forEach((layer, l) =>
        layer.forEach((n, i) => {
          const isTarget = (hover && hover.l === l && hover.i === i) ? 1.0 : 0.0;
          n.hoverProgress += (isTarget - n.hoverProgress) * 0.16;
        })
      );

      // Deduplicated state update for Bottom HUD (never re-renders during tracking)
      const newHoverId = activeHoverNodeMeta ? activeHoverNodeMeta.id : null;
      if (newHoverId !== lastHoverIdRef.current) {
        lastHoverIdRef.current = newHoverId;
        setHoveredAgent(activeHoverNodeMeta);
        // Instantaneous synaptic burst along connected strings when hovering an agent!
        if (activeHoverNodeMeta && triggerPulseRef.current) {
          triggerPulseRef.current(activeHoverNodeMeta.layerIdx, activeHoverNodeMeta.nodeIdx);
        }
      }

      // ==================== RENDERING ====================
      ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = "#050508";
      ctx.fillRect(0, 0, width, height);

      // 1. Draw Subtle Tactical Grid
      ctx.strokeStyle = "rgba(220, 38, 38, 0.06)";
      ctx.lineWidth = 1;
      const step = 52;
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

      // 2. Draw Clean Canonical Synaptic Pathways
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      const SEG = 24;

      for (const p of pathwayMeta) {
        const nodeA = nodes[p.l1]?.[p.i];
        const nodeB = nodes[p.l2]?.[p.j];
        if (!nodeA || !nodeB) continue;

        const isConnectedHover = hover && (
          (hover.l === p.l1 && hover.i === p.i) ||
          (hover.l === p.l2 && hover.i === p.j)
        );
        const hoverIntensity = Math.max(nodeA.hoverProgress, nodeB.hoverProgress);
        const isPathActive = isSystemWorking && activeTarget && (
          (activeTarget.l === p.l1 && activeTarget.i === p.i) ||
          (activeTarget.l === p.l2 && activeTarget.i === p.j)
        );

        const isLoop = Boolean(p.isLoop);
        const baseColor = isLoop ? "245, 158, 11" : tint(p.hue, 0.2);

        // Standby baseline alpha boosted to 0.35 so strands are crisp and visible
        // When hovered, connected pathways burst to 0.95 with neon glow, unconnected pathways dim gently to 0.16
        const anyNodeHovered = Boolean(hover);
        let alpha = isPathActive ? 0.95 : isLoop ? 0.75 : (0.35 + hoverIntensity * 0.60);
        if (anyNodeHovered && !isConnectedHover) {
          alpha = Math.max(0.14, alpha * 0.45);
        }

        const lineWidth = isPathActive ? 1.8 : isLoop ? 1.3 : (0.9 + hoverIntensity * 0.8);

        // Dynamic animated glow halo on hovered and active pathways
        if (hoverIntensity > 0.08 || isPathActive) {
          ctx.save();
          ctx.globalCompositeOperation = "lighter";
          const haloAlpha = isPathActive ? 0.4 : (0.35 * hoverIntensity);
          ctx.strokeStyle = `rgba(244, 63, 94, ${haloAlpha})`;
          ctx.lineWidth = lineWidth * 3.6;
          ctx.beginPath();
          for (let q = 0; q <= SEG; q++) {
            const pt = getPathwayPoint(p, q / SEG, now, p.filaments[1]);
            if (q === 0) ctx.moveTo(pt[0], pt[1]);
            else ctx.lineTo(pt[0], pt[1]);
          }
          ctx.stroke();
          ctx.restore();
        }

        // Loop animation: scrolling dashed feedback loop
        if (isLoop) {
          ctx.setLineDash([6, 6]);
          ctx.lineDashOffset = -now * 0.024;
        } else {
          ctx.setLineDash([]);
        }

        // Draw living filaments
        for (const fl of p.filaments) {
          const pts = [];
          for (let q = 0; q <= SEG; q++) {
            pts.push(getPathwayPoint(p, q / SEG, now, fl));
          }

          ctx.strokeStyle = `rgba(${baseColor}, ${alpha})`;
          ctx.lineWidth = lineWidth;
          ctx.beginPath();
          pts.forEach(([x, y], q) => (q ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
          ctx.stroke();
        }

        ctx.setLineDash([]);
      }

      // 3. Draw Traveling Action Potentials & Continuous Quantum Streams
      ctx.globalCompositeOperation = "lighter";

      // 3A. Continuous Data Photons (Always running smoothly along all canonical pathways)
      for (const p of pathwayMeta) {
        const nodeA = nodes[p.l1]?.[p.i];
        const nodeB = nodes[p.l2]?.[p.j];
        if (!nodeA || !nodeB) continue;

        const isHoveredPath = hover && (
          (hover.l === p.l1 && hover.i === p.i) ||
          (hover.l === p.l2 && hover.i === p.j)
        );
        const isPathActive = isSystemWorking && activeTarget && (
          (activeTarget.l === p.l1 && activeTarget.i === p.i) ||
          (activeTarget.l === p.l2 && activeTarget.i === p.j)
        );

        // Speed surges dynamically when pathway is active or hovered
        const speedRate = isHoveredPath ? 0.00065 : isPathActive ? 0.00055 : 0.00024;
        const trailLength = isHoveredPath ? 0.09 : isPathActive ? 0.08 : 0.055;

        for (const phaseOffset of p.quantaPhases) {
          const t = ((now * speedRate * p.speedMult + phaseOffset) % 1 + 1) % 1;
          
          const headPt = getPathwayPoint(p, t, now, null);
          const midPt = getPathwayPoint(p, Math.max(0, t - trailLength * 0.5), now, null);
          const tailPt = getPathwayPoint(p, Math.max(0, t - trailLength), now, null);

          // Glowing comet tail
          const tailAlpha = isHoveredPath ? 0.95 : isPathActive ? 0.85 : 0.42;
          const streakW = isHoveredPath ? 2.5 : isPathActive ? 2.0 : 1.3;

          ctx.strokeStyle = isHoveredPath
            ? `rgba(255, 230, 230, ${tailAlpha})`
            : p.isLoop
            ? `rgba(251, 191, 36, ${tailAlpha})`
            : `rgba(255, 120, 140, ${tailAlpha})`;
          ctx.lineWidth = streakW;
          ctx.beginPath();
          ctx.moveTo(tailPt[0], tailPt[1]);
          ctx.lineTo(midPt[0], midPt[1]);
          ctx.lineTo(headPt[0], headPt[1]);
          ctx.stroke();

          // Luminous Photon Glow Head
          const glowRadius = isHoveredPath ? 8.5 : isPathActive ? 7.0 : 4.8;
          const halo = ctx.createRadialGradient(headPt[0], headPt[1], 0, headPt[0], headPt[1], glowRadius);
          halo.addColorStop(0, "rgba(255, 255, 255, 0.98)");
          halo.addColorStop(0.35, isHoveredPath ? "rgba(255, 80, 100, 0.85)" : "rgba(239, 68, 68, 0.65)");
          halo.addColorStop(1, "rgba(225, 29, 46, 0)");
          ctx.fillStyle = halo;
          ctx.beginPath();
          ctx.arc(headPt[0], headPt[1], glowRadius, 0, TAU);
          ctx.fill();

          // Tiny sharp white core
          ctx.fillStyle = "#ffffff";
          ctx.beginPath();
          ctx.arc(headPt[0], headPt[1], isHoveredPath ? 1.8 : 1.2, 0, TAU);
          ctx.fill();
        }
      }

      // 3B. High-Energy Action Potential Pulses (Triggered on dispatch, execution & hover enter)
      for (const pulse of pulses) {
        const t = (now - pulse.born) / pulse.dur;
        if (t < 0 || t > 1) continue;

        const p = pulse.path;
        const curPt = getPathwayPoint(p, t, now, null);
        const trailPt = getPathwayPoint(p, Math.max(0, t - 0.14), now, null);

        ctx.strokeStyle = "rgba(255, 255, 255, 0.98)";
        ctx.lineWidth = 2.6;
        ctx.beginPath();
        ctx.moveTo(trailPt[0], trailPt[1]);
        ctx.lineTo(curPt[0], curPt[1]);
        ctx.stroke();

        const halo = ctx.createRadialGradient(curPt[0], curPt[1], 0, curPt[0], curPt[1], 10);
        halo.addColorStop(0, "rgba(255, 255, 255, 1.0)");
        halo.addColorStop(0.4, "rgba(239, 68, 68, 0.75)");
        halo.addColorStop(1, "rgba(225, 29, 46, 0)");
        ctx.fillStyle = halo;
        ctx.beginPath();
        ctx.arc(curPt[0], curPt[1], 10, 0, TAU);
        ctx.fill();
      }

      ctx.globalCompositeOperation = "source-over";

      // 4. Draw 3D Agent Spheres & Badges (Rock-solid positioning with guaranteed clearance)
      for (let l = 0; l < LAYERS.length; l++) {
        for (let i = 0; i < LAYERS[l]; i++) {
          const n = nodes[l][i];
          const isNodeActive = isSystemWorking && activeTarget && activeTarget.l === l && activeTarget.i === i;
          const hp = n.hoverProgress || 0;
          const r = radius * (isNodeActive ? 1.25 : (1.0 + hp * 0.20));

          // A. Bloom Glow for Active Executing Node
          if (isNodeActive) {
            ctx.globalCompositeOperation = "lighter";
            const bloomRadius = r * 4.2;
            const bloom = ctx.createRadialGradient(n.x, n.y, r * 0.2, n.x, n.y, bloomRadius);
            bloom.addColorStop(0, "rgba(255, 70, 90, 0.95)");
            bloom.addColorStop(0.35, "rgba(239, 68, 68, 0.55)");
            bloom.addColorStop(1, "rgba(225, 29, 46, 0)");
            ctx.fillStyle = bloom;
            ctx.beginPath();
            ctx.arc(n.x, n.y, bloomRadius, 0, TAU);
            ctx.fill();
            ctx.globalCompositeOperation = "source-over";

            // Pulsing tactical ring
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.8 + 0.2 * Math.sin(now * 0.009)})`;
            ctx.lineWidth = 1.8;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 5 + Math.sin(now * 0.008) * 2.5, 0, TAU);
            ctx.stroke();
          }

          // B. Smooth Spring Hover Halo
          if (hp > 0.01 && !isNodeActive) {
            ctx.globalCompositeOperation = "lighter";
            const hoverHalo = ctx.createRadialGradient(n.x, n.y, r * 0.3, n.x, n.y, r * 2.5);
            hoverHalo.addColorStop(0, `rgba(255, 60, 80, ${0.42 * hp})`);
            hoverHalo.addColorStop(1, "rgba(225, 29, 46, 0)");
            ctx.fillStyle = hoverHalo;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r * 2.5, 0, TAU);
            ctx.fill();
            ctx.globalCompositeOperation = "source-over";

            ctx.strokeStyle = `rgba(255, 255, 255, ${0.9 * hp})`;
            ctx.lineWidth = 1.3;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r + 3 + (1 - hp) * 3, 0, TAU);
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
            const r0 = Math.round(175 + hp * 65);
            const g0 = Math.round(25 + hp * 25);
            const b0 = Math.round(42 + hp * 33);
            body.addColorStop(0, `rgb(${r0}, ${g0}, ${b0})`);
            body.addColorStop(0.5, hp > 0.5 ? "rgb(185, 25, 42)" : "rgb(115, 12, 22)");
            body.addColorStop(1, hp > 0.5 ? "rgb(100, 10, 18)" : "rgb(55, 5, 10)");
            ctx.fillStyle = body;
            ctx.strokeStyle = hp > 0.3 ? "rgb(255, 120, 140)" : "rgba(244, 63, 94, 0.85)";
            ctx.lineWidth = 1.4 + hp * 0.4;
            ctx.beginPath();
            ctx.arc(n.x, n.y, r, 0, TAU);
            ctx.fill();
            ctx.stroke();

            // Crisp Specular Glint
            ctx.fillStyle = `rgba(255, 255, 255, ${0.75 + hp * 0.2})`;
            ctx.beginPath();
            ctx.arc(n.x - r * 0.3, n.y - r * 0.3, r * 0.22, 0, TAU);
            ctx.fill();
          }

          // D. Tactical Badge (Fixed height 14px, zero vertical collision)
          const agentMeta = AGENT_NODES[l]?.[i];
          if (agentMeta) {
            const tagText = agentMeta.tag;
            ctx.font = "bold 8.5px 'JetBrains Mono', 'Geist Mono', monospace";
            const textMetrics = ctx.measureText(tagText);
            const pillW = textMetrics.width + 10;
            const pillH = 14;
            const pillX = n.x - pillW / 2;
            const pillY = n.y + r + 4;

            ctx.fillStyle = isNodeActive
              ? "rgba(220, 20, 40, 0.95)"
              : hp > 0.2
              ? "rgba(35, 8, 14, 0.92)"
              : "rgba(16, 16, 22, 0.90)";
            ctx.strokeStyle = isNodeActive
              ? "#ffffff"
              : hp > 0.2
              ? "#ef4444"
              : "rgba(239, 68, 68, 0.65)";
            ctx.lineWidth = 1;
            ctx.fillRect(pillX, pillY, pillW, pillH);
            ctx.strokeRect(pillX, pillY, pillW, pillH);

            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillStyle = isNodeActive ? "#ffffff" : hp > 0.2 ? "#ffffff" : "#f4f4f5";
            ctx.fillText(tagText, n.x, pillY + pillH / 2);
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
      mouse = { x: e.clientX - r.left, y: e.clientY - r.top };
    };

    const onLeave = () => {
      mouse = { x: -999, y: -999 };
      if (lastHoverIdRef.current !== null) {
        lastHoverIdRef.current = null;
        setHoveredAgent(null);
      }
    };

    const onDown = (e) => {
      const r = canvas.getBoundingClientRect();
      const mx = e.clientX - r.left;
      const my = e.clientY - r.top;

      let clicked = null;
      nodes.forEach((layer, l) => {
        layer.forEach((n, i) => {
          if (Math.hypot(n.bx - mx, n.by - my) < radius + 12) {
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
  }, []); // Run ONCE on mount: never tears down or re-randomizes on state transitions!

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

      {/* ==================== 1. ACTIVE DIRECTIVE & COCKPIT STATUS BANNER ==================== */}
      <div className="retro-box p-3 bg-[#09090b] border-zinc-800 flex flex-wrap items-center justify-between gap-3 font-mono">
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <span className="px-2 py-0.5 bg-red-600 text-white font-black text-xs border border-red-500 shadow-sm shrink-0 flex items-center gap-1">
            <Zap className="w-3.5 h-3.5 text-white fill-white" />
            <span>COCKPIT DIRECTIVE:</span>
          </span>
          <span className="text-xs font-bold text-white truncate max-w-2xl select-text">
            {activeTaskPrompt ? `"${activeTaskPrompt}"` : "(Awaiting directive from Desktop Popup Cockpit...)"}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1.5 text-[10px] px-2 py-1 bg-black border border-zinc-800">
            <span className="text-zinc-500 font-bold uppercase">STATUS:</span>
            <span className={isLoading ? "text-amber-400 font-bold animate-pulse" : "text-emerald-400 font-bold"}>
              {isLoading ? `[BUSY: ${activeAgent || 'ORCHESTRATING'}]` : "[STANDBY: READY]"}
            </span>
          </div>

          {/* STOP Real-Time Control Button */}
          {isLoading && onStopExecution && (
            <button
              onClick={() => onStopExecution()}
              title="STOP ongoing execution"
              className="px-2.5 py-1 text-xs bg-zinc-900 border border-zinc-700 hover:border-amber-500 hover:text-amber-400 text-zinc-300 flex items-center gap-1 font-bold transition"
            >
              <Square className="w-3.5 h-3.5 text-amber-500 fill-current" />
              <span>[ ⏹ STOP ]</span>
            </button>
          )}

          {/* REFRESH Session Button */}
          {onClearMemory && (
            <button
              onClick={() => onClearMemory()}
              disabled={isLoading}
              title="REFRESH session (Clears volatile context, creates new session ID)"
              className="px-2.5 py-1 text-xs bg-zinc-900 border border-zinc-700 hover:border-red-500 hover:text-red-400 text-zinc-300 flex items-center gap-1 font-bold transition disabled:opacity-40"
            >
              <RefreshCw className="w-3.5 h-3.5 text-red-500" />
              <span>[ ↻ REFRESH ]</span>
            </button>
          )}
        </div>
      </div>

      {/* ==================== AI EXECUTIVE RESPONSE & LIVE STREAMING OUTPUT ==================== */}
      {(isLoading || briefingText || streamingChunk || (conversationHistory && conversationHistory.some(m => m.role === 'assistant' || m.role === 'bot'))) && (
        <div className="retro-box-red p-4 bg-[#09090c] border border-red-900/80 shadow-2xl space-y-3 font-mono">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-zinc-800 pb-2.5">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-red-500 animate-pulse" />
              <span className="font-extrabold text-xs text-white uppercase tracking-wider">
                O.P.S. SYNTHESIZED EXECUTIVE BRIEFING
              </span>
              {activeAgent && (
                <span className="px-2 py-0.5 rounded text-[10px] bg-red-950 border border-red-800 text-red-400 font-bold">
                  [{activeAgent}]
                </span>
              )}
            </div>

            <div className="flex items-center gap-2">
              {briefingText && !isLoading && (
                <button
                  type="button"
                  onClick={() => {
                    const textToCopy = briefingText || [...(conversationHistory || [])].reverse().find(m => m.role === 'assistant' || m.role === 'bot')?.text || '';
                    navigator.clipboard.writeText(textToCopy);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 2000);
                  }}
                  className="px-2.5 py-1 text-[10px] font-bold bg-zinc-900 border border-zinc-700 hover:border-red-600 text-zinc-300 rounded flex items-center gap-1 transition"
                  title="Copy response to clipboard"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-zinc-400" />}
                  <span>{copied ? "COPIED" : "COPY"}</span>
                </button>
              )}

              {briefingText && onSpeakText && !isLoading && (
                <button
                  type="button"
                  onClick={() => onSpeakText(briefingText)}
                  className="px-2.5 py-1 text-[10px] font-bold bg-zinc-900 border border-zinc-700 hover:border-red-600 text-zinc-300 rounded flex items-center gap-1 transition"
                  title="Speak response"
                >
                  <Volume2 className="w-3 h-3 text-red-400" />
                  <span>TTS</span>
                </button>
              )}
            </div>
          </div>

          {/* Real-time Streaming Skeleton or Token Renderer */}
          {isLoading ? (
            <CockpitLoadingSkeleton
              query={activeTaskPrompt}
              activeAgent={activeAgent}
              currentThought={currentThought}
              streamingChunk={streamingChunk}
              onStopExecution={onStopExecution}
              compact={false}
            />
          ) : (
            <div className="text-xs text-zinc-200 leading-relaxed font-mono select-text">
              <MarkdownRenderer content={briefingText || [...(conversationHistory || [])].reverse().find(m => m.role === 'assistant' || m.role === 'bot')?.text || ''} />
            </div>
          )}
        </div>
      )}

      {/* ==================== 2. MAIN AUTHORITATIVE AGENT TOPOLOGY CANVAS ==================== */}
      <div className="relative bg-[#050505] border-2 border-zinc-800 rounded shadow-2xl overflow-hidden min-h-[780px]">
        {/* Subtle scanline overlay */}
        <div className="absolute inset-0 pointer-events-none opacity-20 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.5)_50%)] bg-[length:100%_4px] z-10" />

        {/* Top Header Overlay with LIVE TOPOLOGY status */}
        <div className="absolute top-2.5 left-4 right-4 flex items-center justify-between z-20 pointer-events-none">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 bg-red-600 text-white font-black text-[11px] border border-red-500 shadow">
              O.P.S. v3.0 ORCHESTRATION TOPOLOGY
            </span>
            <span className="text-[10px] text-emerald-400 bg-black/90 px-2 py-0.5 border border-emerald-800/80 font-bold hidden sm:inline-block">
              ● 25 SPECIALIZED AGENTS ACTIVE
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
        <div
          className="absolute top-10 left-0 right-0 grid px-4 text-center z-20 pointer-events-none"
          style={{ gridTemplateColumns: `repeat(${STAGE_LABELS.length}, minmax(0, 1fr))` }}
        >
          {STAGE_LABELS.map((lbl, idx) => (
            <div key={idx} className="text-[9px] font-extrabold text-zinc-400 uppercase tracking-wider">
              {lbl}
            </div>
          ))}
        </div>

        {/* The Live Canvas */}
        <div ref={wrapRef} className="w-full h-[780px] min-h-[740px] relative">
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
              <div className="space-y-2 flex-1 overflow-y-auto max-h-[300px] pr-1 overscroll-contain scroll-smooth">
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

            <div className="space-y-1.5 flex-1 overflow-y-auto max-h-[300px] pr-1 font-mono text-xs overscroll-contain scroll-smooth">
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

            {/* Comprehensive Telemetry Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">COMPONENT TYPE</span>
                <span className="text-white font-bold capitalize mt-0.5 block">
                  {selectedAgent.type?.replace('_', ' ') || 'Execution Worker'}
                </span>
              </div>

              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">LIVE STATUS</span>
                <span className={`font-bold text-xs mt-0.5 block ${
                  agentStateMap[selectedAgent.id]?.status === 'RUNNING'
                    ? 'text-red-400 animate-pulse'
                    : agentStateMap[selectedAgent.id]?.status === 'COMPLETED'
                    ? 'text-emerald-400'
                    : agentStateMap[selectedAgent.id]?.status === 'SKIPPED'
                    ? 'text-zinc-500'
                    : 'text-zinc-300'
                }`}>
                  {agentStateMap[selectedAgent.id]?.status || 'IDLE'}
                </span>
              </div>

              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">ASSIGNED MODEL</span>
                <span className="text-white font-bold flex items-center gap-1 mt-0.5">
                  <Cpu className="w-3.5 h-3.5 text-red-500" />
                  {selectedAgent.model}
                </span>
              </div>

              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">ACTIVE TOOL / LIBRARY</span>
                <span className="text-red-300 font-bold mt-0.5 block">
                  {agentStateMap[selectedAgent.id]?.currentTool || selectedAgent.tool || 'None'}
                </span>
              </div>
            </div>

            {/* Task & Input/Output Summaries */}
            <div className="bg-black p-2 border border-zinc-800 text-xs">
              <span className="text-zinc-500 text-[10px] block uppercase">CURRENT TASK</span>
              <p className="text-zinc-200 mt-0.5 leading-relaxed">
                {agentStateMap[selectedAgent.id]?.taskSummary || selectedAgent.role}
              </p>
            </div>

            {agentStateMap[selectedAgent.id]?.outputSummary && (
              <div className="bg-zinc-950 p-2 border border-emerald-900/60 text-xs">
                <span className="text-emerald-400 text-[10px] block uppercase font-bold">OUTPUT SUMMARY</span>
                <p className="text-zinc-200 mt-0.5 text-[11px] leading-relaxed">
                  {agentStateMap[selectedAgent.id].outputSummary}
                </p>
              </div>
            )}

            {/* Timing, Duration & Graph Relationships */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">START TIME</span>
                <span className="text-zinc-300 font-mono text-[11px] mt-0.5 block">
                  {agentStateMap[selectedAgent.id]?.startTimestamp
                    ? new Date(agentStateMap[selectedAgent.id].startTimestamp * 1000).toLocaleTimeString()
                    : 'N/A'}
                </span>
              </div>

              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">COMPLETION</span>
                <span className="text-zinc-300 font-mono text-[11px] mt-0.5 block">
                  {agentStateMap[selectedAgent.id]?.completionTimestamp
                    ? new Date(agentStateMap[selectedAgent.id].completionTimestamp * 1000).toLocaleTimeString()
                    : 'N/A'}
                </span>
              </div>

              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">DURATION</span>
                <span className="text-emerald-400 font-bold font-mono text-[11px] mt-0.5 block">
                  {agentStateMap[selectedAgent.id]?.duration || '0.00s'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">PARENT NODE</span>
                <span className="text-zinc-300 font-mono text-[11px] mt-0.5 block">
                  {selectedAgent.parent || 'START'}
                </span>
              </div>

              <div className="bg-black p-2 border border-zinc-800">
                <span className="text-zinc-500 text-[10px] block uppercase">CHILD NODE</span>
                <span className="text-zinc-300 font-mono text-[11px] mt-0.5 block">
                  {selectedAgent.child || 'END'}
                </span>
              </div>
            </div>

            {/* Retry & Error Visibility */}
            {agentStateMap[selectedAgent.id]?.retryCount > 0 && (
              <div className="bg-black p-2 border border-amber-900/60 text-xs">
                <span className="text-amber-400 text-[10px] block uppercase font-bold">RETRY / LOOP COUNT</span>
                <span className="text-amber-300 font-bold font-mono">
                  {agentStateMap[selectedAgent.id].retryCount} Adaptive Iteration(s)
                </span>
              </div>
            )}

            {agentStateMap[selectedAgent.id]?.error && (
              <div className="bg-red-950/60 p-2 border border-red-800 text-xs">
                <span className="text-red-400 text-[10px] block uppercase font-bold">ERROR DETAILS</span>
                <p className="text-red-200 mt-0.5 font-mono text-[11px]">{agentStateMap[selectedAgent.id].error}</p>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
