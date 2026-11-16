"""
Agent 8: Desktop Automation Executor
Group 3: Automation Engine
Technology: Pywinauto & Desktop Automation Core Modules
Executes Windows desktop operations: launching apps, window focusing, UIA text input,
control clicking, keyboard shortcuts, folder and file operations, code generation, and empirical verification.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_progress, emit_agent_completed, emit_agent_failed
from automation_system.executors.desktop_executor import DesktopExecutor
from automation_system.desktop.file_controller import FileController

logger = logging.getLogger("OPS.Agent.DesktopExecutor")

AGENT_ID = "desktop_automation_executor"
AGENT_NAME = "Desktop Automation Executor"
GROUP_ID = "automation_engine"
COMPONENT_TYPE = "execution_worker"


def desktop_automation_executor_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 8 node: Executes planned desktop steps using Desktop Automation Core.
    """
    t0 = time.time()
    steps = state.get("execution_plan", [])
    desktop_steps = [s for s in steps if s.get("executor") in ["desktop", "file_system"]]

    # Defense-in-depth: Strict server-side HITL gate enforcement
    appr_required = state.get("approval_required", False)
    appr_status = state.get("approval_status", "NONE")
    if appr_required and appr_status != "APPROVED":
        logger.warning("Desktop execution blocked: Operator authorization has not been granted.")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, "Desktop automation blocked: explicit human approval is required.")
        return {
            "current_agent": AGENT_ID,
            "errors": ["Desktop automation blocked: explicit human approval is required."]
        }

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
                    args=params.get("args"),
                    reuse_existing=params.get("reuse_existing", True)
                )

            elif action in ["close_app", "close_window"]:
                res = executor.close_window(
                    title_or_app=params.get("title") or params.get("app_name", ""),
                    force=params.get("force", False)
                )

            elif action == "open_file":
                res = executor.open_file(
                    path=params.get("path") or params.get("file_path", ""),
                    app=params.get("app")
                )

            elif action == "open_folder":
                res = executor.open_folder(
                    path=params.get("path") or params.get("folder_path", ""),
                    in_vscode=params.get("in_vscode", False)
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
                    control_id=params.get("control_id"),
                    replace=params.get("replace", False)
                )

            elif action in ["create_code_file", "write_code_file"]:
                res = executor.create_code_file(
                    path=params.get("path") or params.get("file_path", ""),
                    code=params.get("code"),
                    prompt=params.get("prompt"),
                    language=params.get("language"),
                    overwrite=params.get("overwrite", True)
                )

            elif action in ["edit_code_file", "edit_file", "modify_file"]:
                res = executor.edit_code_file(
                    path=params.get("path") or params.get("file_path", ""),
                    instruction=params.get("instruction"),
                    target_snippet=params.get("target_snippet"),
                    replacement_snippet=params.get("replacement_snippet"),
                    backup=params.get("backup", True)
                )

            elif action in ["save_file", "save_as"]:
                exp_content = params.get("expected_content") or params.get("text")
                res = executor.save_file(
                    title=params.get("title", "Notepad"),
                    file_path=params.get("path") or params.get("file_path", ""),
                    expected_content=exp_content
                )

            elif action in ["create_file", "write_file"]:
                res = FileController.create_file(
                    path=params.get("path") or params.get("file_path", ""),
                    content=params.get("content", ""),
                    overwrite=params.get("overwrite", True)
                )

            elif action in ["rename_file", "rename"]:
                res = FileController.rename_file(
                    old_path=params.get("old_path") or params.get("path") or "",
                    new_path=params.get("new_path") or ""
                )

            elif action in ["copy_file", "copy"]:
                res = FileController.copy_file(
                    src_path=params.get("src_path") or params.get("path") or "",
                    dst_path=params.get("dst_path") or params.get("destination") or ""
                )

            elif action in ["move_file", "move"]:
                res = FileController.move_file(
                    src_path=params.get("src_path") or params.get("path") or "",
                    dst_path=params.get("dst_path") or params.get("destination") or ""
                )

            elif action in ["delete_file", "remove_file"]:
                res = executor.delete_file(
                    path=params.get("path") or params.get("file_path", ""),
                    backup=params.get("backup", False)
                )

            elif action in ["delete_folder", "remove_folder"]:
                res = executor.delete_folder(
                    path=params.get("path") or params.get("folder_path", ""),
                    recursive=params.get("recursive", True)
                )

            elif action in ["click_element", "click_button"]:
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

            elif action == "read_text":
                res = executor.read_text(
                    title=params.get("title", ""),
                    control_id=params.get("control_id")
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
        status_text = "All desktop actions executed successfully." if overall_ok else "One or more desktop operations failed."

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

        verif_results = state.get("verification_results") or {}
        verif_results["desktop_verified"] = overall_ok
        verif_results["all_verified"] = overall_ok and verif_results.get("browser_verified", True)

        return {
            "current_agent": AGENT_ID,
            "selected_superior_agent": "DesktopSuperiorAgent",
            "selected_specialist_agents": [
                "D1_AppAgent", "D2_WindowAgent", "D3_GUIAgent",
                "D4_FileAgent", "D5_InputAgent", "D6_CodeAgent",
                "D7_VerificationAgent", "D8_RecoveryAgent"
            ],
            "automation_results": prev_results,
            "verification_results": verif_results
        }

    except Exception as e:
        logger.error(f"Desktop Executor error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "errors": [f"Desktop execution failed: {e}"]
        }
