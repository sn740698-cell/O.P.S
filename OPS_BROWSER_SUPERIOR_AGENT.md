# O.P.S. 2.0 — Browser Automation Superior Agent & Specialist Fleet (B1–B8)

## 1. Executive Summary

The **Browser Automation Superior Agent** acts as the high-level operational director for all browser workflows across O.P.S. 2.0. Rather than executing browser actions monolithically, the Superior Agent decomposes directives into atomic operational phases and delegates them to eight specialized sub-agents:

```
                            ┌────────────────────────────────────────┐
                            │        Browser Superior Agent          │
                            │   (Supervisor, Decomposition, Telemetry)│
                            └───────────────────┬────────────────────┘
                                                │
         ┌───────────┬───────────┬───────────┬──┴────────┬───────────┬───────────┬───────────┐
         ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼
       [ B1 ]      [ B2 ]      [ B3 ]      [ B4 ]      [ B5 ]      [ B6 ]      [ B7 ]      [ B8 ]
      Lifecycle     Tab         Nav       Interact     Forms     Transfer    Verifier   Recovery
```

---

## 2. The 8 Specialist Browser Sub-Agents

| Agent ID | Class Name | Core Responsibility | Key Methods / Capabilities |
| :--- | :--- | :--- | :--- |
| **B1** | `B1_LifecycleAgent` | Chromium process lifecycle & context health | `ensure_browser_ready()`, `get_session_status()`, `restart_session()`, `close_browser()` |
| **B2** | `B2_TabAgent` | Multi-tab tracking & domain reuse | `new_tab()`, `switch_tab()`, `close_current_tab()`, `list_tabs()`, `get_or_create_tab()` |
| **B3** | `B3_NavigationAgent` | URL routing & modal overlay dismissal | `navigate()`, `go_back()`, `go_forward()`, `reload()` |
| **B4** | `B4_InteractionAgent` | DOM element actuation & scrolling | `click()`, `click_first_result()`, `scroll()`, `press_key()` |
| **B5** | `B5_FormAgent` | Input field typing & HITL safety pauses | `fill_field()`, `fill_form_batch()`, `clear_field()` |
| **B6** | `B6_TransferAgent` | File downloads & uploads | `trigger_and_wait_download()`, `upload_file()` |
| **B7** | `B7_VerificationAgent` | Empirical DOM & media verification | `verify_state()`, `verify_youtube_playing()`, `capture_screenshot()` |
| **B8** | `B8_RecoveryAgent` | Bounded error classification & recovery | `classify()`, `execute_with_recovery()` |

---

## 3. Thread-Affinity Worker Pattern

To prevent greenlet threading crashes inherent in cross-thread Playwright operations:
- All Playwright objects (`BrowserContext`, `Page`, `Locator`) are isolated to a single dedicated worker thread (`OPS-PlaywrightWorker`).
- `BrowserSessionManager` routes execution via `execute_on_page(conversation_id, fn)` using a thread-safe message queue.
- Calls from any Django WSGI thread or sub-agent execute synchronously on the worker and return clean serialized dictionaries.

---

## 4. Real-Time Telemetry to Cockpit

Whenever a specialist agent is activated or completes a phase, the Superior Agent publishes an event to `event_bus`:
- `agent.started`: Dispatched when the directive begins.
- `agent.handoff`: Dispatched when control transfers to a specialist (e.g. B3 -> B4).
- `agent.progress`: Dispatched during step execution.
- `agent.completed`: Dispatched when postcondition verification passes.
