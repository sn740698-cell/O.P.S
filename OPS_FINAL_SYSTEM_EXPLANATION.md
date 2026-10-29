# O.P.S. (Over-Engineered Programmed System) — Comprehensive Owner-Level System Reference

**Authoritative Target:** Canonical O.P.S. Operating System (`OPS_CANONICAL_UNIFIED_ARCHITECTURE_ANTIGRAVITY.md`)  
**Status:** Integrated, Consolidated, and Verified  
**Date:** 2026-10-07  

---

## 1. Executive Owner-Level Summary: What O.P.S. Is

O.P.S. (Over-Engineered Programmed System) is not a chat assistant or wrapper around an LLM API. It is a **local-first autonomous AI Operating System** designed to control your computer, write and debug software, execute deep web research, manage local knowledge, and orchestrate complex multi-step missions without ever bypassing safety or fabricating success.

### Key Differentiators from a Standard Chatbot
1. **Local-First Privacy & Autonomy:** Runs entirely on your local machine using local Ollama models (Qwen3 0.6B, Qwen3 1.7B, Llama 3.2 1B). No user prompts, code, or personal data leave your machine unless external escalation is explicitly requested.
2. **Operating System Integration:** Interacts directly with Windows desktop applications (Chrome, VS Code, Explorer), file system (`read`, `write`, `create_dir`, `delete`), and terminal subprocesses.
3. **Deterministic Safety Gate & HITL:** No LLM can directly execute dangerous OS commands. Every action is intercepted by a deterministic `SafetyGate` that blocks destructive operations (e.g. disk formatting) and pauses execution for Human-In-The-Loop approval on elevated operations (e.g. file deletion, system installs).
4. **Ground-Truth Physical Verification:** Eliminates LLM hallucinations. An agent cannot declare a task complete simply because it generated code; the `Verifier` physically verifies that the file was written to disk (`os.path.exists`), the command returned exit code `0`, or the browser DOM loaded.
5. **Stateful DAG Mission Control with Bounded Recovery:** Complex directives ("Build a React dashboard, test it, fix bugs, and open it") are decomposed into directed acyclic graph (DAG) plans executed step-by-step with automatic debugger failure diagnosis and a bounded 3-retry recovery loop.

---

## 2. Complete Architecture from Top to Bottom

```text
                                  USER (Voice / Text)
                                           │
                                           ▼
                                   POP-UP COCKPIT (HUD)
                             (React 18 / Tailwind / WebSocket)
                                           │
                                           ▼
                                    SESSION MANAGER
                       (Active RAM State vs Persistent Memory)
                                           │
                                           ▼
                              FAST ROUTER (Qwen3 0.6B)
                     (Sub-50ms Mode & Intent Classification)
                                           │
                       ┌───────────────────┴───────────────────┐
                       ▼                                       ▼
                  [CHAT MODE]                       [TASK / MISSION MODE]
                       │                                       │
                       ▼                                       ▼
                RESPONSE AGENT                            SUPERVISOR
              (Llama 3.2 1B Synth)                    (Qwen3 1.7B Root)
                       │                                       │
                       │                       ┌───────────────┴───────────────┐
                       │                       ▼                               ▼
                       │                 [SIMPLE TASK]                  [COMPLEX MISSION]
                       │                       │                               │
                       │                       │                               ▼
                       │                       │                        MISSION MANAGER
                       │                       │                               │
                       │                       │                               ▼
                       │                       │                       PLANNER (Qwen3 1.7B)
                       │                       │                               │
                       │                       └───────────────┬───────────────┘
                       │                                       │
                       │                                       ▼
                       │                               SPECIALIZED AGENTS
                       │                 ┌─────────────────────┼─────────────────────┐
                       │                 ▼                     ▼                     ▼
                       │            WEB DOMAIN            AUTO DOMAIN           DEV DOMAIN
                       │         (Web Superior)         (Auto Superior)      (Dev/Test/Debug)
                       │                 │                     │                     │
                       │                 └─────────────────────┼─────────────────────┘
                       │                                       │
                       │                                       ▼
                       │                              CAPABILITY REGISTRY
                       │                        (Permission & Schema Gate)
                       │                                       │
                       │                                       ▼
                       │                                  SAFETY GATE
                       │                   (SAFE / ELEVATED / DANGEROUS / FORBIDDEN)
                       │                                       │
                       │                                       ▼
                       │                                 TOOL EXECUTOR
                       │                     (Filesystem / Terminal / Desktop / Browser)
                       │                                       │
                       │                                       ▼
                       │                             GROUND-TRUTH VERIFIER
                       │                      (Physical Disk, Process & DOM Checks)
                       │                                       │
                       │                                       ▼
                       │                                RECOVERY / RETRY
                       │                      (Bounded 3-Attempt Debugger Loop)
                       │                                       │
                       │                                       ▼
                       │                               RESULT AGGREGATOR
                       │                                       │
                       │                                       ▼
                       └───────────────────────────────> RESPONSE AGENT
                                                               │
                                                               ▼
                                                           EVENT BUS
                                                   (StructuredOPSEvents)
                                                               │
                                                               ▼
                                                    COCKPIT + AGENTS UI
```

