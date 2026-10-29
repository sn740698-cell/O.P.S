# O.P.S. User Command Flow Examples (20 Real Flows)

This document traces the complete execution lifecycle across the canonical O.P.S. pipeline for 20 real user commands.

---

## The Canonical Execution Pipeline

```text
USER INPUT -> POP-UP COCKPIT -> SESSION MANAGER -> QWEN3 0.6B ROUTER -> SUPERVISOR -> DIRECT EXECUTION / MISSION MANAGER (PLANNER) -> AGENTS (WEB / AUTO / DEV / RAG) -> CAPABILITY REGISTRY -> SAFETY GATE -> TOOL EXECUTOR -> REAL EXECUTION -> VERIFIER -> RECOVERY (IF NEEDED) -> RESPONSE AGENT -> EVENT BUS -> COCKPIT + AGENTS UI
```

---

## 20 Real Command Flow Traces

| # | User Command | Router Decision | Supervisor Dispatch | Mission? | Agents Activated | Capability Used | Underlying Tool | Verification Assertion | Final UI Output |
|---|---|---|---|---|---|---|---|---|---|
| **1** | "Open Chrome." | `TASK` / `LAUNCH_BROWSER` | Auto Superior | No | Automation / Installed Apps | `desktop.launch_app` | `execute_launch_app` | Chrome process verified in Windows tasklist | "Successfully launched Google Chrome." |
| **2** | "Open VS Code." | `TASK` / `LAUNCH_APP` | Auto Superior | No | Automation / Installed Apps | `desktop.launch_app` | `execute_launch_app` | `code.exe` process verified | "Visual Studio Code opened." |
| **3** | "Create a folder called OPS_TEST." | `TASK` / `CREATE_DIRECTORY` | Developer | No | Developer | `filesystem.create_directory` | `execute_fs_create_dir` | Directory verified on disk (`os.path.isdir`) | "Folder `OPS_TEST` created." |
| **4** | "Delete this folder." | `TASK` / `DELETE_PATH` | Safety Gate | No | Auto / Safety Gate | `filesystem.delete` | `execute_fs_delete` | Deleted path no longer exists | Prompts HITL Approval Modal -> Deletes upon user confirmation |
| **5** | "Search the web for latest React docs." | `TASK` / `WEB_SEARCH` | Web Superior | No | Web Superior, Web Prompt Understanding, BS4 | `web.search` | `OPSScrapingService.search` | HTTP search response > 0 results | Summary of React documentation with citations |
| **6** | "Research React state management." | `TASK` / `WEB_RESEARCH` | Web Superior | No | Web Superior, Crawlee, Retrieval Quality | `web.crawl` | `OPSScrapingService.scrape_url` | Content length > 500 chars | Comprehensive comparative breakdown of Redux, Zustand, Context |
| **7** | "Open Google and search React." | `TASK` / `BROWSER_CONTROL` | Auto Superior | No | Auto Superior, Open Web Agent | `browser.open`, `browser.type` | `execute_browser_open` | Playwright DOM loaded & search query submitted | Interactive browser opens to Google search page |
| **8** | "Extract table from webpage." | `TASK` / `WEB_SCRAPE` | Web Superior | No | Web Superior, ScrapeGraphAI Agent | `web.crawl` | `OPSScrapingService.scrape_url` | Parsed JSON table schema valid | Cleanly formatted Markdown table in Cockpit |
| **9** | "Where is my API code?" | `TASK` / `RAG_SEARCH` | RAG Domain | No | RAG / Knowledge Agent, Response Agent | `rag.search` | `OPSRAGService.query_knowledge` | ChromaDB cosine similarity match > 0.7 | "Your API routes are defined in `backend/ops_core/views.py`." |
| **10** | "Find the file auth.py." | `TASK` / `FIND_FILE` | Developer | No | Developer Agent | `filesystem.read` | `execute_fs_read` | `os.path.exists` matches path | "Found `auth.py` at `backend/ops_core/auth.py`." |
| **11** | "Create a small Python program." | `TASK` / `CODE_GEN` | Developer | No | Developer Agent | `filesystem.write` | `execute_fs_write` | `os.path.getsize(path) > 0` | "Created `calculator.py` with full operations." |
| **12** | "Create tests for the Python program." | `TASK` / `TEST_GEN` | Developer | No | Developer Agent | `filesystem.write` | `execute_fs_write` | File exists with test assertions | "Created `test_calculator.py` with 5 test cases." |
| **13** | "Run the tests." | `TASK` / `RUN_TESTS` | Developer Fleet | No | Tester Agent | `terminal.run_tests` | `execute_run_tests` | Pytest report parsed, exit code 0 | "All 5 tests passed successfully (100% OK)." |
| **14** | "Review the code." | `TASK` / `CODE_REVIEW` | Developer Fleet | No | Reviewer Agent | `filesystem.read` | `execute_fs_read` | File diff inspected | "Code review complete: Clean structure, zero security vulnerabilities." |
| **15** | "Fix this bug." | `MISSION` / `BUG_FIX` | Mission Manager | Yes (3 Steps) | Planner, Debugger, Developer, Tester | `filesystem.read`, `filesystem.write`, `terminal.run_tests` | `execute_fs_write`, `execute_run_tests` | Pytest re-run passes with exit code 0 | "Debugger identified `IndexError` on line 14 and patched it." |
| **16** | "Build a React dashboard." | `MISSION` / `SOFTWARE_DEV` | Mission Manager | Yes (5 Steps) | Planner, Developer, Tester, Reviewer | `filesystem.write`, `terminal.execute` | Multi-file write + npm build | `build/` directory created, exit code 0 | "React dashboard scaffolded, compiled, and ready." |
| **17** | "Run a terminal command (dir)." | `TASK` / `TERMINAL_CMD` | Developer | No | Developer Agent | `terminal.execute` | `execute_terminal_command` | Subprocess exit code == 0 | Captured stdout formatted cleanly in Cockpit |
| **18** | "Start development server." | `TASK` / `START_SERVER` | Developer | No | Developer Agent | `terminal.execute` | `execute_terminal_command` | Local port listening verified | "Development server started on `http://127.0.0.1:8000`." |
| **19** | "Stop the running mission." | `TASK` / `SESSION_STOP` | Session Manager | No | Supervisor | `session.stop` | `SessionManager.stop_execution` | `is_active=False` in session state | "Mission halted safely. Conversation state preserved." |
| **20** | "Refresh the session." | `TASK` / `SESSION_REFRESH` | Session Manager | No | Supervisor | `session.refresh` | `SessionManager.refresh_session` | New `session_id`, ChromaDB memory intact | "Session context refreshed. Long-term memory preserved." |
