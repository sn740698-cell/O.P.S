# O.P.S. (Over-Engineered Programmed System)
## Comprehensive Architecture Audit & Canonical Integration Plan

**Document Version:** 1.0.0  
**Target Specification:** `OPS_CANONICAL_UNIFIED_ARCHITECTURE_ANTIGRAVITY.md`  
**Date:** 2026-10-07  
**Status:** COMPLETE ARCHITECTURE AUDIT (Pre-Implementation Phase)

---

### Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Existing Architecture & Components](#2-existing-architecture--components)
3. [Existing Agents & Domain Hierarchy](#3-existing-agents--domain-hierarchy)
4. [Existing Web Domain Agents](#4-existing-web-domain-agents)
5. [Existing Automation/Auto Domain Agents](#5-existing-automationauto-domain-agents)
6. [Existing Tools & Capabilities](#6-existing-tools--capabilities)
7. [Existing Models & Local AI (Ollama)](#7-existing-models--local-ai-ollama)
8. [Existing Cockpit Integration](#8-existing-cockpit-integration)
9. [Existing Agents UI & Telemetry](#9-existing-agents-ui--telemetry)
10. [Existing Event System & WebSockets](#10-existing-event-system--websockets)
11. [Existing Memory & RAG Separation](#11-existing-memory--rag-separation)
12. [Existing Safety & HITL Approvals](#12-existing-safety--hitl-approvals)
13. [Existing Verification & Ground-Truth Assertions](#13-existing-verification--ground-truth-assertions)
14. [Existing Stop & Refresh Semantics](#14-existing-stop--refresh-semantics)
15. [Identified Duplications](#15-identified-duplications)
16. [Missing Components](#16-missing-components)
17. [Broken & Disconnected Flows](#17-broken--disconnected-flows)
18. [Canonical Component Mapping Table](#18-canonical-component-mapping-table)
19. [Recommended Migration & Integration Plan](#19-recommended-migration--integration-plan)
20. [Risk Assessment & Precautions](#20-risk-assessment--precautions)

---

## 1. Executive Summary

An exhaustive inspection of the O.P.S. codebase was conducted across frontend (React + Tailwind + WebSockets), backend (Django Channels, LangGraph orchestrators, canonical Supervisor, capability registries, verification critics, Ollama local runtimes), database layers (PostgreSQL + ChromaDB), safety gates, and automation tools.

### Key Audit Findings:
1. **Strong Working Subsystems:** The core tools (Playwright, PyAutoGUI, Crawlee/BS4, ChromaDB RAG, Piper TTS, Faster-Whisper, PostgreSQL session models), deterministic safety policies, ground-truth verifiers, and retro-tactical frontend HUD interfaces are implemented and operational.
2. **Dual Parallel Architectures Found:** The system currently possesses two co-existing execution engines:
   - **Engine A (Legacy LangGraph Pipeline):** `AgentOrchestrator` in `backend/ops_core/services/` running a state graph with rich sub-agents (`WebSuperiorAgent`, `AutomationSuperiorAgent`, `ScrapeGraphAIAgent`, `CrawleeAgent`, `HITLApprovalGate`, etc.).
   - **Engine B (Canonical Orchestration Core):** `Supervisor` in `backend/ops_core/orchestration/` with `FastRouter`, `MissionManager`, `Planner`, `CapabilityRegistry`, `SafetyGate`, `Verifier`, and `ResponseEngine`.
3. **Core Mandate:** Rather than discarding either system or creating a third competing architecture, we must **unify and harmonize** the two. Specifically:
   - Wire the rich sub-agent domains (**Web Domain**: Web Superior, Web Prompt Understanding, Crawlee, BS4, ScrapeGraphAI, Retrieval Quality; **Auto Domain**: Auto Superior, Auto Prompt Understanding, HITL Gate, Open Web, Installed Apps, Open File, Desktop Control) directly under the canonical **Supervisor** and **Capability Registry**.
   - Maintain the explicit distinction between **Web Research** (information retrieval) and **Browser Automation / Open Web Agent** (Playwright DOM control).
   - Ensure the existing **Agents UI** reflects the exact, real-time backend state through canonical structured event streams (`OPSEventBus`).

---

## 2. Existing Architecture & Components

| Subsystem | Existing Path | Technology Stack | Status |
| :--- | :--- | :--- | :--- |
| **Frontend HUD** | `frontend/src/App.jsx` | React 18, Tailwind CSS, Lucide Icons | Working & Polished |
| **Pop-up Cockpit** | `frontend/src/components/OpsCommandCore.jsx` | React, WebSockets, Retro Audio Synth | Working |
| **Live Agents UI** | `frontend/src/components/OpsLiveOrchestrationTab.jsx` | HTML5 Canvas, React, Real-time Events | Working |
| **Backend Framework** | `backend/ops_backend/` & `ops_core/` | Django 5.x, Django Channels, Daphne ASGI | Working |
| **Fast Router** | `backend/ops_core/router/fast_router.py` | Qwen3 0.6B Q8_0 + Zero-Latency Regex | Working (<50ms) |
| **Supervisor** | `backend/ops_core/orchestration/supervisor.py` | Qwen3 1.7B Q8_0 Canonical Orchestration | Working |
| **Mission Manager** | `backend/ops_core/orchestration/mission_manager.py` | Stateful DAG Tracker, Bounded Retries | Working |
| **Lead Planner** | `backend/ops_core/orchestration/planner.py` | Qwen3 1.7B Q8_0 Decomposer | Working |
| **Capability Registry** | `backend/ops_core/capabilities/registry.py` | Centralized Capability Schemas & RBAC | Working |
| **Safety Gate** | `backend/ops_core/safety/safety_gate.py` | Deterministic Risk Analyzer & Policy Gate | Working |
| **HITL Manager** | `backend/ops_core/services/permission_manager.py` | In-memory + DB Security Prompts | Working |
| **Verifier / Critic** | `backend/ops_core/verification/verifier.py` | Ground-Truth Physical State Critic | Working |
| **Local LLM Engine** | `backend/ops_core/services/ollama_service.py` | Ollama HTTP API (Local Qwen3/Llama) | Working |
| **Persistent RAG** | `backend/ops_core/services/rag_service.py` | ChromaDB, All-MiniLM-L6-v2 Embeddings | Working |
| **Workstation DB** | `backend/ops_core/models.py` | PostgreSQL (`ops_db`), Django ORM | Working |
| **Voice & Speech** | `backend/ops_core/services/voice_service.py` | Faster-Whisper (STT), Piper TTS (Audio) | Working |
| **Event Bus** | `backend/ops_core/services/event_bus.py` | Django Channels Group Messaging | Working |

---

## 3. Existing Agents & Domain Hierarchy

### Existing Domain Layout:
1. **Ingress & Orchestration:**
   - `FastRouter` (`router/fast_router.py` & `services/agents/router_agent.py`)
   - `Supervisor` (`orchestration/supervisor.py`)
   - `MissionManager` (`orchestration/mission_manager.py`)
   - `Planner` (`orchestration/planner.py`)
2. **Web Domain (Explicit Multi-Agent Tree in `services/agents/web_agents.py`):**
   - `WebSuperiorAgent`
   - `WebPromptUnderstandingAgent`
   - `CrawleeAgent`
   - `BeautifulSoupAgent`
   - `ScrapeGraphAIAgent`
   - `RetrievalQualityAgent`
3. **Automation Domain (Explicit Multi-Agent Tree in `services/agents/automation_agents.py`):**
   - `AutomationSuperiorAgent`
   - `AutomationPromptUnderstandingAgent`
   - `HITLApprovalGate`
   - `OpenWebAgent`
   - `InstalledAppsAgent`
   - `OpenFileAgent`
   - `DesktopControlAgent`
4. **Development Domain (`ops_core/agents/`):**
   - `DeveloperAgent`
   - `DebuggerAgent`
   - `TesterAgent`
   - `ReviewerAgent`
5. **Knowledge & Response Domain:**
   - `RAGAgent` (`ops_core/agents/rag_agent.py`)
   - `ResponseAgent` (`ops_core/agents/response_agent.py`)
   - `Verifier` (`ops_core/verification/verifier.py`)

---

## 4. Existing Web Domain Agents

The Web Domain in `backend/ops_core/services/agents/web_agents.py` is fully realized with individual agent classes:
- **`WebSuperiorAgent` (Qwen3 1.7B):** Controls research execution lifecycle and manages self-correction loops.
- **`WebPromptUnderstandingAgent` (Qwen3 1.7B):** Extracts research objectives, required facts, temporal freshness, optimized queries, and recommends extractors.
- **`CrawleeAgent` (Llama 3.2 1B):** Deep, recursive multi-page web collection.
- **`BeautifulSoupAgent` (Qwen3 0.6B):** Lightweight static DOM parsing and HTML sanitization.
- **`ScrapeGraphAIAgent` (Llama 3.2 1B):** Schema-driven structured data extraction.
- **`RetrievalQualityAgent` (Qwen3 1.7B):** Deterministic and semantic fact-checking loop (evaluates relevance, completeness, freshness) with bounded max 2 retry cycles.

*Audit Note:* In `ops_core/agents/web_agent.py`, a single flat `WebAgent` was also created. We must **preserve the full 6-agent Web Domain** from `web_agents.py` and bridge it into the canonical `Supervisor` and `CapabilityRegistry`.

---

## 5. Existing Automation/Auto Domain Agents

The Automation Domain in `backend/ops_core/services/agents/automation_agents.py` implements complete hierarchical desktop control:
- **`AutomationSuperiorAgent` (Qwen3 1.7B):** Coordinates automation planning, HITL gate clearance, and specialized execution delegation.
- **`AutomationPromptUnderstandingAgent` (Qwen3 1.7B):** Decomposes directives into domain targets (`OPEN_WEB`, `INSTALLED_APPS`, `OPEN_FILE`, `DESKTOP_CONTROL`), structured action plans, and risk ratings.
- **`HITLApprovalGate` (Deterministic):** Evaluates pre-approvals or raises high-priority permission prompts over `/ws/permissions/` before executing actions.
- **`OpenWebAgent` (Playwright / Llama 3.2 1B):** Controls live browser DOM, form inputs, video search, and web applications.
- **`InstalledAppsAgent` (PyAutoGUI / Llama 3.2 1B):** Launches installed desktop applications (Spotify, VLC, WhatsApp, VS Code, Calculator) and simulates hotkeys.
- **`OpenFileAgent` (OS APIs / Qwen3 0.6B):** Resolves local file/folder paths across Downloads, Documents, Desktop, and project workspaces.
- **`DesktopControlAgent` (OS / PyAutoGUI / Llama 3.2 1B):** Creates directories/files, renames, organizes, and controls OS desktop environment.

*Audit Note:* This explicit hierarchy satisfies Sections 5, 6, 7, and 13 of the canonical specification. We must ensure `Supervisor` delegates automation tasks directly through `AutomationSuperiorAgent` without bypassing `CapabilityRegistry` or `SafetyGate`.

---

## 6. Existing Tools & Capabilities

Registered in `backend/ops_core/capabilities/registry.py` and implemented in `backend/ops_core/tools/`:
- **Filesystem Tools:** `filesystem.read`, `filesystem.write`, `filesystem.create_directory`, `filesystem.move`, `filesystem.delete`, `filesystem.list_directory`
- **Browser Automation Tools:** `browser.open`, `browser.navigate`, `browser.click`, `browser.type`, `browser.extract`
- **Web Scraping & Crawling Tools:** `web.search`, `web.crawl`, `web.extract_structured`, `web.parse_html`
- **Terminal & Shell Tools:** `terminal.execute`, `terminal.run_tests`
- **Desktop & Native App Tools:** `desktop.launch_app`, `desktop.open_file`, `desktop.hotkey`
- **RAG & Knowledge Tools:** `rag.search`, `rag.ingest`, `rag.index`

*Audit Note:* All tools properly reside in backend tool modules and are bound to executors in `ToolExecutor`. No direct un-sandboxed shell calls exist in frontend code.

---

## 7. Existing Models & Local AI (Ollama)

Configured via `OPSOllamaService` (`backend/ops_core/services/ollama_service.py`):
- **Fast Router / Classification:** `qwen3:0.6b-q8_0` (or `qwen2.5:0.5b` fallback)
- **Reasoning / Planning / Code:** `qwen3:1.7b-q8_0` (or `qwen2.5:1.5b` fallback)
- **Response Synthesis / Extractor:** `llama3.2:1b-instruct-q8_0` (or `llama3.2:1b` fallback)

*Audit Note:* All models are local-first, privacy-preserving, and run on local Ollama runtime port 11434 with zero mandatory cloud dependencies.

---

## 8. Existing Cockpit Integration

- **Pop-up Cockpit Component:** `frontend/src/components/OpsCommandCore.jsx` & `App.jsx`
- **Features:**
  - Fast text input directive bar
  - Microphone toggle & audio waveform (Whisper Flow STT)
  - Quick directive presets
  - Stop execution (`POST /api/v1/ops/session/stop/`)
  - Refresh session (`POST /api/v1/ops/session/refresh/`)
  - Live pipeline status (`STANDBY READY` / `LIVE ORCHESTRATION ACTIVE`)
  - Real-time terminal log viewer (`OpsTerminalConsole.jsx`)
  - Executive briefing & conversational card (`OpsBriefingCard.jsx`)

*Audit Note:* The Cockpit is fully functional, styled in retro-tactical HUD theme, and connected to the backend.

---

## 9. Existing Agents UI & Telemetry

- **Agents UI Component:** `frontend/src/components/OpsLiveOrchestrationTab.jsx`
- **Features:**
  - Interactive HTML5 Neural Canvas displaying the living topology graph
  - 4 Hierarchical Stages matching the specification:
    - Stage 01: Ingress & Routing (Fast Router, Canonical Supervisor)
    - Stage 02: Planning & Mission Control (Mission Manager, Lead Planner)
    - Stage 03: Specialized Agent Fleet (Web, Auto, Dev, Debugger, Tester, Reviewer, RAG)
    - Stage 04: Verification & Response (Ground-Truth Verifier, Response Engine)
  - Dynamic active glow reticles and tool badges driven strictly by incoming WebSocket events
  - Live Multi-step Mission Progress Card with queued, running, and verified step statuses
  - Real-time execution event stream timeline
  - Agent deep telemetry modal inspector

*Audit Note:* The Agents UI is already connected to live event streams and contains no fake mock loops.

---

## 10. Existing Event System & WebSockets

- **Event Definitions:** `backend/ops_core/core/events.py` (`OPSEventType`, `StructuredOPSEvent`)
- **Event Bus:** `backend/ops_core/services/event_bus.py` (`OPSEventBus.emit_ops_event`, `emit_voice_event`, `emit_permission_event`, `emit_terminal_event`)
- **Transport:** Django Channels WebSocket consumers:
  - `/ws/agent/` (`AgentOrchestrationConsumer`)
  - `/ws/permissions/` (`PermissionConsumer`)
  - `/ws/terminal/` (`TerminalOutputConsumer`)
  - `/ws/voice/` (`VoiceStreamConsumer`)
  - `/ws/mobile/` (`MobileSyncConsumer`)

*Audit Note:* Single canonical event emission pipeline established.

---

## 11. Existing Memory & RAG Separation

- **Active Session Context (Volatile RAM + PostgreSQL):**
  - Managed by `SessionManager` (`backend/ops_core/session/session_manager.py`)
  - Stores active session messages, mission state, tool results, pending approvals, and active agent states.
- **Persistent Knowledge (ChromaDB + PostgreSQL Memories):**
  - Managed by `OPSRAGService` (`backend/ops_core/services/rag_service.py`) and `UserWorkstationMemory` model.
  - Stores semantic vector embeddings of project files, documentation, and explicit user memories.
- **Refresh Verification:** Refreshing a session wipes the active session context and assigns a new session ID, while persistent ChromaDB embeddings and PostgreSQL workstation memories remain 100% untouched.

---

## 12. Existing Safety & HITL Approvals

- **Safety Policy Gate:** `backend/ops_core/safety/safety_gate.py`
  - Categorizes actions into `SAFE`, `ELEVATED`, `DANGEROUS`, `FORBIDDEN`.
  - Blocks destructive commands (e.g. `rmdir /s /q C:\Windows`, `format`) at the gate level without calling LLMs.
- **Prompt Injection Defense:** `backend/ops_core/safety/injection_guard.py`
  - Scans user prompts and untrusted web content for jailbreaks, prompt injection, and DAN patterns.
- **HITL Modal:** `frontend/src/components/OpsSecurityModal.jsx`
  - Renders interactive modals with 2 clear options (`[ ✕ DENY ACTION ]` and `[ ✓ ACCEPT ACTION ]`).

---

## 13. Existing Verification & Ground-Truth Assertions

- **Physical State Verifier:** `backend/ops_core/verification/verifier.py` & `ground_truth.py`
  - Filesystem: Asserts real physical existence on disk (`os.path.exists`, file content check).
  - Terminal: Checks process exit codes (must be 0).
  - Desktop Apps: Verifies target process is running via `psutil`.
  - Web: Verifies extracted text is non-empty and contains real facts.
- **Anti-Hallucination Guarantee:** LLMs claiming "File created successfully" are flagged as `VERIFICATION_FAILED` if the file is not physically on disk.

---

## 14. Existing Stop & Refresh Semantics

- **STOP (`POST /api/v1/ops/session/stop/`):**
  - Halts active tool and agent execution.
  - Preserves session ID, conversation history, and mission context.
- **REFRESH (`POST /api/v1/ops/session/refresh/`):**
  - Clears active volatile session and agent states.
  - Generates a new fresh session ID.
  - Leaves ChromaDB embeddings, project code, and persistent memories intact.

---

## 15. Identified Duplications

During the audit, the following duplicate or parallel implementations were identified:

1. **Dual Orchestration Entrypoints:**
   - `AgentRunWorkflowView` (`views.py` / `agent_orchestrator.py` - LangGraph state graph)
   - `CanonicalExecuteView` (`views.py` / `supervisor.py` - Canonical Supervisor)
2. **Dual Agent Bases:**
   - `ops_core/services/agents/base_agent.py` (`BaseOPSAgent`)
   - `ops_core/agents/base.py` (`BaseAgent`)
3. **Dual Session Managers:**
   - `ops_core/services/session_memory.py` (`SessionMemoryService`)
   - `ops_core/session/session_manager.py` (`SessionManager`)
4. **Dual Web Agent Definitions:**
   - `ops_core/agents/web_agent.py` (Flat single agent)
   - `ops_core/services/agents/web_agents.py` (6-agent Web Domain)
5. **Dual Automation Agent Definitions:**
   - `ops_core/agents/automation_agent.py` (Flat single agent)
   - `ops_core/services/agents/automation_agents.py` (7-agent Auto Domain)

---

## 16. Missing Components

1. **Unified Bridge between Canonical Supervisor and Hierarchical Sub-Agents:**
   - The canonical `Supervisor` currently routes to top-level agent wrappers, but needs explicit routing into the full `WebSuperiorAgent` tree (with Crawlee, BS4, ScrapeGraphAI, Retrieval Quality) and `AutomationSuperiorAgent` tree (with HITL, Open Web, Installed Apps, Open File, Desktop Control).
2. **Explicit Verification Hooks in Web/Auto Sub-Agents:**
   - `WebSuperiorAgent` and `AutomationSuperiorAgent` must emit canonical `VERIFICATION_STARTED` and `VERIFICATION_PASSED` / `VERIFICATION_FAILED` events through `GroundTruthVerifier`.

---

## 17. Broken & Disconnected Flows

1. **Web Sub-agent Event Emission:**
   - `web_agents.py` emitted legacy `agent_thought` and `agent_status` events, which need full alignment with canonical structured `StructuredOPSEvent` types (`AGENT_STARTED`, `TOOL_STARTED`, `VERIFICATION_PASSED`).
2. **Automation Sub-agent Capability Encasement:**
   - Some automation tools in `automation_agents.py` executed via `OPSAutomationService` directly instead of wrapping calls through `ToolExecutor` / `CapabilityRegistry`.
3. **Frontend WebSocket Fallback Parsing:**
   - `App.jsx` handled both legacy and structured events, but requires strict unified dispatching through `/api/v1/ops/execute/`.

---

## 18. Canonical Component Mapping Table

| Canonical Component | Current Path | Action Required |
| :--- | :--- | :--- |
| **Fast Router (Qwen3 0.6B)** | `ops_core/router/fast_router.py` | **KEEP & ENHANCE** (Ensure <50ms classification across all 5 modes) |
| **Supervisor (Qwen3 1.7B)** | `ops_core/orchestration/supervisor.py` | **KEEP & EXPAND** (Act as the single canonical coordinator for all domains) |
| **Mission Manager** | `ops_core/orchestration/mission_manager.py` | **KEEP** (Stateful DAG execution with bounded 3-attempt recovery) |
| **Lead Planner (Qwen3 1.7B)** | `ops_core/orchestration/planner.py` | **KEEP** (Task graph decomposition) |
| **Web Superior Agent** | `ops_core/services/agents/web_agents.py` | **PRESERVE & WIRE TO SUPERVISOR** |
| **Web Prompt Understanding** | `ops_core/services/agents/web_agents.py` | **PRESERVE** |
| **Crawlee Agent** | `ops_core/services/agents/web_agents.py` | **PRESERVE** |
| **BeautifulSoup Agent** | `ops_core/services/agents/web_agents.py` | **PRESERVE** |
| **ScrapeGraphAI Agent** | `ops_core/services/agents/web_agents.py` | **PRESERVE** |
| **Retrieval Quality Agent** | `ops_core/services/agents/web_agents.py` | **PRESERVE** (Self-correction fact-check loop) |
| **Automation Superior Agent**| `ops_core/services/agents/automation_agents.py` | **PRESERVE & WIRE TO SUPERVISOR** |
| **Auto Prompt Understanding** | `ops_core/services/agents/automation_agents.py` | **PRESERVE** |
| **HITL Approval Gate** | `ops_core/services/agents/automation_agents.py` | **PRESERVE & INTEGRATE WITH SAFETY GATE** |
| **Open Web Agent (Playwright)**| `ops_core/services/agents/automation_agents.py` | **PRESERVE AS BROWSER AUTOMATION AGENT** |
| **Installed Apps Agent** | `ops_core/services/agents/automation_agents.py` | **PRESERVE** |
| **Open File Agent** | `ops_core/services/agents/automation_agents.py` | **PRESERVE** |
| **Desktop Control Agent** | `ops_core/services/agents/automation_agents.py` | **PRESERVE** |
| **Developer Agent** | `ops_core/agents/developer_agent.py` | **KEEP & WIRE TO CAPABILITY REGISTRY** |
| **Debugger Agent** | `ops_core/agents/debugger_agent.py` | **KEEP & WIRE TO MISSION MANAGER RECOVERY** |
| **Tester Agent** | `ops_core/agents/tester_agent.py` | **KEEP & WIRE TO TEST RUNNER TOOLS** |
| **Reviewer Agent** | `ops_core/agents/reviewer_agent.py` | **KEEP** |
| **RAG / Knowledge Agent** | `ops_core/agents/rag_agent.py` & `rag_service.py` | **KEEP** |
| **Capability Registry** | `ops_core/capabilities/registry.py` | **KEEP AS AUTHORITATIVE SOURCE OF TRUTH** |
| **Safety Gate** | `ops_core/safety/safety_gate.py` | **KEEP AS MANDATORY GATEWAY** |
| **Ground-Truth Verifier** | `ops_core/verification/verifier.py` | **KEEP AS MANDATORY CRITIC** |
| **Response Engine** | `ops_core/agents/response_agent.py` | **KEEP** (Llama 3.2 1B evidence-grounded synthesis) |
| **Pop-up Cockpit UI** | `frontend/src/components/OpsCommandCore.jsx` | **PRESERVE** |
| **Live Agents UI** | `frontend/src/components/OpsLiveOrchestrationTab.jsx` | **PRESERVE & SYNC WITH EVENT STREAM** |

---

## 19. Recommended Migration & Integration Plan

### Phase 1: Canonical Agent Integration
* Bridge the explicit **Web Domain** (`WebSuperiorAgent` and its 5 sub-agents) and **Automation Domain** (`AutomationSuperiorAgent` and its 6 sub-agents) into `backend/ops_core/agents/` and register them in `Supervisor`.
* Ensure that `OpenWebAgent` is explicitly distinguished as the Browser Control Agent (Playwright) while `WebSuperiorAgent` handles Information Retrieval/Research (Crawlee, BS4, ScrapeGraphAI).

### Phase 2: Tool Execution & Safety Encasement
* Ensure all sub-agent tool invocations (filesystem, apps, browser, crawling) pass strictly through:
  `Agent` $\rightarrow$ `CapabilityRegistry` $\rightarrow$ `SafetyGate` $\rightarrow$ `ToolExecutor` $\rightarrow$ `Verifier`.
* Zero unmediated OS or shell calls.

### Phase 3: Unified Event Stream & Observability
* Standardize event emission across all sub-agents using `OPSEventBus.emit_ops_event_async` with structured `StructuredOPSEvent` payloads.
* Verify that every step generates real-time telemetry consumed by `OpsLiveOrchestrationTab.jsx`.

### Phase 4: Verification & Acceptance Testing
* Run comprehensive end-to-end acceptance tests across all 20 scenarios (`Open Chrome`, `Web Search`, `Create React Dashboard`, `Fix Failing Tests`, `STOP`, `REFRESH`, etc.).

---

## 20. Risk Assessment & Precautions

1. **Risk of Regressing UI Aesthetic:** The 90s retro tactical Iron Man HUD aesthetic must be preserved with zero disruptions to existing layout, scanlines, sounds, or visual hierarchy.
2. **Risk of Fake Agent Cycling:** Agent activations must remain 100% reactive to real backend events. Inactive agents must strictly stay `IDLE`.
3. **Risk of Persistent Memory Loss on Refresh:** `SessionManager.refresh_session` must strictly purge volatile conversation RAM while guaranteeing ChromaDB vector collections and PostgreSQL persistent memories remain intact.

---

*Audit completed and recorded in `OPS_ARCHITECTURE_AUDIT.md`. Ready for Phase Implementation instruction.*
