# O.P.S. Agent & Tool Matrix

This document details the exact models, capabilities, tools, safety levels, verification assertions, and recovery mechanisms across all O.P.S. agents.

---

## 1. Model-to-Responsibility Matrix

| Model | Purpose in O.P.S. | Called By Component | Host / Provider | Context Window |
|---|---|---|---|---|
| **Qwen3 0.6B** (`qwen3:0.6b-q8_0`) | Sub-50ms Fast Intent Classification & Fast HTML Filtering | Fast Router, BeautifulSoup Agent | Local Ollama | 4,096 tokens |
| **Qwen3 1.7B** (`qwen3:1.7b-q8_0`) | Mission Planning, Reasoning, Code Generation, Bug Diagnosis, Web Prompt Understanding, Quality Checks | Supervisor, Planner, Developer, Debugger, Web Superior, Auto Superior, Retrieval Quality | Local Ollama | 8,192 tokens |
| **Llama 3.2 1B** (`llama3.2:1b-instruct-q8_0`) | Grounded Response Synthesis, Structured Data Extraction, Playwright DOM extraction | Response Agent, ScrapeGraphAI Agent, Crawlee Agent | Local Ollama | 4,096 tokens |
| **Wispr Flow / Whisper** | Speech-to-Text (STT) Audio Transcription | Pop-up Cockpit Voice Input Pipeline | Local Service | Real-time stream |
| **Piper TTS** | Low-latency Voice Synthesis | Pop-up Cockpit Audio Feedback | Local Service | Audio Buffer |

---

## 2. Agent Fleet Matrix

| Agent Name | Tier / Hierarchy | Assigned Model | Primary Responsibility | Allowed Capabilities | Downstream / Child Agents |
|---|---|---|---|---|---|
| **Fast Router** | Tier 0 (Entry) | Qwen3 0.6B | Intent classification & mode assignment | None (Direct routing) | Supervisor |
| **Supervisor** | Tier 1 (Root Coordinator) | Qwen3 1.7B | Workflow coordination & agent dispatch | None (Coordinates) | Planner, All Specialist Agents |
| **Mission Manager** | Tier 1 (Mission Engine) | Python Engine | Stateful DAG execution & bounded recovery | All via Capability Registry | Specialist Agents |
| **Planner** | Tier 1 (Decomposition) | Qwen3 1.7B | Decomposes mission into ordered DAG PlanSteps | None (Generates plan) | Developer, Tester, Debugger |
| **Developer Agent** | Tier 2 (Specialist) | Qwen3 1.7B | Code writing, file manipulation, project scaffolding | `filesystem.read`, `filesystem.write`, `terminal.execute` | Tester, Reviewer |
| **Tester Agent** | Tier 2 (Specialist) | Qwen3 1.7B | Test execution, assertion checking, failure reporting | `terminal.execute`, `terminal.run_tests` | Debugger |
| **Debugger Agent** | Tier 2 (Specialist) | Qwen3 1.7B | Traceback diagnosis, root-cause analysis, patch creation | `filesystem.read`, `filesystem.write`, `terminal.execute` | Developer, Tester |
| **Reviewer Agent** | Tier 2 (Specialist) | Qwen3 1.7B | Code review, security sanity check, diff inspection | `filesystem.read` | Supervisor |
| **Web Superior Agent** | Tier 2 (Domain Lead) | Qwen3 1.7B | Web research & extraction loop management | `web.search`, `web.crawl` | Web Understanding, BS4, ScrapeGraphAI, Crawlee, Retrieval Quality |
| **Web Prompt Understanding** | Tier 3 (Sub-agent) | Qwen3 1.7B | Decomposes user search into queries & strategy | None | BS4 / Crawlee / ScrapeGraphAI |
| **BeautifulSoup Agent** | Tier 3 (Sub-agent) | Qwen3 0.6B | Fast HTML text & metadata extraction | `web.crawl`, `bs4.extract` | Retrieval Quality Agent |
| **ScrapeGraphAI Agent** | Tier 3 (Sub-agent) | Llama 3.2 1B | Structured JSON schema extraction | `web.crawl`, `scrapegraph.extract` | Retrieval Quality Agent |
| **Crawlee Agent** | Tier 3 (Sub-agent) | Llama 3.2 1B | Multi-page recursive web crawling | `web.crawl`, `crawlee.crawl` | Retrieval Quality Agent |
| **Retrieval Quality Agent** | Tier 3 (Sub-agent) | Qwen3 1.7B | Evaluates completeness; triggers re-query loop | None | Web Prompt Understanding (if gap) |
| **Automation Superior Agent** | Tier 2 (Domain Lead) | Qwen3 1.7B | OS & desktop workflow orchestration | `desktop.*`, `browser.*` | Auto Understanding, HITL Gate, Open Web, Installed Apps, Open File, Desktop Control |
| **Auto Prompt Understanding** | Tier 3 (Sub-agent) | Qwen3 1.7B | Classifies target application / file path | None | HITL Gate |
| **HITL Approval Gate** | Tier 3 (Safety Guard) | Deterministic | Evaluates elevation risk & pauses execution | None | Cockpit Approval Modal |
| **Open Web Agent** | Tier 3 (Sub-agent) | Llama 3.2 1B | Interactive Playwright browser control | `browser.open`, `browser.navigate` | Verifier |
| **Installed Apps Agent** | Tier 3 (Sub-agent) | Python Engine | Launches Windows applications (Chrome, VS Code, etc.) | `desktop.launch_app` | Verifier |
| **Open File Agent** | Tier 3 (Sub-agent) | Python Engine | Opens files & folders in default handlers | `desktop.open_file` | Verifier |
| **Desktop Control Agent** | Tier 3 (Sub-agent) | Python Engine | Mouse/Keyboard PyAutoGUI actions | `desktop.mouse_click`, `desktop.type_keys` | Verifier |
| **RAG / Knowledge Agent** | Tier 2 (Specialist) | Qwen3 1.7B | Local vector database semantic search & ingestion | `rag.search`, `rag.ingest` | Response Agent |
| **Response Agent** | Tier 2 (Synthesis) | Llama 3.2 1B | Grounded final output synthesis from evidence | None | Pop-up Cockpit UI |

