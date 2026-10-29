# O.P.S. Codebase Implementation & Architecture Map

This document provides a 1-to-1 mapping between the canonical O.P.S. architecture specification and the actual codebase files, classes, methods, endpoints, tools, and events.

---

## 1. Complete Architecture Map

```text
Layer                  Directory / File                                  Class / Function                    Emitted Events
-----------------------------------------------------------------------------------------------------------------------------------------
POP-UP COCKPIT         frontend/src/App.jsx                             App() Component                     USER_INPUT_RECEIVED, APPROVAL_GRANTED, APPROVAL_DENIED
AGENTS UI              frontend/src/components/OpsLiveOrchestrationTab.jsx OpsLiveOrchestrationTab()         (Subscribes to all backend events via WebSocket)
SESSION MANAGER        backend/ops_core/session/session_manager.py       SessionManager                      SESSION_CREATED, SESSION_UPDATED, SESSION_STOPPED, SESSION_RESET
FAST ROUTER            backend/ops_core/router/fast_router.py            FastRouter.route()                  ROUTER_STARTED, ROUTER_COMPLETED
SUPERVISOR             backend/ops_core/orchestration/supervisor.py      Supervisor.handle_request()         SUPERVISOR_STARTED, SUPERVISOR_COMPLETED
MISSION MANAGER        backend/ops_core/orchestration/mission_manager.py MissionManager.execute_mission()    MISSION_CREATED, MISSION_STARTED, MISSION_STEP_STARTED, MISSION_STEP_COMPLETED, MISSION_COMPLETED
PLANNER                backend/ops_core/orchestration/planner.py         Planner.create_plan()               PLAN_CREATED, PLAN_UPDATED
CAPABILITY REGISTRY    backend/ops_core/capabilities/registry.py         CapabilityRegistry                  CAPABILITY_SELECTED
SAFETY GATE            backend/ops_core/safety/safety_gate.py            SafetyGate.evaluate_action()        SAFETY_CHECK_STARTED, SAFETY_CHECK_PASSED, APPROVAL_REQUIRED, SAFETY_CHECK_FAILED
INJECTION GUARD        backend/ops_core/safety/injection_guard.py        PromptInjectionGuard.inspect_input() APPROVAL_REQUIRED
TOOL EXECUTOR          backend/ops_core/tools/executor.py                ToolExecutor.execute_capability()   TOOL_STARTED, TOOL_COMPLETED, TOOL_FAILED
GROUND-TRUTH VERIFIER  backend/ops_core/verification/verifier.py         Verifier.verify_tool_execution()    VERIFICATION_STARTED, VERIFICATION_PASSED, VERIFICATION_FAILED
GROUND-TRUTH INSPECTOR backend/ops_core/verification/ground_truth.py     GroundTruthInspector                VERIFICATION_PASSED, VERIFICATION_FAILED
RESPONSE SYNTHESIZER   backend/ops_core/agents/response_agent.py         ResponseAgent.process()             RESPONSE_STARTED, RESPONSE_COMPLETED
EVENT BUS              backend/ops_core/services/event_bus.py            OPSEventBus.emit_ops_event_async()  StructuredOPSEvent (via WebSocket / SSE)
```

---

## 2. Specialized Agents Map

