"""
O.P.S. 2.0 Browser Automation — Superior Agent
Hierarchical supervisor coordinating 8 specialist browser agents:
- B1: Lifecycle Agent (instance, context, health)
- B2: Tab Management Agent (tabs, contexts)
- B3: Navigation Agent (URLs, history, load states)
- B4: Web Interaction Agent (clicks, scrolling, keys)
- B5: Form & Data Entry Agent (inputs, passwords, validation)
- B6: Download & Upload Agent (file transfers, verification)
- B7: Browser Verification Agent (DOM & playback assertion)
- B8: Browser Recovery Agent (bounded error recovery)
"""

import time
import logging
from typing import Dict, Any, List, Optional

from research_system.events.event_bus import event_bus
from automation_system.browser.specialists.b1_lifecycle_agent import B1_LifecycleAgent
from automation_system.browser.specialists.b2_tab_agent import B2_TabAgent
from automation_system.browser.specialists.b3_navigation_agent import B3_NavigationAgent
from automation_system.browser.specialists.b4_interaction_agent import B4_InteractionAgent
from automation_system.browser.specialists.b5_form_agent import B5_FormAgent
from automation_system.browser.specialists.b6_transfer_agent import B6_TransferAgent
from automation_system.browser.specialists.b7_verification_agent import B7_VerificationAgent
from automation_system.browser.specialists.b8_recovery_agent import B8_RecoveryAgent
from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter

logger = logging.getLogger("OPS.Browser.SuperiorAgent")


