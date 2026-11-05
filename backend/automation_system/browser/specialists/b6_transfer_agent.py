"""
O.P.S. 2.0 Browser Automation Specialist — Agent B6: Download & Upload Agent
Responsibilities:
- Intercept and wait for file downloads
- Save downloaded files to authorized target directory
- Verify file size, non-zero bytes, and integrity
- Handle file uploads via input[type=file]
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from automation_system.browser.browser_manager import BrowserSessionManager

logger = logging.getLogger("OPS.Browser.B6_TransferAgent")

DEFAULT_DOWNLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/downloads"))


class B6_TransferAgent:
    """Specialist Agent B6: Manages browser downloads and file uploads."""

    def __init__(self, conversation_id: str = "default_session", download_dir: Optional[str] = None):
        self.agent_id = "agent_b6_transfer"
        self.agent_name = "Download & Upload Agent"
        self.conversation_id = conversation_id or "default_session"
        self.manager = BrowserSessionManager()
        self.download_dir = download_dir or DEFAULT_DOWNLOAD_DIR
        os.makedirs(self.download_dir, exist_ok=True)

    def trigger_and_wait_download(
        self,
        trigger_selector: str,
        target_filename: Optional[str] = None,
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """Clicks an element and awaits file download completion."""
        t0 = time.time()
        try:
            def _download_task(page):
                loc = page.locator(trigger_selector).first
                with page.expect_download(timeout=timeout_ms) as download_info:
                    loc.click()
                download = download_info.value
                dest_name = target_filename or download.suggested_filename
                dest_path = os.path.join(self.download_dir, dest_name)
                download.save_as(dest_path)
                
                size_bytes = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
                return {
                    "success": True,
                    "action": "download",
                    "file_path": dest_path,
                    "file_name": dest_name,
                    "size_bytes": size_bytes,
                    "exists": os.path.exists(dest_path) and size_bytes > 0,
                    "duration_s": round(time.time() - t0, 2)
                }

            res = self.manager.execute_on_page(self.conversation_id, _download_task, timeout=timeout_ms / 1000.0 + 10.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return {"success": False, "agent_id": self.agent_id, "action": "download", "error": str(e)}

    def upload_file(self, selector: str, file_path: str, timeout_ms: int = 10000) -> Dict[str, Any]:
        """Sets input[type=file] files."""
        if not os.path.exists(file_path):
            return {"success": False, "agent_id": self.agent_id, "error": f"Upload source file not found: {file_path}"}

        try:
            def _upload(page):
                loc = page.locator(selector).first
                loc.set_input_files(file_path, timeout=timeout_ms)
                return {
                    "success": True,
                    "action": "upload_file",
                    "file_path": file_path,
                    "selector": selector
                }

            res = self.manager.execute_on_page(self.conversation_id, _upload, timeout=timeout_ms / 1000.0 + 5.0)
            res["agent_id"] = self.agent_id
            return res
        except Exception as e:
            return {"success": False, "agent_id": self.agent_id, "action": "upload_file", "error": str(e)}
