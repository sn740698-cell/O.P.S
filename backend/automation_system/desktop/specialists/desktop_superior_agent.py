"""
O.P.S. 2.0 Desktop Automation — Superior Agent
Hierarchical supervisor coordinating 8 specialist desktop agents:
- D1: Application Controller Agent (app lifecycle, resolution, launch, close)
- D2: Window Management Agent (discovery, handles, geometry, focus)
- D3: GUI Interaction Agent (buttons, menus, dialogs, control tree)
- D4: File and Folder Agent (files, folders, system guards, backups)
- D5: Keyboard and Input Agent (typing, ValuePattern, shortcuts)
- D6: Code Generation & File Writer Agent (code synthesis, AST parse, atomic write)
- D7: Desktop Verification Agent (window, file, content, process checks)
- D8: Desktop Recovery Agent (refocus, restart, bounded retries)
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional

from research_system.events.event_bus import event_bus
from automation_system.desktop.specialists.d1_discovery_agent import D1_DiscoveryAgent
from automation_system.desktop.specialists.d2_app_agent import D2_AppAgent
from automation_system.desktop.specialists.d3_window_agent import D3_WindowAgent
from automation_system.desktop.specialists.d4_gui_agent import D4_GUIAgent
from automation_system.desktop.specialists.d5_input_agent import D5_InputAgent
from automation_system.desktop.specialists.d6_file_agent import D6_FileAgent
from automation_system.desktop.specialists.d7_code_agent import D7_CodeAgent
from automation_system.desktop.specialists.d8_verification_agent import D8_VerificationRecoveryAgent
from automation_system.desktop.specialists.d1_app_agent import D1_AppAgent
from automation_system.desktop.specialists.d2_window_agent import D2_WindowAgent
from automation_system.desktop.specialists.d3_gui_agent import D3_GUIAgent
from automation_system.desktop.specialists.d4_file_agent import D4_FileAgent
from automation_system.desktop.specialists.d6_code_agent import D6_CodeAgent
from automation_system.desktop.specialists.d7_verification_agent import D7_VerificationAgent
from automation_system.desktop.specialists.d8_recovery_agent import D8_RecoveryAgent

logger = logging.getLogger("OPS.Desktop.SuperiorAgent")


class DesktopSuperiorAgent:
    """
    Desktop Superior Agent: Orchestrates specialist sub-agents (D1-D8)
    to fulfill desktop directives with real-time telemetry and empirical verification.
    """

    def __init__(self, request_id: Optional[str] = None, conversation_id: Optional[str] = None):
        self.agent_id = "superior_desktop_agent"
        self.agent_name = "Desktop Automation Superior Agent"
        self.request_id = request_id or f"req_desktop_{int(time.time())}"
        self.conversation_id = conversation_id or "default_session"

        # Initialize the 8 Specialist Agents
        self.d1_discovery = D1_DiscoveryAgent()
        self.d2_app = D2_AppAgent()
        self.d3_window = D3_WindowAgent()
        self.d4_gui = D4_GUIAgent()
        self.d5_input = D5_InputAgent()
        self.d6_file = D6_FileAgent()
        self.d7_code = D7_CodeAgent()
        self.d8_verify = D8_VerificationRecoveryAgent()

        # Legacy aliases
        self.d1_app = self.d2_app
        self.d2_window = self.d3_window
        self.d3_gui = self.d4_gui
        self.d4_file = self.d6_file
        self.d6_code = self.d7_code
        self.d7_verify = self.d8_verify
        self.d8_recovery = self.d8_verify

    def _emit_event(self, specialist_name: str, event_type: str, status: str, summary: str, extra: Optional[Dict] = None):
        """Emits structured real-time telemetry to O.P.S. EventBus for Cockpit Agent Preview."""
        try:
            extra_data = extra or {}
            event_bus.publish(
                request_id=self.request_id,
                execution_id=f"exec_{int(time.time() * 1000)}",
                conversation_id=self.conversation_id,
                node_id="desktop_superior_agent",
                component_name=specialist_name,
                component_type="SPECIALIST_AGENT",
                event_type=event_type,
                execution_status=status,
                safe_task_summary=summary,
                superior_agent="DesktopSuperiorAgent",
                specialist_agent=specialist_name,
                **extra_data
            )
        except Exception as e:
            logger.debug(f"Failed to publish event: {e}")

    def execute_directive(self, directive: str, steps: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Executes a high-level desktop directive by delegating to specialists,
        tracking state transitions, and empirically verifying results.
        """
        t0 = time.time()
        logger.info(f"DesktopSuperiorAgent received directive: '{directive}'")

        self._emit_event(
            "DesktopSuperiorAgent",
            "agent.started",
            "RUNNING",
            f"Orchestrating desktop directive: {directive}",
            {"total_steps": len(steps) if steps else 1}
        )

        executed_steps = []

        if steps and len(steps) > 0:
            for i, step in enumerate(steps):
                step_res = self.execute_step(step, step_idx=i + 1, total_steps=len(steps))
                executed_steps.append(step_res)
                if not step_res.get("success"):
                    logger.warning(f"Step {i+1} failed: {step_res.get('error')}")
                    break
        else:
            # Plan and execute common high-level directives
            res = self._handle_implicit_directive(directive)
            executed_steps.append(res)

        final_ok = all(s.get("success", False) for s in executed_steps)
        duration = round(time.time() - t0, 2)
        status_str = "COMPLETED" if final_ok else "FAILED"

        self._emit_event(
            "DesktopSuperiorAgent",
            "agent.completed",
            status_str,
            f"Desktop execution {status_str.lower()} in {duration}s",
            {"executed_steps": len(executed_steps), "duration_s": duration}
        )

        return {
            "success": final_ok,
            "directive": directive,
            "superior_agent": self.agent_id,
            "executed_steps": executed_steps,
            "duration_s": duration
        }

    def execute_step(self, step: Dict[str, Any], step_idx: int = 1, total_steps: int = 1) -> Dict[str, Any]:
        """Dispatches an individual step to targeted desktop specialist agent."""
        action = step.get("action", "").lower()
        params = step.get("params", {})
        target = step.get("target") or step.get("app") or step.get("path") or params.get("app_name") or params.get("path") or params.get("title") or params.get("file_path") or ""
        value = step.get("value") or step.get("text") or step.get("content") or params.get("text") or params.get("content") or ""

        logger.info(f"DesktopSuperiorAgent executing step {step_idx}/{total_steps}: {action} -> {target}")

        # 0. Application Discovery
        if action in ["discover_app", "check_app", "find_app"]:
            self._emit_event("D1_DiscoveryAgent", "agent.handoff", "RUNNING", f"Discovering installed status: {target}")
            disc = self.d1_discovery.discover_application(target)
            return {"success": disc.get("installed", False), "action": "discover_app", "app_name": target, **disc}

        # 1. Launch / Focus
        elif action in ["launch", "launch_app", "open_app", "start_app"]:
            path = params.get("path") or target
            app_name = params.get("app_name") or target
            self._emit_event("D1_DiscoveryAgent", "agent.handoff", "RUNNING", f"Verifying installation of {app_name}")
            disc = self.d1_discovery.discover_application(app_name)
            if not disc.get("installed"):
                self._emit_event("D1_DiscoveryAgent", "agent.handoff", "WARNING", f"Application '{app_name}' not installed")
                return {"success": False, "installed": False, "error": disc.get("message"), "web_alternative_url": disc.get("web_alternative_url")}

            resolved_target = disc.get("resolved_path") or disc.get("uri_scheme") or path
            valid_path = resolved_target if (resolved_target and (os.path.isabs(resolved_target) or resolved_target.lower().endswith(".exe") or resolved_target.endswith(":"))) else None
            self._emit_event("D2_AppAgent", "agent.handoff", "RUNNING", f"Launching application: {app_name}")
            l_res = self.d2_app.launch(app_name, path=valid_path)
            if l_res.get("success"):
                self._emit_event("D8_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying window: {app_name}")
                v_res = self.d8_verify.verify_window(app_name)
                l_res["verification"] = v_res
            return l_res

        # 2. Close Application
        elif action in ["close", "close_app", "terminate"]:
            self._emit_event("D1_AppAgent", "agent.handoff", "RUNNING", f"Closing application: {target}")
            c_res = self.d1_app.close(target)
            self._emit_event("D7_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying process closed: {target}")
            v_res = self.d7_verify.verify_closed(target)
            c_res["verification"] = v_res
            return c_res

        # 3. Window Management
        elif action in ["focus_window", "maximize_window", "minimize_window", "restore_window"]:
            state = action.replace("_window", "")
            if state == "focus":
                self._emit_event("D2_WindowAgent", "agent.handoff", "RUNNING", f"Focusing window: {target}")
                return self.d2_window.focus_window(target)
            else:
                self._emit_event("D2_WindowAgent", "agent.handoff", "RUNNING", f"Setting window state ({state}): {target}")
                return self.d2_window.set_window_state(target, state=state)

        # 4. GUI Click
        elif action in ["click", "click_button"]:
            self._emit_event("D3_GUIAgent", "agent.handoff", "RUNNING", f"Clicking GUI control on {target}: {value}")
            return self.d3_gui.click_button(target, value)

        # 5. Type Text
        elif action in ["type", "type_text", "write_text"]:
            self._emit_event("D5_InputAgent", "agent.handoff", "RUNNING", f"Typing text into {target}")
            t_res = self.d5_input.type_text(target, value)
            return t_res

        # 6. Keyboard Shortcut
        elif action in ["send_keys", "shortcut", "key_press"]:
            self._emit_event("D5_InputAgent", "agent.handoff", "RUNNING", f"Sending shortcut '{value}' to {target}")
            return self.d5_input.send_keys(target, value)

        # 7. Code Generation & File Writing
        elif action in ["write_code", "generate_code"]:
            self._emit_event("D6_CodeAgent", "agent.handoff", "RUNNING", f"Generating code file with AST validation: {target}")
            w_res = self.d6_code.generate_and_write(target, value)
            if w_res.get("success"):
                self._emit_event("D7_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying code file on disk: {target}")
                v_res = self.d7_verify.verify_file(target)
                w_res["verification"] = v_res
            return w_res

        # 8. File / Folder Operations
        elif action in ["create_file", "write_file"]:
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Creating file: {target}")
            return self.d4_file.create_file(target, content=value)

        elif action in ["create_folder", "create_directory", "mkdir"]:
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Creating folder: {target}")
            return self.d4_file.create_folder(target)

        elif action in ["delete_folder", "rmdir"]:
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Deleting folder: {target}")
            return self.d4_file.delete_folder(target)

        elif action in ["rename_file", "rename"]:
            dst = step.get("params", {}).get("new_path") or step.get("new_path") or value
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Renaming file: {target} -> {dst}")
            return self.d4_file.rename_file(target, dst)

        elif action in ["copy_file", "copy"]:
            dst = step.get("params", {}).get("dst_path") or step.get("destination") or step.get("dst") or value
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Copying file: {target} -> {dst}")
            return self.d4_file.copy_file(target, dst)

        elif action in ["move_file", "move"]:
            dst = step.get("params", {}).get("dst_path") or step.get("destination") or step.get("dst") or value
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Moving file: {target} -> {dst}")
            return self.d4_file.move_file(target, dst)

        elif action in ["read_file"]:
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Reading file: {target}")
            return self.d4_file.read_file(target)

        elif action in ["edit_file"]:
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Editing file: {target}")
            return self.d4_file.edit_file(target, new_content=value)

        elif action in ["delete_file"]:
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Deleting file: {target}")
            return self.d4_file.delete_file(target)

        elif action in ["open_file"]:
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Opening file: {target}")
            return self.d4_file.open_file(target)

        elif action in ["open_folder"]:
            self._emit_event("D4_FileAgent", "agent.handoff", "RUNNING", f"Opening folder: {target}")
            return self.d4_file.open_folder(target)

        # 9. Verification
        elif action in ["verify_window"]:
            self._emit_event("D7_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying window: {target}")
            return self.d7_verify.verify_window(target)

        elif action in ["verify_file"]:
            self._emit_event("D7_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying file: {target}")
            return self.d7_verify.verify_file(target)

        else:
            return {"success": False, "error": f"Unknown desktop action: '{action}'"}

    def _handle_implicit_directive(self, directive: str) -> Dict[str, Any]:
        """Handles natural language desktop directives that don't supply pre-parsed steps."""
        dir_lower = directive.lower()

        # Directive: Open Notepad and type ...
        if "notepad" in dir_lower and "type" in dir_lower:
            import re
            match = re.search(r"type\s+['\"]?([^'\"]+)['\"]?", directive, re.IGNORECASE)
            text_to_type = match.group(1) if match else "Hello OPS."

            # Step 1: Launch Notepad via D1
            self._emit_event("D1_AppAgent", "agent.handoff", "RUNNING", "Launching Notepad")
            l_res = self.d1_app.launch("notepad")
            time.sleep(1.0)

            # Step 2: Type text via D5
            self._emit_event("D5_InputAgent", "agent.handoff", "RUNNING", f"Typing '{text_to_type}' into Notepad")
            t_res = self.d5_input.type_text("Notepad", text_to_type)

            # Step 3: Verify via D7
            self._emit_event("D7_VerificationAgent", "agent.handoff", "RUNNING", "Verifying Notepad window and content")
            v_res = self.d7_verify.verify_window("Notepad")

            return {
                "success": l_res.get("success", False) and t_res.get("success", False) and v_res.get("verified", False),
                "launch": l_res,
                "typing": t_res,
                "verification": v_res
            }

        # Directive: Launch app
        elif any(k in dir_lower for k in ["open ", "launch ", "start "]):
            import re
            m = re.search(r"(?:open|launch|start)\s+([a-zA-Z0-9_\-\. ]+)", directive, re.IGNORECASE)
            app = m.group(1).strip() if m else "notepad"
            self._emit_event("D1_AppAgent", "agent.handoff", "RUNNING", f"Launching {app}")
            l_res = self.d1_app.launch(app)
            self._emit_event("D7_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying {app} window")
            v_res = self.d7_verify.verify_window(app)
            l_res["verification"] = v_res
            return l_res

        # Directive: Close app
        elif any(k in dir_lower for k in ["close ", "terminate ", "exit "]):
            import re
            m = re.search(r"(?:close|terminate|exit)\s+([a-zA-Z0-9_\-\. ]+)", directive, re.IGNORECASE)
            app = m.group(1).strip() if m else "notepad"
            self._emit_event("D1_AppAgent", "agent.handoff", "RUNNING", f"Closing {app}")
            c_res = self.d1_app.close(app)
            self._emit_event("D7_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying {app} process termination")
            v_res = self.d7_verify.verify_closed(app)
            c_res["verification"] = v_res
            return c_res

        # Default fallback
        return {"success": False, "error": f"Could not formulate desktop steps for: '{directive}'"}