---

## 3. Comprehensive Tool & Capability Matrix

| Capability Name | Underlying Tool Function | Calling Agent | Safety Risk Level | Requires Human Approval? | Physical Ground-Truth Verification | Error Recovery Strategy |
|---|---|---|---|---|---|---|
| `filesystem.read` | `execute_fs_read` | Developer, Debugger, Reviewer | **SAFE** | No | File exists and size > 0 | Return empty string with error |
| `filesystem.write` | `execute_fs_write` | Developer, Debugger | **SAFE** | No | `os.path.exists(path)` & `os.path.getsize(path) > 0` | Retry with absolute path / create parent dir |
| `filesystem.create_directory` | `execute_fs_create_dir` | Developer, Auto | **SAFE** | No | `os.path.isdir(path)` | Create recursively with `os.makedirs` |
| `filesystem.delete` | `execute_fs_delete` | Auto, Developer | **DANGEROUS** | **YES** | `not os.path.exists(path)` | Abort if not confirmed |
| `terminal.execute` (safe cmd) | `execute_terminal_command` | Developer, Tester, Debugger | **SAFE** | No | Subprocess exit code == 0 | Capture stderr, feed to Debugger |
| `terminal.execute` (system write) | `execute_terminal_command` | Developer, Auto | **ELEVATED** | **YES** | Subprocess exit code == 0 | Abort on denial, re-prompt |
| `terminal.execute` (disk wipe/format) | `execute_terminal_command` | None (Blocked) | **FORBIDDEN** | **NEVER ALLOWED** | N/A (Blocked before execution) | Terminated with critical alert |
| `terminal.run_tests` | `execute_run_tests` | Tester | **SAFE** | No | Pytest/Unittest execution report | Feed test failure trace to Debugger Agent |
| `desktop.launch_app` | `execute_launch_app` | Installed Apps, Auto | **SAFE** | No | Process name active in Windows tasklist | Fallback to Windows `start <app>` command |
| `desktop.open_file` | `execute_open_file` | Open File, Auto | **SAFE** | No | `os.path.exists(path)` | Check file path formatting and permissions |
| `browser.open` | `execute_browser_open` | Open Web, Browser | **SAFE** | No | Playwright DOM loaded / status 200 | Retry in headless mode / standard browser |
| `browser.navigate` | `execute_browser_navigate` | Open Web, Browser | **SAFE** | No | Page URL matches destination | Timeout recovery after 10s |
| `browser.click` | `execute_browser_click` | Browser | **SAFE** | No | DOM element state change | Retry with alternative selector or text match |
| `browser.type` | `execute_browser_type` | Browser | **SAFE** | No | Input value set in DOM | Focus window and retry key simulation |
| `web.search` | `OPSScrapingService.search` | Web Superior, Web Agent | **SAFE** | No | Results list length > 0 | Fallback to DuckDuckGo / SearXNG |
| `web.crawl` | `OPSScrapingService.scrape_url` | Web Superior, Crawlee, BS4 | **SAFE** | No | Extracted markdown length > 50 chars | Try BeautifulSoup fallback if ScrapeGraph fails |
| `rag.search` | `OPSRAGService.query_knowledge` | RAG Agent | **SAFE** | No | Similarity score threshold match | Return "No relevant knowledge found" |
| `rag.ingest` | `OPSRAGService.ingest_text` | RAG Agent | **SAFE** | No | ChromaDB document count incremented | Re-chunk text and retry vector insertion |
| `voice.transcribe` | `WisprFlowVoiceService.transcribe` | Voice Subsystem | **SAFE** | No | Text transcription non-empty | Prompt user to repeat voice directive |
| `voice.synthesize` | `WisprFlowVoiceService.synthesize` | Voice Subsystem | **SAFE** | No | Audio buffer non-empty | Fallback to silent UI output |
