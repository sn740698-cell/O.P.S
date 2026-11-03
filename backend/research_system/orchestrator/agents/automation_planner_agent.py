"""
Agent 7: Automation Planner Agent
Group 3: Automation Engine
Model: Qwen3 1.7B / Structured Deterministic Planning
Decomposes user automation directives into ordered, verified execution steps.
Identifies target apps, URLs, file arguments, dependencies, and approval requirements.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_completed, emit_agent_failed
from automation_system.planner.automation_planner import AutomationPlanner, MODE_DESKTOP, MODE_BROWSER, MODE_HYBRID

logger = logging.getLogger("OPS.Agent.AutomationPlanner")

AGENT_ID = "automation_planner"
AGENT_NAME = "Automation Planner"
GROUP_ID = "automation_engine"
COMPONENT_TYPE = "reasoning_agent"


def automation_planner_agent_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 7 node: Creates structured automation plan with dependencies and verification contracts.
    """
    t0 = time.time()
    query = state.get("user_query", "").strip()
    auto_mode = state.get("automation_mode") or "DESKTOP"

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Planning {auto_mode} automation steps...")

    try:
        # Use verified AutomationPlanner from automation_system
        planned = AutomationPlanner.plan_task(query, context={"mode": auto_mode})
        steps = planned.get("steps", [])
        mode = planned.get("automation_mode", auto_mode)

        duration = round(time.time() - t0, 2)
        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            f"Generated {len(steps)} verified automation step(s).",
            output_summary=f"Steps: {len(steps)} | Mode: {mode}",
            duration_s=duration
        )

        return {
            "current_agent": AGENT_ID,
            "automation_mode": mode,
            "execution_plan": steps,
            "approval_required": planned.get("requires_approval", False)
        }

    except Exception as e:
        logger.error(f"Automation Planner error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "errors": [f"Automation planning failed: {e}"]
        }
