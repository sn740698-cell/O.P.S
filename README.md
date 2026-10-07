# 🧠 O.P.S. — Over-Engineered Programmed System (v3.0)

> **A Local-First Agentic AI Operating System that can hear, see, think, search, code, automate, and remember your digital world.**

O.P.S. is an **ambient, multimodal, agentic AI operating system** that transforms your workstation into a J.A.R.V.I.S.-class command cockpit. Built with a **'90s retro tactical Iron Man HUD aesthetic** (Crimson Red, Jet Black, Steel Gray, and Pure White), O.P.S. coordinates local lightweight LLMs (Qwen3 0.6B Fast Router, Qwen3 1.7B Lead Planner & Reasoning Engine, and Llama 3.2 1B Instruct Persona), autonomous web crawling, universal OS & DOM automation, stateful multi-step mission execution, ground-truth physical verification, and dual-layer isolated memory under a strict deterministic Safety Gate.

---

## 🌟 Canonical Core Architecture (v3.0)

The authoritative architecture strictly follows [`OPS_COMPLETE_UPGRADED_ARCHITECTURE_ANTIGRAVITY.md`](file:///d:/Projects/O.P.S/OPS_COMPLETE_UPGRADED_ARCHITECTURE_ANTIGRAVITY.md):

```text
                       [ USER INPUT ]
                             │
                [ O.P.S. POP-UP COCKPIT ]
         (Web Cockpit HUD / Desktop Windows Overlay)
                             │
                    [ SESSION MANAGER ]
              (Active Volatile Session Memory)
                             │
                 [ QWEN3 0.6B FAST ROUTER ]
          (Zero-latency heuristics & <50ms classification)
        ┌─────────────┬─────────────┬─────────────┬─────────────┐
        ▼             ▼             ▼             ▼             ▼
     [ CHAT ]      [ TASK ]     [ MISSION ]   [ MEMORY ]  [ CLARIFY ]
        │             │             │             │             │
        │             └──────┬──────┘             │             │
        │                    │                    │             │
        │             [ SUPERVISOR ]              │             │
        │                    │                    │             │
        │          [ MISSION MANAGER ]            │             │
        │       (Stateful 3-retry loops)          │             │
        │                    │                    │             │
        │          [ QWEN3 1.7B PLANNER ]         │             │
        │       ( Verifiable task decomposition ) │             │
        │                    │                    │             │
        │        [ CAPABILITY REGISTRY ]          │             │
        │   (filesystem, terminal, browser, web)  │             │
        │                    │                    │             │
        │        [ SPECIALIZED AGENTS ]           │             │
        │    (Developer, Tester, Debugger, etc.)  │             │
        │                    │                    │             │
        │          [ SAFETY GATE (HITL) ]         │             │
        │    (Deterministic policy authorization) │             │
        │                    │                    │             │
        │           [ TOOL EXECUTOR ]             │             │
        │                    │                    │             │
        │      [ GROUND-TRUTH VERIFIER ]          │             │
        │       (Physical state assertions)       │             │
        │                    │                    │             │
        └────────────────────┼────────────────────┘─────────────┘
                             ▼
                    [ RESPONSE ENGINE ]
            (Grounded in verified physical evidence)
                             │
                [ O.P.S. POP-UP COCKPIT ]
```

---

## 🚀 Architectural Pillars & Subsystems

### 1. 🤖 Local-First Tri-Model Allocation
* **Model 1 — Qwen3 0.6B Q8_0 (Fast Router & Mode Classifier):**
  * `<50ms` intent classification across 5 execution modes: `CHAT`, `TASK`, `MISSION`, `MEMORY`, `CLARIFICATION`.
* **Model 2 — Qwen3 1.7B Q8_0 (Lead Planner, Developer, Debugger, Tester, Reviewer):**
  * Complex reasoning, step-by-step verifiable task decomposition, root-cause diagnosis, code refactoring.
* **Model 3 — Llama 3.2 1B Instruct (Response Engine & Voice/Persona Layer):**
  * Tactical natural language synthesis grounded strictly in verified evidence.

---

### 2. 🛡️ Deterministic Safety Gate & Human-in-the-Loop (HITL)
* **Risk Levels:**
  * `SAFE`: Read-only actions (read file, web search, system status) auto-approve immediately.
  * `ELEVATED`: File writes, application launches, test runs.
  * `DANGEROUS`: File deletion, hard resets, process termination — triggers interactive **2-button tactile HITL modal** (`[ ❌ DENY ACTION ]` / `[ ✅ ACCEPT ACTION ]`).
  * `FORBIDDEN`: Destructive patterns (`rm -rf /`, `format C:`, disk wiping, bash fork bombs) are **strictly blocked**. The model can never override this gate.

---

### 3. 🔬 Ground-Truth Verifier & Critic Engine
* **Physical Evidence Invariant:** Models reason; tools execute; the verifier checks reality.
* **Physical State Assertions:** File existence, non-zero file sizes, verified exit codes (`exit_code == 0`), live process verification, DOM element presence.
* **No False Success:** The Response Engine never reports success without verified physical evidence.

---

### 4. 🗄️ Dual-Layer Isolated Memory Architecture
* **Layer 1 — Active Session Memory (Volatile):**
  * Manages active conversation history, task/mission state, pending approvals, and temporary scratchpad context.
* **Layer 2 — Persistent Memory Vault (Permanent):**
  * **ChromaDB**: Semantic vector embeddings across codebase, indexed documents, and long-term knowledge.
  * **PostgreSQL**: Structured workstation memories, app usages, user preferences, and audit logs.
* **The `STOP` vs `REFRESH` Contract:**
  * **`[ ⏹ STOP ]`**: Halts active mission/task execution while preserving current session ID, conversation history, and mission context for later resumption.
  * **`[ ↻ REFRESH ]`**: Resets volatile active session state and generates a new `session_id`. **Refresh NEVER deletes ChromaDB, embeddings, or PostgreSQL memories.**

---

### 5. 🎯 Specialized Agent Suite
* **`DeveloperAgent`**: Code scaffolding, filesystem creation/modification, build orchestration.
* **`DebuggerAgent`**: Stack trace inspection, failure root-cause analysis, automatic patch generation.
* **`TesterAgent`**: Automated test suite execution (`pytest`, `unittest`, `npm test`), test-driven assertions.
* **`ReviewerAgent`**: Architecture rule enforcement, security policy compliance.
* **`WebAgent` & `ResearchAgent`**: Live web search and crawl across strict untrusted boundary (`<UNTRUSTED_EXTERNAL_WEB_CONTENT>`).
* **`AutomationAgent` & `BrowserAgent`**: Desktop application launching, native OS interaction, Playwright browser DOM workflows.
* **`RAGAgent`**: Semantic codebase search and persistent knowledge indexing.
* **`ResponseAgent`**: Synthesizes verified evidence into clean, tactical natural language for the Pop-up Cockpit.

---

## 🧪 Acceptance Test Suite (10/10 Verified)

Run the automated acceptance suite verifying all 10 core architectural invariants:

```powershell
d:\Projects\O.P.S\backend\venv\Scripts\python.exe -m unittest ops_core.tests.test_ops_acceptance -v
```

| # | Acceptance Test Case | Specification Status |
|---|---|---|
| 1 | **Chat Fast Path** | ✅ **PASSED** (Direct response without tool execution or planning overhead) |
| 2 | **Single Tool Task** | ✅ **PASSED** (Direct capability execution with verified ground-truth evidence) |
| 3 | **Full Mission Flow** | ✅ **PASSED** (Multi-step plan decomposition, sequential execution, verified assertions) |
| 4 | **Stop Behavior** | ✅ **PASSED** (Halts execution while preserving active session & conversation history) |
| 5 | **Refresh Behavior** | ✅ **PASSED** (Resets volatile context, assigns new session ID, preserves permanent RAG) |
| 6 | **Forbidden Safety Gate** | ✅ **PASSED** (Blocks `rm -rf /` and destructive commands with security violations) |
| 7 | **Ground-Truth Verification** | ✅ **PASSED** (Accurately flags failure when expected physical file is missing) |
| 8 | **Bounded Error Recovery** | ✅ **PASSED** (Debugger retry cycle bounded at max 3 attempts without infinite loops) |
| 9 | **Dangerous Permission HITL** | ✅ **PASSED** (Classifies high-impact actions as `DANGEROUS` requiring confirmation) |
| 10 | **Memory Layer Separation** | ✅ **PASSED** (Persistent ChromaDB knowledge survives active session refresh) |

---

## 🛠️ Quick Start

### Backend (Django + Channels + Ollama):
```powershell
cd d:\Projects\O.P.S\backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver 8000
```

### Frontend Pop-Up Cockpit (React + Vite):
```powershell
cd d:\Projects\O.P.S\frontend
npm run dev
```

### Desktop HUD Overlay:
```powershell
cd d:\Projects\O.P.S\backend
python desktop_overlay.py
```
* Press `Ctrl + Space` to toggle the tactical Pop-up Cockpit overlay anywhere on your desktop.
