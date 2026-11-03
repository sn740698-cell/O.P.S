"""
O.P.S. 2.0 Hybrid Automation Executor
Coordinates combined browser (Playwright) and desktop (Pywinauto) workflows
with dependency resolution, intermediate filesystem operations (extract archive, verify files),
and step-by-step verification gates.
"""

import os
import time
import zipfile
import logging
from typing import Dict, Any, List, Optional
from automation_system.executors.desktop_executor import DesktopExecutor
from automation_system.executors.browser_executor import BrowserExecutor
from automation_system.verification.verifier import AutomationVerifier

logger = logging.getLogger("OPS.HybridExecutor")


class HybridExecutor:
    """
    Executes multi-stage workflows bridging web actions and desktop application interactions.
    Resolves dynamic inter-step data bindings (e.g. $step_1.download_path).
    """

    def __init__(self, desktop_executor: Optional[DesktopExecutor] = None, browser_executor: Optional[BrowserExecutor] = None):
        self.desktop = desktop_executor or DesktopExecutor()
        self.browser = browser_executor or BrowserExecutor()
        self.step_outputs: Dict[int, Dict[str, Any]] = {}

    def extract_archive(self, archive_path: str, extract_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Safely extracts a ZIP or TAR archive to a destination folder and verifies its contents.
        """
        t0 = time.time()
        archive_clean = os.path.expanduser(archive_path)
        dest_folder = os.path.expanduser(extract_to) if extract_to else os.path.splitext(archive_clean)[0]

        if not os.path.exists(archive_clean):
            return {
                "success": False,
                "action": "extract_archive",
                "error": f"Archive file '{archive_clean}' does not exist on filesystem."
            }

        try:
            os.makedirs(dest_folder, exist_ok=True)
            with zipfile.ZipFile(archive_clean, 'r') as zip_ref:
                zip_ref.extractall(dest_folder)

            verif = AutomationVerifier.verify_folder_exists(dest_folder, timeout=3.0)
            extracted_items = os.listdir(dest_folder) if os.path.exists(dest_folder) else []

            return {
                "success": verif.get("verified", False),
                "action": "extract_archive",
                "archive_path": archive_clean,
                "extracted_path": dest_folder,
                "extracted_items_count": len(extracted_items),
                "duration_s": round(time.time() - t0, 2),
                "verification": verif
            }
        except Exception as e:
            logger.error(f"Archive extraction failed: {e}")
            return {"success": False, "action": "extract_archive", "error": str(e)}

    def resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitutes dynamic dependency placeholders like '$step_1.download_path'
        or '$step_2.extracted_path' with verified outputs from prior steps.
        """
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str) and v.startswith("$step_"):
                # Format: $step_{id}.{field}
                parts = v[1:].split(".", 1)
                if len(parts) == 2:
                    try:
                        dep_id = int(parts[0].replace("step_", ""))
                        field = parts[1]
                        step_res = self.step_outputs.get(dep_id, {})
                        val = step_res.get(field) or step_res.get("file_path") or step_res.get("extracted_path") or v
                        resolved[k] = val
                        continue
                    except Exception:
                        pass
            elif isinstance(v, list):
                res_list = []
                for item in v:
                    if isinstance(item, str) and item.startswith("$step_"):
                        parts = item[1:].split(".", 1)
                        if len(parts) == 2:
                            try:
                                dep_id = int(parts[0].replace("step_", ""))
                                field = parts[1]
                                step_res = self.step_outputs.get(dep_id, {})
                                val = step_res.get(field) or step_res.get("file_path") or step_res.get("extracted_path") or item
                                res_list.append(val)
                                continue
                            except Exception:
                                pass
                    res_list.append(item)
                resolved[k] = res_list
                continue
            resolved[k] = v
        return resolved

    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes an individual step using either desktop, browser, or system execution engine.
        """
        executor_type = step.get("executor", "desktop").lower()
        action = step.get("action", "")
        raw_params = step.get("params", {})
        params = self.resolve_params(raw_params)
        step_id = step.get("step_id", 1)

        result = {}
        if executor_type == "desktop":
            if action == "launch_app":
                result = self.desktop.launch_app(
                    app_name=params.get("app_name", "notepad"),
                    path=params.get("path"),
                    args=params.get("args")
                )
            elif action == "connect_window":
                result = self.desktop.connect_window(title=params.get("title", ""))
            elif action == "type_text":
                result = self.desktop.type_text(
                    title=params.get("title", ""),
                    text=params.get("text", ""),
                    control_id=params.get("control_id")
                )
            elif action == "click_element" or action == "click_button":
                result = self.desktop.click_button(
                    title=params.get("title", ""),
                    button_name=params.get("button_name") or params.get("target", "")
                )
            elif action == "send_keys":
                result = self.desktop.send_keys(
                    title=params.get("title", ""),
                    keys=params.get("keys", "")
                )
            elif action == "handle_dialog":
                result = self.desktop.handle_dialog(
                    title=params.get("dialog_title") or params.get("title", ""),
                    action=params.get("action", "accept"),
                    button_name=params.get("button_name")
                )
            elif action == "create_folder":
                result = self.desktop.create_desktop_folder(
                    path=params.get("path", "~/Desktop"),
                    folder_name=params.get("folder_name", "NewFolder")
                )
            else:
                result = {"success": False, "error": f"Unknown desktop action '{action}'"}

        elif executor_type == "browser":
            if action == "navigate":
                result = self.browser.navigate(
                    url=params.get("url", ""),
                    wait_until=params.get("wait_until", "load")
                )
            elif action == "click":
                result = self.browser.click(
                    selector=params.get("selector", ""),
                    name=params.get("name"),
                    role=params.get("role")
                )
            elif action == "fill_form":
                result = self.browser.fill_form(
                    selector_or_label=params.get("selector") or params.get("field", ""),
                    text=params.get("text", ""),
                    is_secret=params.get("is_secret", False)
                )
            elif action == "select_option":
                result = self.browser.select_option(
                    selector=params.get("selector", ""),
                    value=params.get("value", "")
                )
            elif action == "download_file":
                result = self.browser.download_file(
                    trigger_selector=params.get("trigger_selector"),
                    direct_url=params.get("direct_url") or params.get("url"),
                    target_dir=params.get("target_dir")
                )
            elif action == "take_screenshot":
                result = self.browser.capture_screenshot(output_path=params.get("output_path"))
            else:
                result = {"success": False, "error": f"Unknown browser action '{action}'"}

        elif executor_type == "system":
            if action == "extract_archive":
                result = self.extract_archive(
                    archive_path=params.get("archive_path", ""),
                    extract_to=params.get("extract_to")
                )
            elif action == "verify_file":
                result = AutomationVerifier.verify_file_exists(
                    file_path=params.get("path", ""),
                    min_size=params.get("min_size", 1)
                )
                result["success"] = result.get("verified", False)
            elif action == "verify_folder":
                result = AutomationVerifier.verify_folder_exists(folder_path=params.get("path", ""))
                result["success"] = result.get("verified", False)
            elif action == "verify_window":
                result = AutomationVerifier.verify_window_exists(title_substring=params.get("title", ""))
                result["success"] = result.get("verified", False)
            else:
                result = {"success": False, "error": f"Unknown system action '{action}'"}

        # Store output for dependency resolution in subsequent steps
        self.step_outputs[step_id] = result
        return result

    def close(self):
        """Cleans up browser context."""
        try:
            self.browser.close()
        except Exception:
            pass
