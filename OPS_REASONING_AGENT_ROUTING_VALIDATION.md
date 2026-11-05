# O.P.S. 2.0 — Deterministic Routing Validation & Self-Correction

## 1. Purpose and Role

The **Deterministic Routing Validation Layer** (`validator.py`) functions as an infallible guardrail positioned directly between the probabilistic LLM reasoning engine (Qwen3 1.7B) and the LangGraph execution graph.

LLMs are prone to occasional syntax oversights, keyword capture, or optimism bias. The validation layer ensures that no hallucinated task, missed negative constraint, or unauthorized execution plan ever penetrates the execution boundary.

---

## 2. Invariant Enforcement Matrix

| Invariant | Trigger Condition | Deterministic Enforcement Action |
| :--- | :--- | :--- |
| **Negative Execution Constraint** | Prompt contains *"don't execute"*, *"explain only"*, *"no execution"* | Forces `task_type="ANSWER"`, `answering_engine="LLM"`, `automation_engine="NONE"`, wipes all execution plans, disables HITL prompts. |
| **Explanation vs Execution Guard** | Prompt begins with *"Explain how to..."*, *"How do I..."* | Neutralizes automation triggers; forces `task_type="ANSWER"`, `answering_engine="LLM"`. |
| **Fresh External Facts** | Prompt queries *"latest stable release"*, *"current version"*, *"status of"* | Upgrades `LLM` mode to `WEB` mode to prevent stale knowledge cutoff hallucination. |
| **Comparative Recommendation** | Prompt requests *"Compare X and Y and recommend"* | Sets answering mode to `HYBRID`, enforcing dual-branch execution (Web Research + Offline Reasoning). |
| **Direct Browser Navigation** | Prompt requests *"Open official website in Chrome"* | Routes to `BROWSER` automation rather than informational Web research. |
| **Cross-Platform Transfer** | Prompt requests *"Download file and open on my computer"* | Routes to `HYBRID` automation (`BrowserSuperiorAgent` -> `DesktopSuperiorAgent`). |
| **Missing Entity Disambiguation** | Directive references missing project/file (*"Open my project"*) with zero prior context | Flags `clarification_required=True`, halts execution, formats clarifying prompt for user. |
| **Explicit Non-Destructive Constraint** | Directive specifies *"do not overwrite anything"* | Injects `do_not_overwrite=True` into parameters and locks overwrite flag to `False`. |
| **Topological Dependency Order** | Multi-step folder, file, and code directives | Enforces sequential task dependencies (`step_i` depends on `step_i-1`), preventing race conditions. |

---

## 3. Bounded Correction Loop

If any invariant is violated:
1. The validation layer intercepts the contract.
2. Applies the necessary mathematical or semantic correction.
3. Appends an audit trail note to `reasoning_summary` (e.g. `[Auto-Validated: Enforced negative constraint]`).
4. Emits real-time notification telemetry to the Cockpit EventBus.
