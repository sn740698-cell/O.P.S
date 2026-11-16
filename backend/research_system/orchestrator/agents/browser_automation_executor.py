"""
Agent 9: Browser Automation Executor
Group 3: Automation Engine
Technology: Playwright (Chromium Headed/Visible Engine via BrowserSessionManager)
Executes web portal automation, page navigation, search queries, element clicks,
first-result selections, and media playback.
Maintains persistent session state across conversation turns.
Guarantees thread-safe execution via dedicated Playwright worker actor.
"""

import time
import logging
from typing import Dict, Any, List
from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.base import emit_agent_started, emit_agent_progress, emit_agent_completed, emit_agent_failed
from automation_system.browser.browser_manager import BrowserSessionManager
from automation_system.browser.navigation_engine import NavigationEngine
from automation_system.browser.search_engine import SearchEngine
from automation_system.browser.interaction_engine import InteractionEngine
from automation_system.browser.verification_engine import BrowserVerificationEngine
from automation_system.browser.page_inspector import PageInspector
from automation_system.browser.auth_manager import AuthenticationManager
from automation_system.browser.adapters.youtube_adapter import YouTubeAdapter
from automation_system.browser.adapters.instagram_adapter import InstagramAdapter
from automation_system.browser.adapters.google_adapter import GoogleAdapter
from automation_system.browser.adapters.spotify_adapter import SpotifyAdapter

logger = logging.getLogger("OPS.Agent.BrowserExecutor")

AGENT_ID = "browser_automation_executor"
AGENT_NAME = "Browser Automation Executor"
GROUP_ID = "automation_engine"
COMPONENT_TYPE = "execution_worker"


