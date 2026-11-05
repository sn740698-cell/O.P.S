"""
O.P.S. 2.0 Hybrid Automation Coordinator
Orchestrates complex cross-domain automation workflows combining Browser and Desktop operations:
- DAG-based task decomposition and dependency resolution
- Parallel execution of independent subtasks via ThreadPoolExecutor
- Sequential execution of dependent subtasks with state handoff
- Resource locking and file ownership protection against race conditions
- Real-time event telemetry integration with Cockpit Agent Preview
"""

import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Set

from research_system.events.event_bus import event_bus
from automation_system.browser.specialists.browser_superior_agent import BrowserSuperiorAgent
from automation_system.desktop.specialists.desktop_superior_agent import DesktopSuperiorAgent

logger = logging.getLogger("OPS.Automation.HybridCoordinator")


class ResourceLockManager:
    """Thread-safe resource and file locking manager to prevent concurrency hazards."""

    def __init__(self):
        self._lock = threading.Lock()
        self._locked_resources: Set[str] = set()

    def acquire_lock(self, resource_id: str) -> bool:
        norm = resource_id.lower().strip()
        with self._lock:
            if norm in self._locked_resources:
                return False
            self._locked_resources.add(norm)
            return True

    def release_lock(self, resource_id: str):
        norm = resource_id.lower().strip()
        with self._lock:
            self._locked_resources.discard(norm)

    def is_locked(self, resource_id: str) -> bool:
        norm = resource_id.lower().strip()
        with self._lock:
            return norm in self._locked_resources


