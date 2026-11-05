# O.P.S. 2.0 — Advanced Prompt Understanding & Reasoning Agent Architecture

## 1. Architectural Overview

The Prompt Understanding and Reasoning subsystem has been upgraded from static template planning and keyword heuristics into an intelligent, multi-stage reasoning engine:

```
                                [ User Natural-Language Directive ]
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │ STAGE 1: Conversation Context & Anaphora Resolver   │
                     │ (Historical turns, pronouns, entities, corrections) │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │ STAGE 2–6: Qwen3 1.7B Main Understanding Engine    │
                     │ - Stage 2: Actual Objective Classification          │
                     │ - Stage 3: Entity & Parameter Extraction            │
                     │ - Stage 4: Constraint & Exclusion Understanding     │
                     │ - Stage 5: Dependency-Aware Task Decomposition      │
                     │ - Stage 6: Operational Engine & Mode Selection      │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │ STAGE 7: Structured Reasoning Contract Synthesis    │
                     │ (Validated Pydantic Schema: ReasoningPlanContract)  │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                     ┌─────────────────────────────────────────────────────┐
                     │ STAGE 8: Deterministic Validation & Self-Correction │
                     │ - Negative constraint enforcement ("don't execute") │
                     │ - Explanation vs execution guard ("explain how")    │
                     │ - Missing target clarification gate                 │
                     │ - External fact promotion to Web mode               │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                                   [ Validated Plan Output ]
                               (Dispatched to Central LangGraph)
```

---

## 2. Model Roles and Responsibilities

### Qwen3 0.6B — Fast Pre-Classifier
- **Model**: `hf.co/Qwen/Qwen3-0.6B-GGUF:Q8_0`
- **Role**: Lightweight syntactic triage, obvious entity detection, and low-latency pre-routing tags.
- **Strict Boundary**: Never solely responsible for task planning, file creation decisions, or downstream execution approval.

### Qwen3 1.7B — Main Understanding & Reasoning Model
- **Model**: `hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0`
- **Role**: Natural language interpretation, conversational context resolution, constraint preservation, task decomposition, and structured plan synthesis.

---

## 3. The 6-Stage Understanding Pipeline

1. **Stage 1 — Context & Anaphora Resolution**:
   Tracks active application, project, file, language, and framework across multi-turn messages. Resolves words like *"it"*, *"that"*, *"the other component"*, and user corrections (e.g. *"Use TypeScript instead"*).
2. **Stage 2 — Objective Identification**:
   Classifies directives into seven canonical task types:
   `ANSWER`, `RESEARCH`, `REASONING`, `AUTOMATION`, `DEVELOPMENT`, `COMPOSITE`, `CLARIFICATION`.
3. **Stage 3 — Entity & Parameter Extraction**:
   Extracts application names, URLs, file paths, and options without hallucinating missing paths.
4. **Stage 4 — Constraint Understanding**:
   Enforces mandatory exclusions (*"don't modify existing files"*, *"explain only"*, *"do not overwrite"*). Negative constraints take absolute precedence.
5. **Stage 5 — Task Decomposition & Planning**:
   Breaks complex tasks into ordered subtasks, assigning responsible specialist agents and dependency links.
6. **Stage 6 — Engine & Mode Selection**:
   - **Answering Engine**: `LLM` (offline reasoning), `WEB` (fresh facts), `HYBRID` (research + synthesis).
   - **Automation Engine**: `DESKTOP` (Pywinauto), `BROWSER` (Playwright), `HYBRID` (Cross-platform).

---

## 4. Deterministic Self-Correction Layer

A deterministic validation gate audits every model contract before LangGraph execution:
- Overrides automation requests to `ANSWER/LLM` when negative constraints (*"don't execute"*, *"explain only"*) are present.
- Promotes queries containing *"latest stable version"* to `WEB` mode.
- Sets comparison queries with recommendations to `HYBRID` mode.
- Automatically triggers the `CLARIFICATION` gate when essential target entities (e.g. undefined project names) are missing.