---

## 3. Detailed Subsystem Breakdown

### 3.1 Pop-up Cockpit & Agents UI
- **Pop-up Cockpit (`frontend/src/App.jsx`):** The primary tactical interface. Provides a floating overlay HUD with 90s retro Iron Man aesthetic, global hotkey triggers (`Ctrl+Space`), quick mode indicators, live agent status glow, approval decision buttons, and voice orb.
- **Agents UI (`frontend/src/components/OpsLiveOrchestrationTab.jsx`):** A real-time telemetry view of the backend orchestration system. Displays a dynamic 4-stage hierarchy (Intake & Routing -> Orchestration -> Execution Fleet -> Verification & Safety), active tool badges, stateful DAG mission progress, real-time event logs, and detailed agent telemetry modals.
- **Real Backend Telemetry:** The UI never simulates activity. It renders live state broadcasted from `OPSEventBus` over `/ws/agent/`.

### 3.2 Session Manager & Memory Architecture
- **Active Session State (`backend/ops_core/session/session_manager.py`):** Holds volatile in-memory context (active `session_id`, conversation messages, current mission state, pending approval tickets).
- **Persistent Long-Term Memory (`backend/ops_core/services/rag_service.py`):** Backed by ChromaDB and PostgreSQL. Holds indexed codebase files, ingested documentation, and historical mission memories.
- **STOP vs REFRESH Semantics:**
  - **STOP (`POST /api/v1/ops/session/stop/`):** Immediately sets `is_active=False`, aborts running sub-processes and tool loops, but **preserves all conversation history and active session state** for inspection.
  - **REFRESH (`POST /api/v1/ops/session/refresh/`):** Purges volatile in-memory conversation history and generates a brand-new `session_id`, while **intentionally leaving all persistent ChromaDB vector memories and PostgreSQL records completely intact**.

### 3.3 Fast Router (Qwen3 0.6B)
- **Module:** `backend/ops_core/router/fast_router.py`
- **Model:** `qwen3:0.6b-q8_0` (Local Ollama)
- **Classification Modes:**
  1. `CHAT`: Direct conversational and informational queries.
  2. `TASK`: Single-agent, single-capability direct executions.
  3. `MISSION`: Multi-step, multi-agent workflows requiring planner decomposition.
  4. `MEMORY`: Storage or retrieval of long-term knowledge.
  5. `CLARIFICATION`: Ambiguous or underspecified directives requiring user prompt.
- **Sub-50ms Heuristic Fast-Path:** Employs pre-compiled zero-latency regex matching for common system commands (e.g. `open chrome`, `remember that`, `search for`) delivering `<5ms` decisions, falling back to structured JSON generation with Qwen3 0.6B.

