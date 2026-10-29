# O.P.S. Architectural Gaps & Prioritized Fix Plan

This document outlines the current state of implementation, identified legacy remnants, consolidated fixes, and prioritized roadmap items for O.P.S.

---

## 1. System Implementation Status

### 1.1 Fully Working Subsystems
- **Pop-up Cockpit UI:** React 18 HUD with tactical Iron Man retro styling, real-time command input, voice trigger bindings, live agent status telemetry, approval prompt modals, and mission progress cards.
- **Agents UI (Live View):** Dynamic 4-stage hierarchy visualization with real-time WebSocket connection to `StructuredOPSEvent` bus, tool badges, live step trackers, event timeline, and agent telemetry inspector modal.
- **Fast Router (Qwen3 0.6B):** Sub-50ms heuristic matching + Ollama structured JSON fallback for 5 execution modes (`CHAT`, `TASK`, `MISSION`, `MEMORY`, `CLARIFICATION`).
- **Supervisor & Mission Manager:** Stateful DAG mission execution engine with dependency resolution, step state persistence, and bounded 3-retry recovery.
- **Planner (Qwen3 1.7B):** Generates structured `MissionPlan` with assigned specialist agents, capabilities, arguments, and verification rules.
- **Specialized Developer Fleet:** Developer, Debugger, Tester, and Reviewer agents executing filesystem and terminal actions.
- **Capability Registry & Safety Gate:** Deterministic risk classifier (`SAFE`, `ELEVATED`, `DANGEROUS`, `FORBIDDEN`) with mandatory HITL approval gating.
- **Ground-Truth Verifier & Inspector:** Deterministic physical assertions (file stat, process check, exit codes, DOM inspection).
- **RAG & ChromaDB Persistence:** Vector storage, chunking, and semantic search for local codebase knowledge.
- **Session Manager (STOP vs REFRESH):** Accurate differentiation between freezing volatile execution and resetting context while preserving long-term memory.
- **Desktop & OS Control Engine:** Full PyAutoGUI execution with automatic Windows Native Win32 API (`ctypes.windll.user32`) and PowerShell `WScript.Shell` background fallbacks for mouse clicks, typing, hotkeys, and screenshots in any environment (interactive, virtual, background, or headless).

### 1.2 Partially Working / Configuration-Dependent Subsystems
- **Local Vision Subsystem:** Vision model prompts and image payload structures are defined, but requires local Ollama vision model (e.g., `llava` or `minicpm-v`) to be pulled and active for live screen parsing.
- **Voice Subsystem (Wispr Flow / Piper):** Service abstractions and fallback speech synthesis endpoints are integrated; requires local microphone hardware and Piper TTS binary on system PATH for native audio output.

### 1.3 Identified & Resolved Architectural Gaps
- **Gap 1 (Resolved):** Legacy duplicate routing endpoints were bypassing `SafetyGate` and `Verifier`.  
  *Fix:* Unified all frontend requests into `POST /api/v1/ops/execute/` via `Supervisor.handle_request()`.
- **Gap 2 (Resolved):** Agents UI was previously using mock state intervals.  
  *Fix:* Rebuilt `OpsLiveOrchestrationTab.jsx` to subscribe directly to `StructuredOPSEvent` payloads over `/ws/agent/`.
- **Gap 3 (Resolved):** Volatile session refresh was wiping long-term memories.  
  *Fix:* Separated in-memory `active_sessions` from persistent ChromaDB collections and PostgreSQL tables.

---

## 2. Prioritized Fix & Optimization Roadmap

| Priority | Component | Action Item | Target File / Module | Expected Outcome |
|---|---|---|---|---|
| **P0 (Immediate)** | Sub-Agent Tree Registration | Register the full 6 Web domain agents and 7 Automation domain agents directly in `Supervisor.agents` dict | `backend/ops_core/orchestration/supervisor.py` | Complete granular sub-agent tracking on Agents UI |
| **P1 (High)** | Ollama Vision Preloading | Add automatic detection and fallback for `llava:latest` in `OPSOllamaService` | `backend/ops_core/services/ollama_service.py` | Seamless screenshot & image inspection |
| **P2 (Medium)** | Multi-file Batch Verifier | Add parallel file existence and regex content assertions in `GroundTruthInspector` | `backend/ops_core/verification/ground_truth.py` | Faster multi-step mission verification |
| **P3 (Low)** | Voice Waveform Canvas | Add audio visualizer rendering in Cockpit when Wispr Flow is streaming | `frontend/src/components/OpsVoiceOrb.jsx` | Enhanced tactile retro Iron Man HUD feel |
