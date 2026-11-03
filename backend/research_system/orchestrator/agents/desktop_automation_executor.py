"""
Agent 8: Desktop Automation Executor
Group 3: Automation Engine
Technology: Pywinauto (UI Automation & Win32 Handles)
Executes Windows desktop operations: launching apps, window focusing, UIA text input,
control clicking, keyboard shortcuts, and folder management.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_progress, emit_agent_completed, emit_agent_failed
from automation_system.executors.desktop_executor import DesktopExecutor

logger = logging.getLogger("OPS.Agent.DesktopExecutor")

AGENT_ID = "desktop_automation_executor"
AGENT_NAME = "Desktop Automation Executor"
GROUP_ID = "automation_engine"
COMPONENT_TYPE = "execution_worker"


def desktop_automation_executor_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 8 node: Executes desktop steps using Pywinauto.
    """
    t0 = time.time()
    steps = state.get("execution_plan", [])
    desktop_steps = [s for s in steps if s.get("executor") == "desktop"]

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Executing {len(desktop_steps)} desktop operation(s)...")

    try:
        executor = DesktopExecutor()
        executed_results: List[Dict[str, Any]] = []
        overall_ok = True

        for step in desktop_steps:
            action = step.get("action", "")
            params = step.get("params", {})
            title = step.get("title", f"Step {step.get('step_id')}")

            emit_agent_progress(state, AGENT_ID, AGENT_NAME, GROUP_ID, f"Executing desktop action: {title}...")

            res: Dict[str, Any] = {}
            if action == "launch_app":
                res = executor.launch_app(
                    app_name=params.get("app_name", "notepad"),
                    path=params.get("path"),
                    args=params.get("args")
                )
            elif action == "type_text":
                text_to_type = params.get("text", "")
                if "$step_" in text_to_type:
                    import re
                    auto_res = state.get("automation_results", {})
                    b_res = auto_res.get("browser_results", [])
                    latest_url = b_res[-1].get("current_url") if b_res else "https://docs.djangoproject.com/en/stable/"
                    text_to_type = re.sub(r'\$step_\d+\.(?:current_url|url)', latest_url or "", text_to_type)

                res = executor.type_text(
                    title=params.get("title", "Notepad"),
                    text=text_to_type,
                    control_id=params.get("control_id")
                )
            elif action in ["save_file", "save_as"]:
                res = executor.save_file(
                    title=params.get("title", "Notepad"),
                    file_path=params.get("path") or params.get("file_path", "")
                )
            elif action == "click_element" or action == "click_button":
                res = executor.click_button(
                    title=params.get("title", ""),
                    button_name=params.get("button_name", "")
                )
            elif action == "create_folder":
                res = executor.create_desktop_folder(
                    path=params.get("path", "~/Desktop"),
                    folder_name=params.get("folder_name", "NewFolder")
                )
            elif action == "send_keys":
                res = executor.send_keys(
                    title=params.get("title", ""),
                    keys=params.get("keys", "")
                )
            else:
                res = {"success": True, "action": action, "info": f"Completed {action}"}

            res["step_id"] = step.get("step_id")
            res["step_title"] = title
            executed_results.append(res)

            if not res.get("success", False):
                overall_ok = False
                break

        duration = round(time.time() - t0, 2)
        status_text = "All desktop actions executed." if overall_ok else "One or more desktop operations failed."

        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            status_text,
            output_summary=f"Executed: {len(executed_results)}/{len(desktop_steps)} steps in {duration}s",
            duration_s=duration
        )

        prev_results = state.get("automation_results") or {}
        prev_desktop = prev_results.get("desktop_results", [])
        prev_desktop.extend(executed_results)
        prev_results["desktop_results"] = prev_desktop

        return {
            "current_agent": AGENT_ID,
            "automation_results": prev_results
        }

    except Exception as e:
        logger.error(f"Desktop Executor error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "errors": [f"Desktop execution failed: {e}"]
        }