### 3.4 Supervisor & Mission Manager
- **Supervisor (`backend/ops_core/orchestration/supervisor.py`):** The central conductor. Coordinates input handling, receives Router decisions, selects specialist agents, passes complex tasks to the Mission Manager, and routes output through the Response Agent.
- **Mission Manager (`backend/ops_core/orchestration/mission_manager.py`):** Handles stateful DAG execution. Manages step status transitions (`PENDING` -> `RUNNING` -> `VERIFYING` -> `SUCCESS` / `FAILED`), dependency resolution, and step retries.
- **Planner (`backend/ops_core/orchestration/planner.py`):** Uses `qwen3:1.7b-q8_0` to decompose high-level goals into ordered `PlanStep` sequences with assigned agents and required capability schemas.

### 3.5 Specialized Agent Domains
1. **Web Research Domain (`backend/ops_core/services/agents/web_agents.py`):**
   - **Web Superior Agent (Qwen3 1.7B):** Coordinates research and extraction workflows.
   - **Web Prompt Understanding Agent (Qwen3 1.7B):** Formulates search queries and selects the optimal extractor.
   - **BeautifulSoup Agent (Qwen3 0.6B):** High-speed direct HTML text and article parsing.
   - **ScrapeGraphAI Agent (Llama 3.2 1B):** Structured schema and tabular data extraction.
   - **Crawlee Agent (Llama 3.2 1B):** Recursive, multi-page deep crawling.
   - **Retrieval Quality Agent (Qwen3 1.7B):** Assesses content completeness and triggers self-correction loops if information is missing.
2. **Automation / Desktop Domain (`backend/ops_core/services/agents/automation_agents.py`):**
   - **Automation Superior Agent (Qwen3 1.7B):** Coordinates OS-level actions.
   - **Auto Prompt Understanding Agent (Qwen3 1.7B):** Parses application names and target paths.
   - **HITL Approval Gate:** Evaluates risk and triggers human approval prompts.
   - **Open Web Agent (Llama 3.2 1B):** Interactive browser control via Playwright.
   - **Installed Apps Agent (Python Engine):** Launches Windows desktop applications.
   - **Open File Agent (Python Engine):** Opens files and directories in native handlers.
   - **Desktop Control Agent (PyAutoGUI):** Performs keyboard and mouse automation.
3. **Software Development Fleet (`backend/ops_core/agents/`):**
   - **Developer Agent (Qwen3 1.7B):** Generates code, creates project structures, edits files.
   - **Tester Agent (Qwen3 1.7B):** Runs pytest/unittest test suites and captures stderr/tracebacks.
   - **Debugger Agent (Qwen3 1.7B):** Analyzes test failures, diagnoses root causes, and generates code patches.
   - **Reviewer Agent (Qwen3 1.7B):** Inspects code diffs for quality, style, and security invariants.
4. **RAG & Knowledge Agent (`backend/ops_core/agents/rag_agent.py`):**
   - Indexes local project files into ChromaDB vector store. Performs cosine similarity semantic search to answer queries like "Where is my API code?".
5. **Response Synthesizer (`backend/ops_core/agents/response_agent.py`):**
   - Uses `llama3.2:1b-instruct-q8_0` to generate clear, concise user-facing summaries grounded entirely in verified tool execution evidence.

### 3.6 Safety Gate & Human-In-The-Loop (HITL)
- **Module:** `backend/ops_core/safety/safety_gate.py`
- **Risk Tiers:**
  - `SAFE`: Non-destructive read operations, informational searches (`filesystem.read`, `web.search`, `rag.search`). Auto-approved.
  - `ELEVATED`: System package installations, background server launches (`terminal.execute`). Requires HITL approval.
  - `DANGEROUS`: File deletion, destructive overwrites, killing active processes (`filesystem.delete`). Requires explicit two-button confirmation in Cockpit (`Accept Action` vs `Deny Action`).
  - `FORBIDDEN`: Disk formatting, system directory wiping (`rmdir /s /q C:\Windows`). **Hard blocked unconditionally with zero exceptions.**

