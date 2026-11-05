# O.P.S. 2.0 — Prompt Understanding & Reasoning Agent Implementation Report

## 1. Executive Summary

We have upgraded the O.P.S. 2.0 Prompt Understanding and Intent Reasoning subsystem from brittle heuristic switches and bypassed models into a dedicated, schema-validated, multi-stage reasoning engine:
1. **Model Assignment Respected**: `Qwen3 0.6B` acts as the lightweight pre-router; `Qwen3 1.7B` serves as the central natural-language understanding, context resolution, and task decomposition engine.
2. **6-Stage Understanding Pipeline**: Formally implements Context Resolution (Stage 1), Objective Identification (Stage 2), Entity Extraction (Stage 3), Constraint Understanding (Stage 4), Dependency Decomposition (Stage 5), and Engine/Mode Selection (Stage 6).
3. **Structured Reasoning Contract**: Implemented Pydantic-validated `ReasoningPlanContract` adhering strictly to Section 8 of the system specifications.
4. **Deterministic Validation & Self-Correction Gate**: Replaces keyword traps with an invariant enforcement engine that guarantees explanation queries are never automated and negative constraints are strictly upheld.
5. **No Regressions**: Preserved the Cockpit UI, LangGraph checkpointer, Playwright/Pywinauto automation engines, and Pinecone RAG pipelines.

---

## 2. Directory Structure of Modified and Created Files

```
backend/research_system/orchestrator/
├── reasoning/
│   ├── __init__.py                  # Package exports
│   ├── schema.py                    # ReasoningPlanContract Pydantic models
│   ├── context_resolver.py          # Stage 1: Conversation & Anaphora Resolver
│   ├── prompt_engine.py             # System & user prompt templates for Qwen3 1.7B
│   ├── validator.py                 # Stage 9: Deterministic Invariant Validation
│   └── understanding_agent.py       # Main Qwen3 1.7B inference and contract builder
├── agents/
│   ├── task_understanding_planner.py# Updated Agent 2 delegating to UnderstandingAgent
│   └── global_intent_router.py      # Updated Agent 1 routing integration
└── router.py                        # Updated heuristic pre-routing engine
```

---

## 3. Code Modifications Breakdown

### A. New Modules
- **`schema.py`**: Declares `ReasoningPlanContract` with strict field validators on `task_type`, `answering_engine`, `automation_engine`, and `risk_level`.
- **`context_resolver.py`**: Tracks active application, active project, target files, and programming languages across multi-turn sessions. Supports override corrections (*"Actually, use TypeScript instead"*) while maintaining active project frameworks.
- **`validator.py`**: Infallible deterministic filter that enforces negative constraints (*"don't execute"*), explanation guards (*"explain how"*), fresh external fact requirements, and missing entity clarification gates.
- **`understanding_agent.py`**: Orchestrates `ollama_client` calls to `MODEL_QWEN_1_7B` (`hf.co/Qwen/Qwen3-1.7B-GGUF:Q8_0`), handles JSON serialization, and binds the validation gate.

### B. Upgraded Existing Components
- **`task_understanding_planner.py`**: Replaced static if/else planning switch with a direct call to `AdvancedPromptUnderstandingAgent.understand_and_plan()`. The node now dynamically provisions dependencies, parameters, and approval gates.
- **`router.py`**: Syntactically disambiguates modal inquiries (*"Explain how..."*, *"How do I..."*) from actionable directives (*"Create..."*, *"Open..."*).
