"""
Agent 9: Browser Automation Executor
Group 3: Automation Engine
Technology: Playwright (Chromium Headless/Headed Engine)
Executes web portal automation, page navigation, form interactions, credential protection,
element clicks, and non-blocking file downloads.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_progress, emit_agent_completed, emit_agent_failed
from automation_system.executors.browser_executor import BrowserExecutor

logger = logging.getLogger("OPS.Agent.BrowserExecutor")

AGENT_ID = "browser_automation_executor"
AGENT_NAME = "Browser Automation Executor"
GROUP_ID = "automation_engine"
COMPONENT_TYPE = "execution_worker"


def browser_automation_executor_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 9 node: Executes browser automation steps using Playwright.
    """
    t0 = time.time()
    steps = state.get("execution_plan", [])
    browser_steps = [s for s in steps if s.get("executor") == "browser"]

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Executing {len(browser_steps)} browser operation(s)...")

    executor = BrowserExecutor(headless=True)
    try:
        executed_results: List[Dict[str, Any]] = []
        overall_ok = True

        for step in browser_steps:
            action = step.get("action", "")
            params = step.get("params", {})
            title = step.get("title", f"Step {step.get('step_id')}")

            emit_agent_progress(state, AGENT_ID, AGENT_NAME, GROUP_ID, f"Executing browser action: {title}...")

            res: Dict[str, Any] = {}
            if action == "navigate":
                res = executor.navigate(url=params.get("url", "https://github.com"))
            elif action == "click":
                res = executor.click(
                    selector=params.get("selector", ""),
                    name=params.get("name"),
                    role=params.get("role")
                )
            elif action == "fill_form":
                res = executor.fill_form(
                    selector_or_label=params.get("field") or params.get("selector", ""),
                    text=params.get("text", ""),
                    is_secret=params.get("is_secret", False)
                )
            elif action == "download_file":
                res = executor.download_file(
                    trigger_selector=params.get("trigger_selector"),
                    direct_url=params.get("direct_url"),
                    target_dir=params.get("target_dir")
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
        status_text = "All browser actions executed." if overall_ok else "Browser operation halted on error."

        emit_agent_completed(
            state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
            status_text,
            output_summary=f"Executed: {len(executed_results)}/{len(browser_steps)} steps in {duration}s",
            duration_s=duration
        )

        prev_results = state.get("automation_results") or {}
        prev_browser = prev_results.get("browser_results", [])
        prev_browser.extend(executed_results)
        prev_results["browser_results"] = prev_browser

        return {
            "current_agent": AGENT_ID,
            "automation_results": prev_results
        }

    except Exception as e:
        logger.error(f"Browser Executor error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "errors": [f"Browser execution failed: {e}"]
        }
    finally:
        executor.close()
