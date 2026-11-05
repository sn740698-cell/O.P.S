"""
O.P.S. 2.0 — Deterministic Routing Validation & Self-Correction Layer
Section 9: Enforces strict syntactic, semantic, safety, and dependency invariants
on the ReasoningPlanContract before passing execution to LangGraph.
"""

import re
import logging
from typing import Dict, Any, List, Tuple
from .schema import ReasoningPlanContract

logger = logging.getLogger("OPS.Reasoning.Validator")


class ReasoningPlanValidator:
    """
    Deterministic validation and self-correction gate.
    Ensures model-generated reasoning contracts adhere strictly to
    system invariants, negative constraints, and factual boundaries.
    """

    @classmethod
    def validate_and_correct(
        cls,
        contract: ReasoningPlanContract,
        raw_query: str,
        context: Dict[str, Any]
    ) -> Tuple[ReasoningPlanContract, bool, List[str]]:
        """
        Validates contract and applies deterministic self-corrections.
        Returns: (corrected_contract, was_valid, list_of_corrections)
        """
        corrections: List[str] = []
        q_low = raw_query.lower()

        # Invariant 1: Negative Execution Constraints ("Don't execute", "Explain only")
        is_explain_only = any(p in q_low for p in [
            "don't execute", "dont execute", "do not execute",
            "explain only", "just explain", "explain how",
            "what changes you would make", "no execution"
        ])

        if is_explain_only and contract.task_type in ["AUTOMATION", "DEVELOPMENT"]:
            contract.task_type = "ANSWER"
            contract.answering_engine = "LLM"
            contract.automation_engine = "NONE"
            contract.execution_plan = []
            contract.approval_required = False
            corrections.append("Enforced negative constraint: Overrode AUTOMATION to ANSWER/LLM due to 'explain only / don't execute' instruction.")

        # Invariant 2: Explanation vs Execution ("Explain how to create React app" vs "Create React app")
        if q_low.startswith(("explain how to", "how do i", "explain the difference", "tell me how to")) or "explain how" in q_low:
            if contract.task_type in ["AUTOMATION", "DEVELOPMENT"]:
                contract.task_type = "ANSWER"
                contract.answering_engine = "LLM"
                contract.automation_engine = "NONE"
                contract.execution_plan = []
                contract.approval_required = False
                corrections.append("Corrected keyword trap: Prompt requests explanation of process, not execution.")

        # Invariant 3: External Fresh Facts Requirement ("latest stable version")
        has_latest_version_query = any(w in q_low for w in ["latest stable", "latest version", "current release", "what is the latest", "latest release", "recent updates"])
        if has_latest_version_query and contract.task_type in ["ANSWER", "RESEARCH"] and contract.answering_engine == "LLM":
            contract.task_type = "RESEARCH"
            contract.answering_engine = "WEB"
            corrections.append("Promoted LLM to WEB mode: Query requires verified fresh external facts.")

        # Invariant 4: Comparison & Recommendations ("Compare X and Y and recommend")
        if any(w in q_low for w in ["compare", "versus", "vs.", "difference between"]) and any(w in q_low for w in ["recommend", "which one", "suggest", "for o.p.s"]):
            if contract.task_type in ["ANSWER", "RESEARCH", "REASONING"] and contract.answering_engine != "HYBRID":
                contract.task_type = "REASONING"
                contract.answering_engine = "HYBRID"
                corrections.append("Set Answering Engine to HYBRID: Comparison with recommendation requires both research and deep reasoning.")

        # Invariant 5: Direct Website Opening in Browser vs Web Research
        # "Open the official Django documentation in Chrome" -> BROWSER AUTOMATION
        if any(w in q_low for w in ["open the official", "open in chrome", "open in browser", "navigate to"]) and any(w in q_low for w in ["chrome", "browser"]):
            if contract.automation_engine != "BROWSER" and contract.task_type != "AUTOMATION":
                contract.task_type = "AUTOMATION"
                contract.automation_engine = "BROWSER"
                contract.answering_engine = "NONE"
                corrections.append("Re-routed to Browser Automation: User directed opening a live browser window.")

        # Invariant 6: Cross-Engine Hybrid Automation ("Download PDF and open it on my computer")
        if any(w in q_low for w in ["download", "save"]) and any(w in q_low for w in ["and open it on my computer", "open on my computer", "then open it", "open it"]):
            if "download" in q_low and "computer" in q_low:
                contract.task_type = "AUTOMATION"
                contract.automation_engine = "HYBRID"
                corrections.append("Re-routed to Hybrid Automation: Workflow crosses Browser download and Desktop file opening.")

        # Invariant 6B: Composite Discovery + Download Workflow ("Find latest Node.js LTS, download it and save in Downloads")
        if any(w in q_low for w in ["find", "search", "locate"]) and any(w in q_low for w in ["download", "download it"]) and any(w in q_low for w in ["save", "downloads"]):
            contract.task_type = "COMPOSITE"
            contract.answering_engine = "WEB"
            contract.automation_engine = "HYBRID"
            corrections.append("Classified Composite workflow: Web discovery + Download/Save operation.")

        # Invariant 6C: Actionable Project Creation Request ("Create a React application...")
        if q_low.startswith(("create a react", "create a python", "create a django", "create a project")) and not is_explain_only:
            contract.task_type = "AUTOMATION"
            contract.automation_engine = "DESKTOP"
            contract.answering_engine = "NONE"
            contract.clarification_required = False
            corrections.append("Identified actionable project creation request: Routed to Desktop automation.")

        # Invariant 7: Missing Target Clarification ("Open my project and fix the error")
        if "open my project" in q_low or "fix the error" in q_low or "delete that file" in q_low:
            if not context.get("active_project") and not context.get("active_file") and not contract.parameters.get("target_path"):
                contract.task_type = "CLARIFICATION"
                contract.clarification_required = True
                contract.automation_engine = "NONE"
                contract.answering_engine = "NONE"
                contract.execution_plan = []
                if not contract.clarification_question:
                    contract.clarification_question = "Which project or file would you like me to open? Please specify the name or directory path."
                corrections.append("Activated Clarification Gate: Essential target entity (project/file) is missing from context.")

        # Invariant 8: Explicit Constraints Extraction ("do not overwrite")
        if "do not overwrite" in q_low or "dont overwrite" in q_low:
            if "do_not_overwrite" not in contract.constraints:
                contract.constraints.append("do_not_overwrite")
                contract.parameters["overwrite"] = False
                corrections.append("Extracted mandatory negative constraint: do_not_overwrite=True.")

        # Invariant 9: Sequential Dependencies in Multi-Step File/Folder Creation
        # "Create folder OPS_TEST, put Python file inside it, write program, open file"
        if len(contract.execution_plan) > 1:
            for i in range(1, len(contract.execution_plan)):
                prev_id = contract.execution_plan[i - 1].get("id") or f"step_{i}"
                cur_step = contract.execution_plan[i]
                if not cur_step.get("dependencies") and cur_step.get("action") not in ["launch_app_parallel"]:
                    cur_step["dependencies"] = [prev_id]

        # Invariant 10: Invariant Clarification Engine Guard
        if contract.task_type == "CLARIFICATION" or contract.clarification_required:
            contract.task_type = "CLARIFICATION"
            contract.clarification_required = True
            contract.automation_engine = "NONE"
            contract.answering_engine = "NONE"
            contract.approval_required = False

        was_valid = len(corrections) == 0
        if corrections:
            contract.reasoning_summary = f"{contract.reasoning_summary} [Auto-Validated: {'; '.join(corrections)}]"

        return contract, was_valid, corrections
