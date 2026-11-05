# O.P.S. 2.0 — Prompt Understanding & Reasoning Agent Root Cause Audit

## 1. Executive Summary

A comprehensive architectural audit was performed on the existing O.P.S. 2.0 Prompt Understanding, Intent Routing, and Task Planning subsystems:
- **Agent 1 (`global_intent_router.py`)**: Responsible for initial intent classification and operational engine/mode selection.
- **Agent 2 (`task_understanding_planner.py`)**: Assigned to Qwen3 1.7B for natural language understanding, context resolution, and task decomposition.
- **Routing Module (`router.py`)**: Legacy heuristic and regex classification engine.

### Critical Finding:
The primary failure mode in O.P.S. 2.0 was that **Agent 2 (`task_understanding_planner.py`) was not actually invoking the Qwen3 1.7B model to understand the user's objective, resolve conversational references, or plan tasks**. Instead, it relied entirely on a hardcoded Python `if/elif` switch based on the static `task_type` passed to it by Agent 1. Concurrently, Agent 1 (`router.py`) was heavily dependent on static keyword matching, making it vulnerable to keyword traps, missed negative constraints, and contextual blindness.

---

## 2. Root Cause Analysis

### Failure 1 — The Static Planning Trap (Bypassed Qwen3 1.7B Model)
* **Observed in Code**: In [`task_understanding_planner.py`](file:///d:/Projects/O.P.S/backend/research_system/orchestrator/agents/task_understanding_planner.py), lines 37–120:
  ```python
  if task_type == "CLARIFICATION":
      execution_plan = [...]
  elif task_type == "ANSWER":
      if answering_mode == "LLM":
          execution_plan = [...]
  ...
  ```
* **Root Cause**: The model assigned to understanding (`Qwen3 1.7B`) was never called during the planning node. The node merely populated static step templates. As a result, no dynamic reasoning, parameter extraction, constraint analysis, or task dependency computation ever occurred.

---

### Failure 2 — Syntactic Keyword Traps ("Explain" vs "Do")
* **Observed in Code**: In [`router.py`](file:///d:/Projects/O.P.S/backend/research_system/router.py), regular expressions checked for imperative action verbs (`create`, `open`, `write`, `launch`) regardless of grammatical mood or prefix:
  * Input: *"Explain how to create a React application."*
  * Regex matched: `create a React application` -> Classified as `TASK_AUTOMATION` (`DESKTOP`).
* **Root Cause**: Heuristic token scanning lacked syntactic awareness. The modal auxiliary *"How do I..."* or imperative *"Explain..."* was masked by trailing action keywords, causing informational inquiries to be misrouted to automation executors.

---

### Failure 3 — Blindness to Negative Constraints & Prohibitions
* **Observed in Code**: Neither `router.py` nor `task_understanding_planner.py` parsed negative constraints:
  * Input: *"Create a file, but do not overwrite anything that already exists."*
  * Input: *"Don't execute anything. Just explain what changes you would make."*
* **Root Cause**: The parser extracted `create a file` or `changes to project architecture` and discarded the qualifying conjunctions (`but do not`, `don't execute`). The resulting execution plan scheduled destructive actions or unauthorized operations.

---

### Failure 4 — Loss of Conversational Context and Pronoun Resolution
* **Observed in Code**: Multi-turn history was processed by concatenating the raw string text of the last 6 messages (`" ".join(...)`) and checking for general topic substrings (`has_recent_youtube = "youtube" in recent_text`).
* **Root Cause**:
  * If a user said: *"Create a Python project."* -> *"Use Django."* -> *"Actually, use TypeScript instead."*
  * The system could not resolve that *"TypeScript"* modified the project template from the earlier turn. It either created a detached single-word task or retained the stale Python configuration.
  * Pronouns like *"it"*, *"that file"*, or *"the other component"* could not be bound to specific antecedent entities.

---

### Failure 5 — Premature Guessing vs. Essential Clarification
* **Observed in Code**: When essential parameters were missing (e.g. *"Open my project and fix the error"*), the router attempted heuristic resolution against hardcoded defaults (`notepad` or `VS Code`) instead of identifying that the target project entity was undefined.
* **Root Cause**: The router only triggered clarification on a hardcoded list of 16 short phrases (`open it`, `do that`, `fix it`). Any prompt exceeding 3 words bypassed clarification and guessed an execution target.

---

### Failure 6 — Absence of a Structured Contract & Self-Correction
* **Observed in Code**: Router outputs were loosely typed dictionaries without formal Pydantic/dataclass schema validation. Invalid enum values or unresolvable task dependencies passed into LangGraph unvalidated, resulting in downstream runtime crashes.
* **Root Cause**: No deterministic validation or bounded self-correction loop was present to verify that the planned tasks matched the user's actual objective.

---

## 3. Targeted Architecture Upgrade Strategy

To remedy these structural defects, O.P.S. 2.0 requires:
1. **Upgraded Fast Router (Qwen3 0.6B)**: Provides fast syntactic classification, modal auxiliary detection ("explain" vs "execute"), and candidate domain tagging.
2. **True Multi-Stage Understanding & Planning Engine (Qwen3 1.7B)**:
   - **Stage 1**: Conversational Context & Anaphora Resolution.
   - **Stage 2**: Objective Classification (7 canonical types).
   - **Stage 3**: Entity & Exact Parameter Extraction (zero hallucination of paths).
   - **Stage 4**: Constraint & Exclusion Enforcement (negative constraints take precedence).
   - **Stage 5**: Dependency-Aware Task Decomposition.
   - **Stage 6**: Deterministic Engine & Mode Routing.
3. **Strict Structured Output Contract**: Validated schema with required fields, dependency checks, and confidence scoring.
4. **Deterministic Validation & Self-Correction Gate**: Automatically traps contract violations, keyword misclassifications, and missing required parameters before execution begins.
