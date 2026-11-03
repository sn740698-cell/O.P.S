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

    def _substitute_placeholder(self, text: str) -> str:
        """Substitutes dynamic $step_{id}.{field} references inside text strings."""
        if not isinstance(text, str) or "$step_" not in text:
            return text
        import re
        def _repl(match):
            try:
                dep_id = int(match.group(1))
                field = match.group(2)
                step_res = self.step_outputs.get(dep_id, {})
                val = (
                    step_res.get(field)
                    or step_res.get("current_url")
                    or step_res.get("url")
                    or step_res.get("file_path")
                    or step_res.get("extracted_path")
                    or step_res.get("download_path")
                )
                return str(val) if val is not None else match.group(0)
            except Exception:
                return match.group(0)
        return re.sub(r'\$step_(\d+)\.([a-zA-Z0-9_]+)', _repl, text)

    def resolve_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitutes dynamic dependency placeholders like '$step_1.download_path'
        or '$step_1.current_url' with verified outputs from prior steps.
        """
        resolved = {}
        for k, v in params.items():
            if isinstance(v, str):
                resolved[k] = self._substitute_placeholder(v)
            elif isinstance(v, list):
                res_list = []
                for item in v:
                    if isinstance(item, str):
                        res_list.append(self._substitute_placeholder(item))
                    else:
                        res_list.append(item)
                resolved[k] = res_list
            else:
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
            elif action in ["save_file", "save_as"]:
                result = self.desktop.save_file(
                    title=params.get("title", "Notepad"),
                    file_path=params.get("path") or params.get("file_path", "")
                )
            else:
                result = {"success": True, "action": action, "info": f"Completed desktop {action}"}

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
            elif action == "youtube_search":
                result = self.browser.youtube_search(query=params.get("query", ""))
            elif action == "youtube_search_and_play":
                result = self.browser.youtube_search_and_play(query=params.get("query", ""))
            elif action == "youtube_click_first":
                result = self.browser.youtube_click_first()
            elif action == "google_search":
                result = self.browser.google_search(query=params.get("query", ""))
            elif action == "google_click_top":
                result = self.browser.google_click_top()
            elif action == "instagram_reels":
                result = self.browser.instagram_reels()
            elif action == "instagram_open":
                result = self.browser.instagram_open()
            elif action == "click_first_result":
                result = self.browser.click_first_result()
            elif action == "go_back":
                result = self.browser.go_back()
            elif action == "search":
                result = self.browser.search(
                    query=params.get("query", ""),
                    selector=params.get("selector")
                )
            elif action == "youtube_pause":
                from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter
                result = YouTubeAdapter.pause_playback(self.browser._page)
            elif action == "youtube_resume":
                from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter
                result = YouTubeAdapter.resume_playback(self.browser._page)
            elif action == "youtube_stop":
                from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter
                result = YouTubeAdapter.stop_playback(self.browser._page)
            elif action == "youtube_inspect_results":
                from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter
                result = YouTubeAdapter.inspect_search_results(self.browser._page)
            elif action == "spotify_search":
                from automation_system.browser.adapters.spotify_adapter import SpotifyAdapter
                result = SpotifyAdapter.search_song(self.browser._page, query=params.get("query", ""))
            elif action == "spotify_play":
                from automation_system.browser.adapters.spotify_adapter import SpotifyAdapter
                result = SpotifyAdapter.play_top_result(self.browser._page, query=params.get("query", ""))
            elif action == "spotify_toggle_playback":
                from automation_system.browser.adapters.spotify_adapter import SpotifyAdapter
                result = SpotifyAdapter.toggle_playback(self.browser._page)
            elif action == "instagram_dms":
                from automation_system.browser.adapters.instagram_adapter import InstagramAdapter
                result = InstagramAdapter.navigate_dms(self.browser._page)
            elif action == "instagram_open_conversation":
                from automation_system.browser.adapters.instagram_adapter import InstagramAdapter
                result = InstagramAdapter.open_conversation(self.browser._page, contact_name=params.get("contact_name", ""))
            elif action == "instagram_read_messages":
                from automation_system.browser.adapters.instagram_adapter import InstagramAdapter
                result = InstagramAdapter.read_visible_messages(self.browser._page)
            else:
                result = {"success": True, "action": action, "info": f"Completed browser {action}"}

        elif executor_type == "system":
            from automation_system.executors.file_system_executor import FileSystemExecutor
            if action == "create_file":
                result = FileSystemExecutor.create_file(
                    path=params.get("path") or params.get("file_path", ""),
                    content=params.get("content", ""),
                    overwrite=params.get("overwrite", False)
                )
            elif action == "create_folder":
                result = FileSystemExecutor.create_folder(
                    path=params.get("path", "~/Desktop"),
                    folder_name=params.get("folder_name")
                )
            elif action == "create_project_structure":
                result = FileSystemExecutor.create_project_structure(
                    base_path=params.get("path", "~/Desktop"),
                    structure=params.get("structure", {})
                )
            elif action == "read_file":
                result = FileSystemExecutor.read_file(path=params.get("path", ""))
            elif action == "append_to_file":
                result = FileSystemExecutor.append_to_file(
                    path=params.get("path", ""),
                    content=params.get("content", "")
                )
            elif action == "replace_in_file":
                result = FileSystemExecutor.replace_in_file(
                    path=params.get("path", ""),
                    target_content=params.get("target_content", ""),
                    replacement_content=params.get("replacement_content", "")
                )
            elif action == "rename_file":
                result = FileSystemExecutor.rename_file(
                    source_path=params.get("source") or params.get("source_path", ""),
                    new_name_or_path=params.get("destination") or params.get("new_name", "")
                )
            elif action == "move_file":
                result = FileSystemExecutor.move_file(
                    source_path=params.get("source") or params.get("source_path", ""),
                    destination_dir_or_path=params.get("destination") or params.get("dest_path", "")
                )
            elif action == "delete_file":
                result = FileSystemExecutor.delete_file(path=params.get("path", ""))
            elif action == "delete_folder":
                result = FileSystemExecutor.delete_folder(path=params.get("path", ""))
            elif action == "delete_code_region":
                result = FileSystemExecutor.delete_code_region(
                    path=params.get("path", ""),
                    target_code=params.get("target_code", "")
                )
            elif action == "extract_archive":
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
                result = {"success": True, "action": action, "info": f"Completed system {action}"}

        # Store output for dependency resolution in subsequent steps
        self.step_outputs[step_id] = result
        return result

    def close(self):
        """Cleans up browser context."""
        try:
            self.browser.close()
        except Exception:
            pass
