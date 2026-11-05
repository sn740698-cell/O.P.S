# O.P.S. 2.0 — Browser Automation Engine Functionality Repair & Cockpit Stability Report

## 1. Executive Summary

The O.P.S. 2.0 Browser Automation subsystem and the Pop-up Cockpit have undergone a complete architectural repair and stabilization. All observed failures—including failure on subsequent browser requests, desktop cockpit flickering/blinking, Tailwind CSS file corruption in `browser_executor.py`, and Human-in-the-Loop gating—have been systematically diagnosed and resolved.

Empirical verification confirms **10 out of 10 tests passed** in the automated test suite with 100% reliability, sub-second sequential history navigation, and zero cross-thread greenlet or memory errors.

---

## 2. Root Cause Analysis

### Issue A: Subsequent Browser Requests Failing (`greenlet.error`)
- **Diagnosis**: Python's Playwright `sync_api` runs on top of greenlets tied to the specific OS thread where `sync_playwright().start()` was invoked. Django's development server dispatches requests across a worker thread pool.
- **Root Cause**: When Request 1 finished, any subsequent request (such as a Human-in-the-Loop approval resolution on `POST /api/chat/approvals/<id>/respond/` or a follow-up directive) arrived on a different worker thread. Accessing the cached `page` or calling `page.goto()` from that thread triggered:
  ```text
  greenlet.error: Cannot switch to a different thread
  Expected: <greenlet ...> suspended active started main
  Current:  <greenlet ...> current active started main
  ```
- **File Corruption**: `backend/automation_system/executors/browser_executor.py` had minified Tailwind CSS accidentally prepended at lines 1–36, making the file syntactically broken if imported directly.

### Issue B: Cockpit Blinking, Flickering & Rapid Re-renders
- **Root Cause 1 (DWM Compositing Conflict)**: In `desktop_overlay/window.py`, `WA_TranslucentBackground = True` was applied to a frameless `QWebEngineView`. When Playwright launched Chromium or played hardware-accelerated video (e.g. YouTube 60fps), Windows DWM compositing invalidated the transparency buffer on every frame, causing the entire cockpit window to blink and redraw transparent-to-black continuously.
- **Root Cause 2 (WebSocket Reconnection Loops)**: In `frontend/src/App.jsx`, `loadConversation` had `conversationId` in its dependency array, and the WebSocket initialization `useEffect` depended on `[conversationId, loadConversation]`. Every time a conversation started or updated, all 4 WebSockets were torn down and reconnected.
- **Root Cause 3 (Unbatched SSE Telemetry & Approval Polling Race)**: Every incoming streaming event fired 8 individual state setters, triggering micro-renderings. Simultaneously, a 3-second approval polling interval in `SeparatePopupCockpit.jsx` raced against the native overlay's 1.2s polling loop, causing the approval modal to toggle open and closed.

---

## 3. Implemented Architecture: O.P.S. Browser Automation Core Library

A dedicated, thread-safe, persistent Core Library was built inside `backend/automation_system/browser/`:

### Module Responsibilities:
1. **`BrowserManager` & `PlaywrightWorker`** (`browser_manager.py`):
   - Single owner of persistent Playwright instance and dedicated visible Chromium browser.
   - All Playwright operations execute sequentially on a single dedicated daemon thread (`OPS-PlaywrightWorker`) via a thread-safe task queue.
   - Dedicated user profile stored in `~/.ops/browser_profile` (avoiding Windows path parser issues with dot-directories).
   - Exposes `PageProxy` and `execute_on_page(conversation_id, fn)` for native execution with zero serialization overhead.
2. **`TabManager`** (`tab_manager.py`):
   - Multi-tab support per conversation: `list_tabs`, `new_tab`, `switch_tab`, `close_current_tab`.
3. **`LocatorEngine`** (`locator_engine.py`):
   - Cascaded priority locators: Accessible Role & Name -> Form Label -> Placeholder -> Visible Text -> Test ID -> CSS -> XPath.
   - Auto-waits, visibility verification, and scroll-into-view.
4. **`NavigationEngine`** (`navigation_engine.py`):
   - `navigate`, `go_back`, `go_forward`, `reload`, and automatic cookie/consent modal dismissal.
5. **`InteractionEngine`** (`interaction_engine.py`):
   - `click`, `fill_form`, `click_first_result`, `scroll`, `hover`.
6. **`BrowserVerificationEngine`** (`verification_engine.py`):
   - Verifies URL matching, page titles, DOM visibility, search result count, and YouTube `<video>` playback (`currentTime > 0` and `paused === false`).