```text
Agent Domain           File Path                                         Class Name                          Allowed Capabilities
-----------------------------------------------------------------------------------------------------------------------------------------
Developer              backend/ops_core/agents/developer_agent.py        DeveloperAgent                      filesystem.read, filesystem.write, terminal.execute
Debugger               backend/ops_core/agents/debugger_agent.py         DebuggerAgent                       filesystem.read, filesystem.write, terminal.execute
Tester                 backend/ops_core/agents/tester_agent.py           TesterAgent                         terminal.execute, terminal.run_tests
Reviewer               backend/ops_core/agents/reviewer_agent.py         ReviewerAgent                       filesystem.read
Web Superior Domain    backend/ops_core/services/agents/web_agents.py    WebSuperiorAgent                    web.search, web.crawl
├─ Web Prompt Underst. backend/ops_core/services/agents/web_agents.py    WebPromptUnderstandingAgent         (Sub-agent planning & search formulation)
├─ ScrapeGraphAI Agent backend/ops_core/services/agents/web_agents.py    ScrapeGraphAIAgent                  web.crawl, scrapegraph.extract
├─ BeautifulSoup Agent backend/ops_core/services/agents/web_agents.py    BeautifulSoupAgent                  web.crawl, bs4.extract
├─ Crawlee Agent       backend/ops_core/services/agents/web_agents.py    CrawleeAgent                        web.crawl, crawlee.crawl
└─ Retrieval Quality   backend/ops_core/services/agents/web_agents.py    RetrievalQualityAgent               (Self-correction & quality assessment loop)
Auto Superior Domain   backend/ops_core/services/agents/automation_agents.py AutomationSuperiorAgent         desktop.*, browser.*, filesystem.*
├─ Auto Prompt Underst.backend/ops_core/services/agents/automation_agents.py AutoPromptUnderstandingAgent     (Action classification & target identification)
├─ HITL Approval Gate  backend/ops_core/services/agents/automation_agents.py HITLApprovalGate               (Human-in-the-loop elevation check)
├─ Open Web Agent      backend/ops_core/services/agents/automation_agents.py OpenWebAgent                    browser.open, browser.navigate
├─ Installed Apps Agentbackend/ops_core/services/agents/automation_agents.py InstalledAppsAgent              desktop.launch_app
├─ Open File Agent     backend/ops_core/services/agents/automation_agents.py OpenFileAgent                   desktop.open_file
└─ Desktop Control     backend/ops_core/services/agents/automation_agents.py DesktopControlAgent             desktop.mouse_click, desktop.type_keys
RAG / Knowledge Agent  backend/ops_core/agents/rag_agent.py              RAGAgent                            rag.search, rag.ingest
Response Agent         backend/ops_core/agents/response_agent.py         ResponseAgent                       (Grounded synthesis & final formatting)
```

---

## 3. Tool Implementations Map

```text
Tool Category          File Path                                         Functions
-----------------------------------------------------------------------------------------------------------------------------------------
Filesystem Tools       backend/ops_core/tools/filesystem_tools.py        execute_fs_read(), execute_fs_write(), execute_fs_create_dir(), execute_fs_delete()
Terminal Tools         backend/ops_core/tools/terminal_tools.py          execute_terminal_command(), execute_run_tests()
Desktop / App Tools    backend/ops_core/tools/desktop_tools.py           execute_launch_app(), execute_open_file()
Browser Tools          backend/ops_core/tools/browser_tools.py           execute_browser_open(), execute_browser_navigate(), execute_browser_click(), execute_browser_type(), execute_browser_extract()
Web Scraping & Search  backend/ops_core/services/scraping_service.py     OPSScrapingService.search(), OPSScrapingService.scrape_url()
RAG / ChromaDB Tools   backend/ops_core/services/rag_service.py          OPSRAGService.ingest_text(), OPSRAGService.query_knowledge()
Voice Tools            backend/ops_core/services/voice_service.py        WisprFlowVoiceService.transcribe(), WisprFlowVoiceService.synthesize()
```

---

## 4. API Endpoints Map

```text
HTTP Method   Endpoint                             View / Handler Class              File Path
-----------------------------------------------------------------------------------------------------------------------------------------
POST          /api/v1/ops/execute/                 CanonicalExecuteView              backend/ops_core/views.py
POST          /api/v1/ops/session/stop/            CanonicalSessionStopView          backend/ops_core/views.py
POST          /api/v1/ops/session/refresh/         CanonicalSessionRefreshView       backend/ops_core/views.py
GET           /api/v1/ops/session/state/           SessionStateView                  backend/ops_core/views.py
POST          /api/v1/ops/approval/respond/        ApprovalResponseView              backend/ops_core/views.py
WS            /ws/agent/                           OPSEventConsumer                  backend/ops_core/consumers.py
GET           /api/v1/ops/rag/query/               RAGQueryView                      backend/ops_core/views.py
POST          /api/v1/ops/rag/ingest/              RAGIngestView                     backend/ops_core/views.py
GET           /api/v1/ops/voice/status/            VoiceStatusView                   backend/ops_core/views.py
```
