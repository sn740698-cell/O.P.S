"""
O.P.S. Tool Sandbox & Execution Protocol (MCP Layer)
Provides safe, gatekept execution wrappers for:
- Terminal Commands (with live WebSocket streaming and timeout control)
- File System (Safe Read/Write)
- Web Scraping & URL Intelligence
- Local Vector RAG Search
- OS Desktop GUI Automation
"""

import os
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from django.utils import timezone
from channels.db import database_sync_to_async
from ops_core.safety import OPSSafetyGatekeeper
from ops_core.services.event_bus import OPSEventBus
from ops_core.services.rag_service import OPSRAGService
from ops_core.services.scraping_service import OPSScrapingService
from ops_core.services.automation_service import OPSAutomationService

logger = logging.getLogger("ops.tool_sandbox")


class OPSToolSandbox:
    def __init__(self):
        self.rag_service = OPSRAGService()
        self.scraping_service = OPSScrapingService()
        self.automation_service = OPSAutomationService()

    async def execute_terminal_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        task_id: Optional[str] = None,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Executes a shell command with safety validation, live WebSocket stdout streaming,
        and database audit logging.
        """
        start_time = time.time()
        agent_name = "DeveloperAgent"

        # 1. Safety Gatekeeper Check
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name=agent_name,
            action="run_terminal_cmd",
            params={"command": command, "cwd": cwd},
            reason_explanation=f"Execute terminal command: {command[:60]}",
            task_id=task_id,
            timeout_seconds=timeout_seconds
        )

        if not auth_res.get("approved"):
            logger.warning(f"Terminal execution denied/blocked for: {command}")
            return {
                "status": "BLOCKED",
                "command": command,
                "stdout": "",
                "stderr": auth_res.get("reason", "Command rejected by safety gatekeeper."),
                "exit_code": -1,
                "duration_ms": int((time.time() - start_time) * 1000)
            }

        # 2. Execute process with live stdout streaming
        await OPSEventBus.emit_terminal_log_async(f"$ {command}", stream="stdout")
        
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                errors="replace"
            )

            stdout_lines = []
            stderr_lines = []

            for line in process.stdout:
                stdout_lines.append(line)
                await OPSEventBus.emit_terminal_log_async(line.rstrip(), stream="stdout")

            for line in process.stderr:
                stderr_lines.append(line)
                await OPSEventBus.emit_terminal_log_async(line.rstrip(), stream="stderr")

            process.wait(timeout=timeout_seconds)
            exit_code = process.returncode
            duration_ms = int((time.time() - start_time) * 1000)
            stdout_text = "".join(stdout_lines)
            stderr_text = "".join(stderr_lines)

            # Record in Execution Audit Log
            try:
                await database_sync_to_async(OPSSafetyGatekeeper._create_audit_record)(
                    agent_name=agent_name,
                    action_type="run_terminal_cmd",
                    target=command,
                    parameters={"cwd": cwd},
                    status="SUCCESS" if exit_code == 0 else "FAILED",
                    stdout=stdout_text,
                    stderr=stderr_text,
                    duration_ms=duration_ms,
                    task_id=task_id
                )
            except Exception as audit_err:
                logger.warning(f"Audit log recording error: {audit_err}")

            return {
                "status": "SUCCESS" if exit_code == 0 else "FAILED",
                "command": command,
                "exit_code": exit_code,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "duration_ms": duration_ms
            }
        except subprocess.TimeoutExpired:
            process.kill()
            duration_ms = int((time.time() - start_time) * 1000)
            msg = f"Command timed out after {timeout_seconds}s"
            await OPSEventBus.emit_terminal_log_async(f"[ERROR] {msg}", stream="stderr")
            try:
                await database_sync_to_async(OPSSafetyGatekeeper._create_audit_record)(
                    agent_name=agent_name,
                    action_type="run_terminal_cmd",
                    target=command,
                    status="TIMEOUT",
                    stderr=msg,
                    duration_ms=duration_ms,
                    task_id=task_id
                )
            except Exception:
                pass
            return {
                "status": "TIMEOUT",
                "command": command,
                "exit_code": -1,
                "stdout": "",
                "stderr": msg,
                "duration_ms": duration_ms
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            msg = f"Execution error: {str(e)}"
            await OPSEventBus.emit_terminal_log_async(f"[ERROR] {msg}", stream="stderr")
            return {
                "status": "ERROR",
                "command": command,
                "exit_code": -1,
                "stdout": "",
                "stderr": msg,
                "duration_ms": duration_ms
            }

    async def read_file(
        self, 
        file_path: str, 
        start_line: Optional[int] = None, 
        end_line: Optional[int] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Safely reads file content with optional line slicing."""
        path = Path(file_path).resolve()
        if not path.is_file():
            return {"status": "ERROR", "message": f"File not found: {file_path}"}

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            total_lines = len(lines)
            s_idx = max(0, (start_line - 1)) if start_line else 0
            e_idx = min(total_lines, end_line) if end_line else total_lines

            content = "".join(lines[s_idx:e_idx])
            return {
                "status": "SUCCESS",
                "file_path": str(path),
                "total_lines": total_lines,
                "start_line": s_idx + 1,
                "end_line": e_idx,
                "content": content
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    async def write_file(
        self,
        file_path: str,
        content: str,
        overwrite: bool = True,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Safely writes or creates a file under gatekeeper policy."""
        path = Path(file_path).resolve()

        # Gatekeeper check
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="DeveloperAgent",
            action="edit_file",
            params={"file_path": str(path), "overwrite": overwrite},
            reason_explanation=f"Write file: {path.name}",
            task_id=task_id
        )

        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason")}

        try:
            os.makedirs(path.parent, exist_ok=True)
            mode = "w" if overwrite else "a"
            with open(path, mode, encoding="utf-8") as f:
                f.write(content)

            try:
                await database_sync_to_async(OPSSafetyGatekeeper._create_audit_record)(
                    agent_name="DeveloperAgent",
                    action_type="edit_file",
                    target=str(path),
                    status="SUCCESS",
                    task_id=task_id
                )
            except Exception:
                pass
            return {
                "status": "SUCCESS",
                "file_path": str(path),
                "bytes_written": len(content.encode("utf-8"))
            }
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    async def web_scrape(self, url: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Scrapes web content and extracts clean markdown/text."""
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="BrowserAgent",
            action="web_scrape",
            params={"url": url},
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason")}

        result = self.scraping_service.scrape_url(url)
        return result

    def rag_search(self, query: str, collection: str = "ops_codebase", n_results: int = 3) -> List[Dict[str, Any]]:
        """Searches local ChromaDB vector store."""
        return self.rag_service.query(query_text=query, collection_name=collection, n_results=n_results)

    async def search_web(self, query: str, max_results: int = 5, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Performs live web search and extracts search results."""
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="BrowserAgent",
            action="web_search",
            params={"query": query},
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason")}

        await OPSEventBus.emit_terminal_log_async(f"[OPS-SEARCH] Querying web: '{query}'", stream="stdout")
        return self.scraping_service.search_web(query, max_results=max_results)

    async def auto_research_web(self, query: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes autonomous background live web crawling across Person Bios, Concepts,
        Theories, or Real-time News without opening external desktop browser windows.
        """
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="WebCrawlingAgent",
            action="crawl_research",
            params={"query": query},
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason")}

        await OPSEventBus.emit_terminal_log_async(f"[OPS-CRAWLER] Initiating autonomous deep crawl for: '{query}'", stream="stdout")
        return self.scraping_service.auto_research(directive=query)

    async def launch_application(self, app_name: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Launches desktop application on workstation."""
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="SystemAutomationAgent",
            action="launch_app",
            params={"app": app_name},
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason")}

        await OPSEventBus.emit_terminal_log_async(f"[OPS-AUTO] Launching app: {app_name}", stream="stdout")
        return self.automation_service.launch_app(app_name)

    async def open_browser_search(self, query: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Opens live browser to Google search with safety approval."""
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="BrowserAgent",
            action="open_browser_search",
            params={"query": query},
            reason_explanation=f"Permission required to open browser search: '{query}'",
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason", "Action blocked or denied.")}

        await OPSEventBus.emit_terminal_log_async(f"[OPS-BROWSER] Opening browser search: '{query}'", stream="stdout")
        return self.automation_service.open_web_search(query)

    async def open_file_or_folder(self, target: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Opens any file, directory, or standard folder with safety approval."""
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="SystemAutomationAgent",
            action="open_file_or_folder",
            params={"target": target},
            reason_explanation=f"Permission required to open file or folder: '{target}'",
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason", "Action blocked or denied.")}

        await OPSEventBus.emit_terminal_log_async(f"[OPS-FS] Opening file or folder: {target}", stream="stdout")
        return self.automation_service.open_file_or_folder(target)

    async def open_in_vscode(self, target: str = "", task_id: Optional[str] = None) -> Dict[str, Any]:
        """Opens file or workspace in VS Code with safety approval."""
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="DeveloperAgent",
            action="open_in_vscode",
            params={"target": target or "workspace"},
            reason_explanation=f"Permission required to open in VS Code: '{target or 'workspace'}'",
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason", "Action blocked or denied.")}

        await OPSEventBus.emit_terminal_log_async(f"[OPS-DEV] Opening in VS Code: {target or 'workspace'}", stream="stdout")
        return self.automation_service.open_in_vscode(target)

    async def run_claude_routine(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Executes Claude workflow (cd D:\\freellmapi && npm run dev, then launch Claude) with safety approval."""
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="DeveloperAgent",
            action="run_claude_routine",
            params={"directory": r"D:\freellmapi", "workflow": "cd D:\\freellmapi -> npm run dev -> launch Claude"},
            reason_explanation="Permission required to execute Claude workflow (cd D:\\freellmapi -> npm run dev -> launch Claude)",
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason", "Action blocked or denied.")}

        await OPSEventBus.emit_terminal_log_async(r"[OPS-AUTO] Executing Claude routine in D:\freellmapi...", stream="stdout")
        return self.automation_service.run_claude_routine()

    async def execute_browser_dom_task(
        self,
        url: str,
        search_query: Optional[str] = None,
        site_name: str = "",
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes DOM automation with Playwright/Chrome and captures preview."""
        auth_res = await OPSSafetyGatekeeper.validate_and_authorize_async(
            agent_name="BrowserAgent",
            action="browser_dom_task",
            params={"url": url, "query": search_query or "", "site": site_name or url},
            reason_explanation=f"Permission required for browser DOM task on {site_name or url} ('{search_query or 'Navigate'}')",
            task_id=task_id
        )
        if not auth_res.get("approved"):
            return {"status": "BLOCKED", "reason": auth_res.get("reason", "Action blocked or denied.")}

        await OPSEventBus.emit_terminal_log_async(f"[OPS-DOM] Executing browser DOM task on {site_name or url} ('{search_query}')", stream="stdout")
        return self.automation_service.execute_browser_dom_task(url=url, search_query=search_query, site_name=site_name)

    async def execute_gui_action(self, action: str, x: int = 0, y: int = 0, text: str = "", task_id: Optional[str] = None) -> Dict[str, Any]:
        """Executes OS desktop GUI action."""
        await OPSEventBus.emit_terminal_log_async(f"[OPS-GUI] Action: {action} ({text})", stream="stdout")
        return self.automation_service.execute_gui_action(action, x=x, y=y, text=text)