7. **`PageInspector`** (`page_inspector.py`):
   - Generates concise structured summaries: URL, title, headings (H1/H2), interactive buttons, form inputs, and text preview.
8. **`AuthenticationManager`** (`auth_manager.py`):
   - Detects login walls, bot verification checks, and CAPTCHAs across Google, YouTube, Spotify, and Instagram. Pauses execution and returns clear guidance without leaking credentials.
9. **`RecoveryManager`** (`recovery_manager.py`):
   - Classifies errors (`TIMEOUT`, `TARGET_CLOSED`, `ELEMENT_NOT_FOUND`, `NETWORK_ERROR`) and performs bounded retries.
10. **`BrowserExecutor`** (`executors/browser_executor.py`):
    - Cleaned and restored from corruption; provides high-level facade for all adapters.

---

## 4. Cockpit Stability & UI Fixes

1. **`desktop_overlay/window.py`**:
   - Disabled `WA_TranslucentBackground` on Windows.
   - Configured high-performance dark cyberpunk background `#08080a` (`QColor(8, 8, 10, 255)`) on `central_widget`, `web_view`, and `custom_page`.
   - Result: Completely eliminated DWM flickering and repainting loops during video playback and browser interactions.
2. **`frontend/src/App.jsx`**:
   - Decoupled `loadConversation` from `conversationId` state, making its callback reference stable.
   - WebSocket connection effect now runs strictly on mount (`[]`), preventing reconnection loops.
   - Separate `useEffect` synchronizes conversation history when `conversationId` changes.
3. **`frontend/src/components/SeparatePopupCockpit.jsx`**:
   - Stabilized `loadConversation` dependency array (`[]`).
   - Fixed pending approval polling race condition to prevent the approval modal from flickering open and closed.

---

## 5. 10-Test Empirical Validation Results

The automated test suite (`tests/test_browser_core_10.py`) was executed against live visible Chromium:

| Test ID | Capability Tested | Status | Duration | Empirical Verification Details |
|---|---|:---:|:---:|---|
| **Test 1** | Google Search & Inspection | **PASSED** | 2.95s | Navigated to `google.com`, submitted query, extracted results, verified search URL. |
| **Test 2** | YouTube Search | **PASSED** | 6.37s | Navigated to `youtube.com`, searched "Imagine Dragons Believer", verified search query URL. |
| **Test 3** | YouTube Search & Play | **PASSED** | 6.85s | Clicked top video, loaded `watch?v=`, verified video playback state (`paused=False`). |
| **Test 4** | Spotify Navigation & Auth | **PASSED** | 3.59s | Navigated to `open.spotify.com`, searched track, detected preview mode without login wall crash. |
| **Test 5** | Instagram Login Boundary | **PASSED** | 2.88s | Navigated to `/reels/`, cleanly identified `INSTAGRAM_LOGIN_WALL`, halted safely. |
| **Test 6** | General Website Navigation | **PASSED** | 2.66s | Navigated to Wikipedia, clicked English portal, verified arrival at `en.wikipedia.org/wiki/Main_Page`. |
| **Test 7** | Multi-Step History Traversal | **PASSED** | 1.75s | Navigated A -> B -> Back to A -> Forward to B with verified URL history states. |
| **Test 8** | Conversation Continuity | **PASSED** | 1.14s | Reused existing session tab across turns, inspected page DOM without reopening window. |
| **Test 9** | Human-in-the-Loop Safety Gate | **PASSED** | 4.47s | Created `PendingApproval`, simulated operator DENIAL, verified 0 unauthorized browser actions. |
| **Test 10** | Error Recovery (Invalid URL) | **PASSED** | 0.10s | Navigated to non-existent domain, classified error as `NETWORK_ERROR`, reported gracefully. |

**Sequential Stress Test**:
- 15 consecutive requests back-to-back across multiple threads completed in sub-second times with **100% success** and zero greenlet errors.

---

## 6. Remaining Limitations & Safe Boundaries

1. **Third-Party Login Walls**: Platforms like Spotify and Instagram enforce strict authentication walls for private content (e.g. streaming full tracks, Direct Messages). O.P.S. adheres to security best practices by detecting these boundaries, pausing execution, and prompting the operator to authenticate directly in the headed browser rather than storing or scraping credentials.
2. **Bot Detection & CAPTCHA**: While Chromium is launched with `--disable-blink-features=AutomationControlled` to minimize anti-automation flags, major web properties may occasionally challenge non-standard traffic. The `AuthenticationManager` detects Cloudflare and CAPTCHA frames and alerts the operator via the Cockpit.