class BrowserSuperiorAgent:
    """
    Browser Superior Agent: Orchestrates specialist sub-agents (B1-B8)
    to fulfill browser directives with real-time telemetry and verification.
    """

    def __init__(self, conversation_id: str = "default_session", request_id: Optional[str] = None):
        self.agent_id = "superior_browser_agent"
        self.agent_name = "Browser Automation Superior Agent"
        self.conversation_id = conversation_id or "default_session"
        self.request_id = request_id or f"req_browser_{int(time.time())}"

        # Initialize the 8 Specialist Agents
        self.b1_lifecycle = B1_LifecycleAgent(self.conversation_id)
        self.b2_tab = B2_TabAgent(self.conversation_id)
        self.b3_nav = B3_NavigationAgent(self.conversation_id)
        self.b4_interact = B4_InteractionAgent(self.conversation_id)
        self.b5_form = B5_FormAgent(self.conversation_id)
        self.b6_transfer = B6_TransferAgent(self.conversation_id)
        self.b7_verify = B7_VerificationAgent(self.conversation_id)
        self.b8_recovery = B8_RecoveryAgent(self.conversation_id)

    def _emit_event(self, specialist_name: str, event_type: str, status: str, summary: str, extra: Optional[Dict] = None):
        """Emits structured real-time telemetry to O.P.S. EventBus for Cockpit Agent Preview."""
        try:
            extra_data = extra or {}
            event_bus.publish(
                request_id=self.request_id,
                execution_id=f"exec_{int(time.time() * 1000)}",
                conversation_id=self.conversation_id,
                node_id="browser_superior_agent",
                component_name=specialist_name,
                component_type="SPECIALIST_AGENT",
                event_type=event_type,
                execution_status=status,
                safe_task_summary=summary,
                superior_agent="BrowserSuperiorAgent",
                specialist_agent=specialist_name,
                **extra_data
            )
        except Exception as e:
            logger.debug(f"Failed to publish event: {e}")

    def execute_directive(self, directive: str, steps: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Executes a high-level browser directive by breaking down tasks, delegating to specialists,
        and validating results.
        """
        t0 = time.time()
        logger.info(f"BrowserSuperiorAgent received directive: '{directive}'")

        self._emit_event(
            "BrowserSuperiorAgent",
            "agent.started",
            "RUNNING",
            f"Orchestrating browser directive: {directive}",
            {"total_steps": len(steps) if steps else 1}
        )

        # Step 1: Ensure browser lifecycle is healthy via B1
        self._emit_event("B1_LifecycleAgent", "agent.handoff", "RUNNING", "Ensuring Chromium session is active")
        b1_res = self.b1_lifecycle.ensure_browser_ready()
        if not b1_res.get("success"):
            self._emit_event("B8_RecoveryAgent", "agent.handoff", "WARNING", "Restarting crashed browser session")
            b1_res = self.b8_recovery.execute_with_recovery("restart_session", self.b1_lifecycle.restart_session)
            if not b1_res.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to initialize browser session: {b1_res.get('error')}",
                    "stage": "b1_lifecycle"
                }

        executed_steps = []
        directive_lower = directive.lower()

        # Route specialized high-level workflows
        # 1. YouTube workflow
        if "youtube.com" in directive_lower or "youtube" in directive_lower:
            res = self._handle_youtube_directive(directive)
            executed_steps.append(res)
        # 2. General Steps workflow
        elif steps and len(steps) > 0:
            for i, step in enumerate(steps):
                step_res = self.execute_step(step, step_idx=i + 1, total_steps=len(steps))
                executed_steps.append(step_res)
                if not step_res.get("success"):
                    logger.warning(f"Step {i+1} failed: {step_res.get('error')}")
                    break
        # 3. Direct URL / Navigation directive
        elif any(proto in directive_lower for proto in ["http://", "https://", "www.", ".com", ".org", ".net", ".io"]):
            res = self._handle_direct_navigation(directive)
            executed_steps.append(res)
        else:
            # Fallback search directive via B3/B4
            res = self._handle_general_search(directive)
            executed_steps.append(res)

        # Final verification via B7
        self._emit_event("B7_VerificationAgent", "agent.handoff", "RUNNING", "Performing final DOM and state verification")
        final_ok = all(s.get("success", False) for s in executed_steps)

        duration = round(time.time() - t0, 2)
        status_str = "COMPLETED" if final_ok else "FAILED"

        self._emit_event(
            "BrowserSuperiorAgent",
            "agent.completed",
            status_str,
            f"Browser execution {status_str.lower()} in {duration}s",
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
        """Dispatches an individual planned step to the targeted specialist agent."""
        action = step.get("action", "").lower()
        target = step.get("target") or step.get("url") or step.get("selector") or ""
        value = step.get("value") or step.get("text") or ""

        logger.info(f"BrowserSuperiorAgent executing step {step_idx}/{total_steps}: {action} -> {target}")

        if action in ["navigate", "open_url", "goto"]:
            self._emit_event("B3_NavigationAgent", "agent.handoff", "RUNNING", f"Navigating to {target}")
            return self.b3_nav.navigate(target)

        elif action in ["click", "click_element"]:
            self._emit_event("B4_InteractionAgent", "agent.handoff", "RUNNING", f"Clicking element: {target}")
            return self.b4_interact.click(selector=target if target.startswith(("#", ".", "[")) else None, name=target if not target.startswith(("#", ".", "[")) else None)

        elif action in ["click_first_result", "first_result"]:
            self._emit_event("B4_InteractionAgent", "agent.handoff", "RUNNING", "Clicking first search result")
            return self.b4_interact.click_first_result()

        elif action in ["type", "fill", "enter_text"]:
            self._emit_event("B5_FormAgent", "agent.handoff", "RUNNING", f"Entering text into {target}")
            return self.b5_form.fill_field(target, value)

        elif action in ["download"]:
            self._emit_event("B6_TransferAgent", "agent.handoff", "RUNNING", f"Triggering download via {target}")
            return self.b6_transfer.trigger_and_wait_download(target, target_filename=value or None)

        elif action in ["switch_tab"]:
            idx = int(value or 0)
            self._emit_event("B2_TabAgent", "agent.handoff", "RUNNING", f"Switching to tab {idx}")
            return self.b2_tab.switch_tab(idx)

        elif action in ["verify", "assert"]:
            self._emit_event("B7_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying page state: {target}")
            return self.b7_verify.verify_state(url_substring=target)

        else:
            return {"success": False, "error": f"Unknown browser action: '{action}'"}

    def _handle_youtube_directive(self, directive: str) -> Dict[str, Any]:
        """Orchestrates YouTube searches, navigation, and playback."""
        import re
        self._emit_event("B3_NavigationAgent", "agent.handoff", "RUNNING", "Navigating to YouTube")
        
        # Extract query
        q_match = re.search(r"(?:search for|play|find)\s+([^\.]+)", directive, re.IGNORECASE)
        query = q_match.group(1).strip() if q_match else directive

        # Execute on page with adapter
        def _yt_action(page):
            return YouTubeAdapter.search_and_play(page, query=query)

        self._emit_event("B4_InteractionAgent", "agent.handoff", "RUNNING", f"Searching YouTube for '{query}' and playing first hit")
        res = self.b1_lifecycle.manager.execute_on_page(self.conversation_id, _yt_action, timeout=35.0)

        # Verification via B7
        self._emit_event("B7_VerificationAgent", "agent.handoff", "RUNNING", "Verifying YouTube media playback")
        v_res = self.b7_verify.verify_youtube_playing()
        res["verification"] = v_res
        res["success"] = res.get("success", False) and v_res.get("verified", False)
        return res

    def _handle_direct_navigation(self, directive: str) -> Dict[str, Any]:
        """Extracts URL and performs navigation and verification."""
        import re
        url_match = re.search(r"https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(?:com|org|net|io|edu)", directive)
        url = url_match.group(0) if url_match else "https://duckduckgo.com"
        if not url.startswith("http"):
            url = f"https://{url}"

        self._emit_event("B3_NavigationAgent", "agent.handoff", "RUNNING", f"Navigating directly to {url}")
        nav_res = self.b3_nav.navigate(url)

        self._emit_event("B7_VerificationAgent", "agent.handoff", "RUNNING", f"Verifying DOM readiness for {url}")
        v_res = self.b7_verify.verify_state(url_substring=url.split("//")[-1].split("/")[0])
        nav_res["verification"] = v_res
        return nav_res

    def _handle_general_search(self, query: str) -> Dict[str, Any]:
        """Navigates to search engine and submits query."""
        import urllib.parse
        target_url = f"https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}"
        self._emit_event("B3_NavigationAgent", "agent.handoff", "RUNNING", f"Searching DuckDuckGo for: {query}")
        nav_res = self.b3_nav.navigate(target_url)
        v_res = self.b7_verify.verify_state(url_substring="duckduckgo.com")
        nav_res["verification"] = v_res
        return nav_res