class HybridAutomationCoordinator:
    """
    Coordinates multi-step, multi-domain automations between
    BrowserSuperiorAgent and DesktopSuperiorAgent.
    """

    def __init__(self, conversation_id: str = "default_session", request_id: Optional[str] = None):
        self.coordinator_id = "hybrid_coordinator"
        self.coordinator_name = "Hybrid Automation Coordinator"
        self.conversation_id = conversation_id or "default_session"
        self.request_id = request_id or f"req_hybrid_{int(time.time())}"

        self.browser_superior = BrowserSuperiorAgent(self.conversation_id, self.request_id)
        self.desktop_superior = DesktopSuperiorAgent(self.request_id, self.conversation_id)
        self.lock_mgr = ResourceLockManager()

    def _emit_event(self, component: str, event_type: str, status: str, summary: str, extra: Optional[Dict] = None):
        """Streams coordinator progress events to Cockpit Agent Preview."""
        try:
            extra_data = extra or {}
            event_bus.publish(
                request_id=self.request_id,
                execution_id=f"exec_{int(time.time() * 1000)}",
                conversation_id=self.conversation_id,
                node_id="hybrid_coordinator",
                component_name=component,
                component_type="COORDINATOR",
                event_type=event_type,
                execution_status=status,
                safe_task_summary=summary,
                coordinator="HybridAutomationCoordinator",
                **extra_data
            )
        except Exception as e:
            logger.debug(f"Coordinator event failed: {e}")

    def execute_plan(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes a plan of subtasks resolving dependencies (DAG).
        Each subtask:
        {
            "id": "task_1",
            "domain": "BROWSER" | "DESKTOP",
            "action": str,
            "target": str,
            "value": str,
            "dependencies": ["task_0"],
            "resource_lock": "path/or/app"
        }
        """
        t0 = time.time()
        logger.info(f"Hybrid Coordinator initiating execution of {len(subtasks)} subtasks")

        self._emit_event(
            "HybridCoordinator",
            "coordinator.started",
            "RUNNING",
            f"Scheduling {len(subtasks)} hybrid subtasks across Browser and Desktop",
            {"total_subtasks": len(subtasks)}
        )

        completed_tasks: Dict[str, Dict[str, Any]] = {}
        pending_tasks = {t["id"]: t for t in subtasks}

        while pending_tasks:
            # Find tasks whose dependencies are satisfied
            ready_to_run = []
            for tid, tspec in list(pending_tasks.items()):
                deps = tspec.get("dependencies", [])
                if all(dep in completed_tasks and completed_tasks[dep].get("success") for dep in deps):
                    ready_to_run.append(tspec)

            if not ready_to_run:
                # Cycle or failed dependency
                unmet = {tid: tspec.get("dependencies") for tid, tspec in pending_tasks.items()}
                logger.error(f"Deadlock or unmet dependencies: {unmet}")
                self._emit_event(
                    "HybridCoordinator",
                    "coordinator.failed",
                    "FAILED",
                    f"Subtask dependency deadlock on tasks: {list(unmet.keys())}"
                )
                return {
                    "success": False,
                    "completed_subtasks": completed_tasks,
                    "failed_subtasks": list(unmet.keys()),
                    "error": "Unmet dependencies or cycle detected in subtask DAG"
                }

            # If multiple tasks are ready and do not share resource locks, run in parallel!
            # Filter non-conflicting tasks
            batch_to_run = []
            active_batch_locks = set()
            for t in ready_to_run:
                lock_res = t.get("resource_lock")
                if lock_res:
                    if lock_res in active_batch_locks or self.lock_mgr.is_locked(lock_res):
                        continue
                    active_batch_locks.add(lock_res)
                batch_to_run.append(t)

            if not batch_to_run:
                batch_to_run = [ready_to_run[0]]

            # Execute batch (parallel if > 1, sequential if 1)
            if len(batch_to_run) > 1:
                self._emit_event(
                    "HybridCoordinator",
                    "coordinator.parallel_dispatch",
                    "RUNNING",
                    f"Executing {len(batch_to_run)} independent subtasks in parallel: {[t['id'] for t in batch_to_run]}"
                )
                with ThreadPoolExecutor(max_workers=len(batch_to_run)) as executor:
                    future_to_task = {
                        executor.submit(self._run_subtask_with_handoff, t, completed_tasks): t["id"]
                        for t in batch_to_run
                    }
                    for future in as_completed(future_to_task):
                        tid = future_to_task[future]
                        res = future.result()
                        completed_tasks[tid] = res
                        del pending_tasks[tid]
            else:
                single_t = batch_to_run[0]
                tid = single_t["id"]
                res = self._run_subtask_with_handoff(single_t, completed_tasks)
                completed_tasks[tid] = res
                del pending_tasks[tid]

        all_ok = all((r.get("success", False) or r.get("verified", False)) for r in completed_tasks.values())
        duration = round(time.time() - t0, 2)
        status_str = "COMPLETED" if all_ok else "FAILED"

        self._emit_event(
            "HybridCoordinator",
            "coordinator.completed",
            status_str,
            f"Hybrid plan execution finished with status {status_str} in {duration}s",
            {"completed_count": len(completed_tasks), "duration_s": duration}
        )

        return {
            "success": all_ok,
            "duration_s": duration,
            "total_subtasks": len(subtasks),
            "completed_subtasks": completed_tasks
        }

    def _run_subtask_with_handoff(self, subtask: Dict[str, Any], completed_tasks: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an individual subtask, resolving variable handoffs and locks."""
        tid = subtask["id"]
        domain = subtask.get("domain", "").upper()
        lock_res = subtask.get("resource_lock")

        if lock_res:
            self.lock_mgr.acquire_lock(lock_res)

        try:
            # Resolve variable references from previous task outputs (e.g. "$task_0.file_path")
            resolved_step = dict(subtask)
            for k in ["target", "value"]:
                val = resolved_step.get(k)
                if isinstance(val, str) and val.startswith("$"):
                    parts = val[1:].split(".")
                    ref_tid = parts[0]
                    ref_key = parts[1] if len(parts) > 1 else "output"
                    if ref_tid in completed_tasks:
                        handoff_val = completed_tasks[ref_tid].get(ref_key) or completed_tasks[ref_tid].get("file_path")
                        if handoff_val:
                            resolved_step[k] = str(handoff_val)

            self._emit_event(
                f"Superior_{domain.capitalize()}",
                "agent.handoff",
                "RUNNING",
                f"Delegating subtask {tid} to {domain} Superior Agent: {resolved_step.get('action')}"
            )

            if domain == "BROWSER":
                res = self.browser_superior.execute_step(resolved_step)
            elif domain == "DESKTOP":
                res = self.desktop_superior.execute_step(resolved_step)
            else:
                res = {"success": False, "error": f"Unknown subtask domain: {domain}"}

            res["subtask_id"] = tid
            res["domain"] = domain
            return res

        finally:
            if lock_res:
                self.lock_mgr.release_lock(lock_res)