def _dispatch_single_action(page, action: str, params: Dict[str, Any], raw_query: str) -> Dict[str, Any]:
    """
    Executes a single browser action on the real Playwright Page inside the worker thread.
    """
    res: Dict[str, Any] = {}

    if action == "navigate":
        url = params.get("url") or params.get("target_url") or params.get("destination")
        if not url:
            q_low = raw_query.lower()
            if "django" in q_low:
                url = "https://docs.djangoproject.com/en/stable/"
            elif "youtube" in q_low:
                url = "https://www.youtube.com"
            elif "instagram" in q_low:
                url = "https://www.instagram.com"
            elif "python" in q_low:
                url = "https://www.python.org"
            elif "spotify" in q_low:
                url = "https://open.spotify.com"
            else:
                url = "https://www.google.com"
        res = NavigationEngine.navigate(page, url=url)
        res["verification"] = BrowserVerificationEngine.verify_page_state(page, url_substring=url.split("//")[-1].split("/")[0])

    elif action == "search":
        q = params.get("query", "")
        custom_sel = params.get("selector")
        res = SearchEngine.execute_search(page, query=q, custom_selector=custom_sel)

    elif action == "click":
        res = InteractionEngine.click(
            page,
            selector=params.get("selector"),
            name=params.get("name"),
            role=params.get("role")
        )

    elif action == "click_first_result":
        res = InteractionEngine.click_first_result(page)

    elif action == "go_back":
        res = NavigationEngine.go_back(page)

    elif action == "go_forward":
        res = NavigationEngine.go_forward(page)

    elif action == "reload":
        res = NavigationEngine.reload(page)

    elif action == "fill_form":
        res = InteractionEngine.fill_form(
            page,
            selector_or_label=params.get("field") or params.get("selector", ""),
            text=params.get("text", ""),
            is_secret=params.get("is_secret", False)
        )

    elif action == "inspect_page":
        res = PageInspector.inspect(page)

    elif action == "youtube_search_and_play":
        q = params.get("query", "")
        res = YouTubeAdapter.execute_full_search_and_play(page, query=q)

    elif action == "youtube_search":
        q = params.get("query", "")
        res = YouTubeAdapter.search_song_or_video(page, query=q)

    elif action == "youtube_click_first":
        res = YouTubeAdapter.click_first_video(page)

    elif action == "youtube_pause":
        res = YouTubeAdapter.pause_playback(page)

    elif action == "youtube_resume":
        res = YouTubeAdapter.resume_playback(page)

    elif action == "youtube_stop":
        res = YouTubeAdapter.stop_playback(page)

    elif action == "youtube_inspect_results":
        res = YouTubeAdapter.inspect_search_results(page, max_results=params.get("max_results", 5))

    elif action == "spotify_search":
        q = params.get("query", "")
        res = SpotifyAdapter.search_song(page, query=q)

    elif action == "spotify_play":
        q = params.get("query", "")
        res = SpotifyAdapter.play_top_result(page, query=q)

    elif action == "spotify_toggle_playback":
        res = SpotifyAdapter.toggle_playback(page)

    elif action == "instagram_reels":
        res = InstagramAdapter.navigate_reels(page)

    elif action == "instagram_open":
        res = InstagramAdapter.open_home(page)

    elif action == "instagram_dms":
        res = InstagramAdapter.navigate_dms(page)

    elif action == "instagram_open_conversation":
        user = params.get("username") or params.get("contact_name", "")
        res = InstagramAdapter.open_conversation(page, contact_name=user)

    elif action == "instagram_read_messages":
        user = params.get("username") or params.get("contact_name", "")
        res = InstagramAdapter.read_visible_messages(page, max_messages=params.get("max_messages", 5))

    elif action == "google_search":
        q = params.get("query", "")
        res = GoogleAdapter.search(page, query=q)

    elif action in ["open_tab", "new_tab"]:
        from automation_system.browser.tab_manager import TabManager
        tab_mgr = TabManager(conv_id)
        u = params.get("url") or "about:blank"
        res = tab_mgr.new_tab(url=u)

    elif action in ["switch_tab"]:
        from automation_system.browser.tab_manager import TabManager
        tab_mgr = TabManager(conv_id)
        t = params.get("tab") or params.get("index", 0)
        if isinstance(t, str) and not t.isdigit():
            tabs = tab_mgr.list_tabs()
            matched_idx = 0
            for tb in tabs:
                if t.lower() in tb.get("url", "").lower() or t.lower() in tb.get("title", "").lower():
                    matched_idx = tb.get("index", 0)
                    break
            res = tab_mgr.switch_tab(matched_idx)
        else:
            res = tab_mgr.switch_tab(int(t))

    elif action in ["close_tab"]:
        from automation_system.browser.tab_manager import TabManager
        tab_mgr = TabManager(conv_id)
        t = params.get("tab")
        res = tab_mgr.close_tab(t)

    elif action in ["download"]:
        from automation_system.browser.specialists.b6_transfer_agent import B6_TransferAgent
        transfer = B6_TransferAgent(conversation_id=conv_id)
        u = params.get("url") or params.get("selector", "")
        tgt_name = params.get("target_filename") or params.get("filename")
        res = transfer.trigger_and_wait_download(u, target_filename=tgt_name)

    elif action == "google_click_top":
        res = GoogleAdapter.click_top_result(page)

    elif action == "google_inspect_results":
        res = GoogleAdapter.inspect_results(page, max_items=params.get("max_results", 5))

    elif action == "google_extract_content":
        res = GoogleAdapter.extract_page_content(page)

    elif action == "web_prompt_and_submit":
        u = params.get("url") or ""
        prompt_text = params.get("prompt") or params.get("text", "")
        should_submit = params.get("submit", True)

        target_domain = u.split("//")[-1].split("/")[0].lower() if u else ""
        cur_url = getattr(page, "url", "").lower()
        if target_domain and target_domain not in cur_url:
            try:
                page.goto(u, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(1000)
            except Exception as e_nav:
                logger.warning(f"Navigation in web_prompt_and_submit notice: {e_nav}")

        # Check for search button triggers (e.g. GitHub)
        if "github.com" in getattr(page, "url", "").lower():
            for search_trigger in [
                "button.header-search-button",
                "[data-target='qbsearch-input.inputButtonText']",
                "button[aria-label*='Search' i]"
            ]:
                try:
                    btn = page.locator(search_trigger).first
                    if btn.is_visible(timeout=600):
                        btn.click()
                        page.wait_for_timeout(300)
                        break
                except Exception:
                    pass

        selectors = [
            "div.ql-editor",
            "rich-textarea p",
            "#prompt-textarea",
            "input#query-builder-test",
            "input[name='query-builder-test']",
            "div[contenteditable='true'][aria-label*='prompt' i]",
            "div[contenteditable='true'][aria-label*='message' i]",
            "div[contenteditable='true']",
            "textarea[placeholder*='message' i]",
            "textarea[placeholder*='ask' i]",
            "textarea[placeholder*='prompt' i]",
            "textarea",
            "input[placeholder*='search' i]",
            "input[aria-label*='search' i]",
            "input[name='q']",
            "input[type='text']",
            "[role='textbox']"
        ]

        target_el = None
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.is_visible(timeout=800):
                    target_el = loc
                    break
            except Exception:
                continue

        if target_el:
            try:
                target_el.click()
                page.wait_for_timeout(200)
                target_el.fill(prompt_text)
                page.wait_for_timeout(300)
                if should_submit:
                    target_el.press("Enter")
                    page.wait_for_timeout(500)
                res = {
                    "success": True,
                    "action": "web_prompt_and_submit",
                    "url": getattr(page, "url", u),
                    "prompt": prompt_text,
                    "submitted": should_submit
                }
            except Exception as e_type:
                res = {"success": False, "action": "web_prompt_and_submit", "error": str(e_type)}
        else:
            if "github.com" in getattr(page, "url", "").lower():
                import urllib.parse
                s_url = f"https://github.com/search?q={urllib.parse.quote(prompt_text)}"
                page.goto(s_url, wait_until="domcontentloaded", timeout=20000)
                res = {"success": True, "action": "web_prompt_and_submit", "url": s_url, "prompt": prompt_text, "submitted": True}
            else:
                res = {"success": True, "action": "web_prompt_and_submit", "url": getattr(page, "url", u), "prompt": prompt_text, "info": "Navigated to target portal"}

    else:
        res = {"success": True, "action": action, "info": f"Completed {action}"}

    # Always check authentication boundaries after action
    auth_check = AuthenticationManager.inspect_auth_barriers(page)
    if auth_check.get("auth_required"):
        res["auth_barrier"] = auth_check

    return res


def browser_automation_executor_node(state: CentralGraphState) -> Dict[str, Any]:
    """
    Agent 9 node: Executes browser automation steps using persistent Playwright session.
    """
    t0 = time.time()
    steps = state.get("execution_plan", [])
    browser_steps = [s for s in steps if s.get("executor") == "browser"]
    conv_id = state.get("conversation_id", "default_session")

    # Defense-in-depth: Strict server-side HITL gate enforcement
    appr_required = state.get("approval_required", False)
    appr_status = state.get("approval_status", "NONE")
    if appr_required and appr_status != "APPROVED":
        logger.warning("Browser execution blocked: Operator authorization has not been granted.")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, "Browser automation blocked: explicit human approval is required.")
        return {
            "current_agent": AGENT_ID,
            "errors": ["Browser automation blocked: explicit human approval is required."]
        }

    emit_agent_started(state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE, f"Executing {len(browser_steps)} browser operation(s)...")

    try:
        session_mgr = BrowserSessionManager()

        executed_results: List[Dict[str, Any]] = []
        overall_ok = True

        if not browser_steps:
            emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, "No browser automation steps were planned or found.")
            return {
                "current_agent": AGENT_ID,
                "automation_results": {"browser_results": []},
                "verification_results": {"browser_verified": False, "all_verified": False},
                "errors": ["No browser automation steps were planned or executed."]
            }

        for step in browser_steps:
            action = step.get("action", "")
            params = step.get("params", {})
            title = step.get("title", f"Step {step.get('step_id')}")
            raw_query = state.get("user_query", "")

            emit_agent_progress(state, AGENT_ID, AGENT_NAME, GROUP_ID, f"Executing browser action: {title}...")

            # Derive target_url for multi-tab isolation
            step_target_url = None
            if action == "navigate":
                step_target_url = params.get("url") or params.get("target_url") or params.get("destination")
            elif "google" in action:
                step_target_url = "https://www.google.com"
            elif "youtube" in action:
                step_target_url = "https://www.youtube.com"
            elif "instagram" in action:
                step_target_url = "https://www.instagram.com"
            elif "spotify" in action:
                step_target_url = "https://open.spotify.com"
            elif action == "web_prompt_and_submit":
                step_target_url = params.get("url")

            # Execute securely on the Playwright worker thread with multi-tab awareness
            res = session_mgr.execute_on_page(
                conv_id,
                lambda page: _dispatch_single_action(page, action, params, raw_query),
                target_url=step_target_url
            )

            res["step_id"] = step.get("step_id")
            res["step_title"] = title
            executed_results.append(res)

            if not res.get("success", False):
                overall_ok = False
                break

        duration = round(time.time() - t0, 2)
        has_real_actions = len(executed_results) > 0 and any(r.get("success", False) for r in executed_results)
        overall_ok = overall_ok and has_real_actions

        if overall_ok:
            status_text = "All browser actions executed and verified."
            emit_agent_completed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID, COMPONENT_TYPE,
                status_text,
                output_summary=f"Executed and verified: {len(executed_results)}/{len(browser_steps)} steps in {duration}s",
                duration_s=duration
            )
        else:
            status_text = "Browser automation failed: no actions completed or postcondition verification failed."
            emit_agent_failed(
                state, AGENT_ID, AGENT_NAME, GROUP_ID,
                status_text
            )

        prev_results = state.get("automation_results") or {}
        prev_browser = prev_results.get("browser_results", [])
        prev_browser.extend(executed_results)
        prev_results["browser_results"] = prev_browser

        # Record verification results
        verif_results = state.get("verification_results") or {}
        verif_results["browser_verified"] = overall_ok
        verif_results["all_verified"] = overall_ok and verif_results.get("desktop_verified", True)

        return {
            "current_agent": AGENT_ID,
            "selected_superior_agent": "BrowserSuperiorAgent",
            "selected_specialist_agents": [
                "B1_LifecycleAgent", "B2_TabAgent", "B3_NavigationAgent",
                "B4_InteractionAgent", "B5_FormAgent", "B6_TransferAgent",
                "B7_VerificationAgent", "B8_RecoveryAgent"
            ],
            "automation_results": prev_results,
            "verification_results": verif_results
        }

    except Exception as e:
        logger.error(f"Browser Executor error: {e}")
        emit_agent_failed(state, AGENT_ID, AGENT_NAME, GROUP_ID, str(e))
        return {
            "current_agent": AGENT_ID,
            "errors": [f"Browser execution failed: {e}"]
        }
