# O.P.S. 2.0 — Advanced Multi-Agent Automation Architecture

## 1. Architectural Overview

O.P.S. 2.0 upgrades from monolithic execution agents into an advanced, two-tier hierarchical multi-agent automation system:

```
                            ┌────────────────────────────────────────┐
                            │    LangGraph Central Orchestrator      │
                            │   (Intent Router + Safety HITL Gate)   │
                            └───────────────────┬────────────────────┘
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 │                              │                              │
                 ▼                              ▼                              ▼
    ┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
    │ Browser Superior Agent  │    │ Desktop Superior Agent  │    │   Hybrid Coordinator    │
    │ (B1–B8 Fleet Manager)   │    │ (D1–D8 Fleet Manager)   │    │ (DAG Scheduler & Locks) │
    └────────────┬────────────┘    └────────────┬────────────┘    └────────────┬────────────┘
                 │                              │                              │
    ┌────────────┴────────────┐    ┌────────────┴────────────┐                 │
    │ B1: Lifecycle Agent     │    │ D1: App Controller      │                 │
    │ B2: Tab Agent           │    │ D2: Window Agent        │                 │
    │ B3: Navigation Agent    │    │ D3: GUI Interaction     │                 │
    │ B4: Web Interaction     │    │ D4: File & Folder Agent │                 │
    │ B5: Form & Entry Agent  │    │ D5: Keyboard & Input    │                 │
    │ B6: Transfer Agent      │    │ D6: Code Writer Agent   │                 │
    │ B7: Browser Verifier    │    │ D7: Desktop Verifier    │                 │
    │ B8: Browser Recovery    │    │ D8: Desktop Recovery    │                 │
    └─────────────────────────┘    └─────────────────────────┘                 │
                 ▲                              ▲                              │
                 └──────────────────────────────┴──────────────────────────────┘
```

---

## 2. Browser Superior Agent & Specialist Fleet (B1–B8)

1. **`B1_LifecycleAgent`**: Manages the persistent Chromium context via `BrowserSessionManager`. Detects thread affinity boundaries, connects to running instances, and tracks browser health.
2. **`B2_TabAgent`**: Multi-tab lifecycle manager. Opens, switches, and closes tabs while reusing open tabs matching targeted domains.
3. **`B3_NavigationAgent`**: Handles URL navigation, history traversal (back/forward/reload), and automatically dismisses modal consent dialogues.
4. **`B4_InteractionAgent`**: Handles accessible DOM clicks, first-result selections (YouTube, Google), page scrolling, and key presses.
5. **`B5_FormAgent`**: Safe input field entry with secret masking in logs and Human-in-the-Loop pre-submission pauses.
6. **`B6_TransferAgent`**: Waits for file downloads, verifies non-zero byte payloads, and manages file uploads.
7. **`B7_VerificationAgent`**: Validates post-execution DOM state, URL matching, and media playback (e.g. YouTube video playback confirmation).
8. **`B8_RecoveryAgent`**: Error classifier (TIMEOUT, TARGET_CLOSED, ELEMENT_NOT_FOUND) executing bounded retries (max 1–2).

---

## 3. Desktop Superior Agent & Specialist Fleet (D1–D8)

1. **`D1_AppAgent`**: Resolves binaries across PATH and Registry App Paths; handles Windows 11 packaged UWP application launch stubs via `explorer.exe shell:AppsFolder\...`.
2. **`D2_WindowAgent`**: Discovers top-level desktop windows using `win32service.OpenDesktop("default", ...)`, manages window geometry (maximize, minimize, restore), and brings handles to the foreground.
3. **`D3_GUIAgent`**: Pywinauto UIA/Win32 control tree inspector, clicking buttons, menus, and system dialogs.
4. **`D4_FileAgent`**: Manages disk files and folders, system path protections (`C:\Windows`, `C:\Program Files`), and automatic `.bak` safety backups.
5. **`D5_InputAgent`**: Enforces UI Automation `ValuePattern.SetValue` text injection to bypass UIPI privilege isolation, plus Win32 `keybd_event` system shortcuts (`Ctrl+S`, `Ctrl+A`, `Alt+F4`).
6. **`D6_CodeAgent`**: Generates code with Qwen3 1.7B, verifies AST syntax validity before disk writes, and types code into active editors.
7. **`D7_VerificationAgent`**: Validates window existence, file creation timestamps, file content signatures, and process termination.
8. **`D8_RecoveryAgent`**: Missing control recovery, app refocusing, and bounded recovery retries.

---

## 4. Hybrid Automation Coordinator

- **DAG Subtask Scheduling**: Translates composite directives into structured subtasks with explicit dependencies.
- **True Parallel Execution**: Dispatches independent subtasks simultaneously using `ThreadPoolExecutor`.
- **Resource Locking**: Employs `ResourceLockManager` to prevent race conditions on shared files or applications.
- **Bidirectional State Handoff**: Passes file paths, tokens, and outputs between browser and desktop domains.