### 3.7 Ground-Truth Verifier & Bounded Recovery
- **Module:** `backend/ops_core/verification/verifier.py` & `ground_truth.py`
- **Verification Rule:** A step is NEVER marked complete based solely on LLM output. The Verifier performs deterministic OS/process checks:
  - `filesystem.write`: Checks `os.path.exists(path)` and `os.path.getsize(path) > 0`.
  - `terminal.execute`: Checks process return code `== 0`.
  - `desktop.launch_app`: Checks Windows process table for active executable.
  - `browser.open`: Checks Playwright page status and DOM render.
- **Bounded 3-Retry Recovery:** When a step fails verification, the Mission Manager routes the failure evidence to the `DebuggerAgent`, which formulates a patch and retries up to 3 times before safely terminating the mission.

---

## 4. Operational Invariant Status & Readiness

| System Component | Implementation Status | Verification Evidence |
|---|---|---|
| **Pop-up Cockpit HUD** | **FULLY WORKING** | Retro Iron Man overlay, hotkeys, reactive WebSocket connection |
| **Live Agents UI** | **FULLY WORKING** | Dynamic 4-tier DAG topology, live telemetry modals, tool badges |
| **Fast Router (Qwen3 0.6B)** | **FULLY WORKING** | Sub-50ms heuristic + Ollama structured JSON fallback |
| **Supervisor & Mission Manager** | **FULLY WORKING** | Stateful DAG plan execution, step state tracking |
| **Developer Fleet (Dev/Test/Debug/Review)** | **FULLY WORKING** | Multi-file write, pytest execution, automated bug repair |
| **Capability Registry & Safety Gate** | **FULLY WORKING** | Deterministic risk classification, HITL modal integration |
| **Ground-Truth Verifier** | **FULLY WORKING** | Anti-hallucination physical file/process assertion |
| **Session Manager (STOP vs REFRESH)** | **FULLY WORKING** | Volatile RAM reset vs persistent ChromaDB preservation |
| **RAG & ChromaDB Knowledge Base** | **FULLY WORKING** | Vector ingestion, semantic search, codebase indexing |
| **Desktop Control Engine** | **FULLY WORKING** | PyAutoGUI + Native Win32 API (`ctypes.windll.user32`) & PowerShell `WScript.Shell` fallback |
| **Wispr Flow / Voice Integration** | **PARTIALLY WORKING** | Core service endpoints active; requires local microphone hardware |
| **Local Vision Subsystem** | **PARTIALLY WORKING** | Schema & routing ready; requires local vision model (`llava`) pull |

---

## 5. Owner-Level Answers to Key Operational Questions

1. **"What can I ask O.P.S. to do right now?"**
   - Launch any installed desktop application (e.g., "Open Chrome", "Open VS Code").
   - Create, edit, and organize files and directories on disk.
   - Search the web and crawl pages for structured information and summaries.
   - Query your local codebase and project knowledge (e.g., "Where is my API code?").
   - Build complete codebases, write unit tests, execute them, and automatically fix failures.
   - Stop or refresh active sessions with full safety and persistence guarantees.

2. **"How does O.P.S. know the work actually succeeded?"**
   - O.P.S. never trusts LLM text claims. It inspects physical reality on your machine: confirming the file exists on disk with non-zero size, checking the process exit code is 0, or verifying that the application process is running in Windows tasklist.

3. **"What happens when I press Stop vs Refresh?"**
   - **Stop:** Instantly freezes execution and cancels active processes, while keeping all conversation history and session logs visible in the Cockpit.
   - **Refresh:** Clears the active conversation in the Cockpit and issues a new session ID, while preserving all long-term vector memories in ChromaDB.

4. **"What actions require my approval?"**
   - Any destructive action (deleting files, dropping tables, modifying system configurations) triggers the two-button HITL Approval Bar in the Cockpit (`Accept Action` / `Deny Action`). Execution remains paused until you decide.
