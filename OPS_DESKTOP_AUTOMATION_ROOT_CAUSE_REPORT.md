# O.P.S. 2.0 — Desktop Automation Root Cause Analysis & Architecture Plan

## 1. Executive Summary

A comprehensive architectural audit was performed on O.P.S. 2.0's desktop automation subsystem (`backend/automation_system/` and `backend/research_system/orchestrator/agents/desktop_automation_executor.py`). 

While basic hooks for Pywinauto and filesystem utilities existed, the system suffered from critical architectural limitations that prevented reliable execution of natural-language desktop workflows. Specifically:
- Application launching relied on static hardcoded aliases without registry or Start Menu discovery, failing on general Windows applications.
- No instance detection existed; requests to open an already-running app launched duplicate instances or threw window title collision errors (`ElementAmbiguousError`).
- In-place application closing lacked graceful termination checks and unsaved-changes detection.
- File and code editing lacked safe targeted replacement, backup mechanisms (`.bak`), and LLM-driven code generation.
- Human-in-the-Loop (HITL) gate enforcement was inconsistent across plan generation and lacked structured cancellation handling when denied.
- Verification relied on naive sleeps rather than empirical post-condition checks (window state, file existence, content matches, process shutdown).

This report outlines the root causes and defines the 5-module **Desktop Automation Engine** architecture to achieve 100% test pass rates across the 20 benchmark tests.

---

## 2. Identified Root Causes & Deficiencies

### Root Cause 1: Static Application Resolution & Absence of Registry/Path Fallbacks
- **Observed Defect**: `DesktopExecutor.launch_app` used a trivial hardcoded `if/elif` block checking only `notepad`, `code`, `calc`, `explorer`, and `spotify`.
- **Impact**: Inability to resolve standard Windows utilities and applications (e.g. Acrobat Reader, SumatraPDF, Paint, Word, Excel, PowerPoint, VLC, Windows Terminal) or installed applications located outside standard PATH.
- **Architectural Remedy**: Implement a 4-tier application resolver:
  1. `shutil.which` (System PATH)
  2. Windows Registry `App Paths` (`HKLM` & `HKCU\Software\Microsoft\Windows\CurrentVersion\App Paths`)
  3. Standard Windows Installation Paths (`Program Files`, `Program Files (x86)`, `LocalAppData\Programs`, `AppData\Roaming`)
  4. Start Menu Programs shortcuts (`*.lnk` resolution via COM / WScript.Shell)

### Root Cause 2: Lack of Running Instance Detection & Foreground Focus
- **Observed Defect**: When an application was already running, launching it again initiated a duplicate process rather than focusing the existing window. Subsequent Pywinauto calls often failed with `ElementAmbiguousError` due to multiple matching window titles.
- **Impact**: Failed Test 16 ("Application already running") and cluttered user desktop.
- **Architectural Remedy**: Query `pywinauto.Desktop` and Windows APIs (`FindWindow`, `SetForegroundWindow`, `BringWindowToTop`) to detect existing instances, bring them to the foreground, set active window reference, and return `{status: "already_running", action: "brought_to_front"}`.

### Root Cause 3: Brittle Window Closing & Lack of Unsaved Dialog Handling
- **Observed Defect**: Application closing either called `win.close()` abruptly or force-terminated the PID without checking for unsaved changes or prompt dialogs.
- **Impact**: Potential data loss or hung processes if a "Do you want to save changes?" dialog appeared.
- **Architectural Remedy**: Implement graceful shutdown via `WM_CLOSE` / `win.close()`, inspect for child modal dialogs, and verify process termination empirically. Only fall back to process termination if graceful close fails and user explicitly permits.

### Root Cause 4: Absence of LLM-Driven Code Generation & Safe File Editing
- **Observed Defect**: Directives like "Create a Python file with a calculator app" or "Modify app.py to add a new route" had no dedicated code synthesizer. `FileSystemExecutor` only accepted pre-formed raw strings.
- **Impact**: Directives failed or generated empty files. Existing files were overwritten rather than edited safely.
- **Architectural Remedy**: Create `CodeWriter` module integrating local `Qwen3 1.7B` via `ollama_client`. Support full generation for Python, JavaScript, TypeScript, HTML, CSS, JSX, JSON, and SQL. For editing:
  1. Create automatic backup `<filename>.bak`.
  2. Load complete existing file into memory.
  3. Prompt Qwen3 1.7B for precise replacement or targeted snippet edit.
  4. Preserve all unrelated comments, docstrings, imports, and indentation.
  5. Validate syntax (AST parse for Python, JSON parse for JSON).

### Root Cause 5: Unvalidated Paths & Missing Clarification Workflow
- **Observed Defect**: If a user asked "Open my Python file" without a path, the planner either guessed an arbitrary file or failed with an unhandled exception.
- **Impact**: Failed Test 14 ("Ambiguous file request").
- **Architectural Remedy**: Integrate ambiguity detection in `AutomationPlanner`. If file, folder, or application target is underspecified, return `NEEDS_CLARIFICATION` with a direct question to the user, halting execution until clarified.

### Root Cause 6: Weak Verification & Non-Standard Execution Statuses
- **Observed Defect**: Verification returned simple boolean flags without deep checks (e.g. checking file size $>0$, reading back file content, verifying window is actually visible on screen).
- **Impact**: Inability to diagnose intermittent automation delays or report truthful progress to the Cockpit.
- **Architectural Remedy**: Implement `VerificationEngine` with empirical state assertions, bounded retries (max 3), and standard lifecycle statuses: `PENDING`, `EXECUTING`, `VERIFYING`, `COMPLETED`, `FAILED`, `CANCELLED_BY_USER`, `REQUIRES_CLARIFICATION`.

---

## 3. Five-Module Desktop Automation Architecture

```
d:\Projects\O.P.S\backend\automation_system\desktop\
├── __init__.py                     # Unified package export
├── application_controller.py       # Module 1: Universal app resolver, launcher, instance activator, safe closer
├── gui_controller.py               # Module 2: Pywinauto UIA/Win32, locators, typing, clicks, hotkeys, reader
├── file_controller.py              # Module 3: Filesystem controller (open, create, read, edit, delete, backup)
├── code_writer.py                  # Module 4: Qwen3 1.7B code generator, targeted editor, syntax verifier
└── verification_engine.py          # Module 5: Empirical state verifier, retry manager, status reporter
```

### Module Responsibilities Matrix

| Module | Core Responsibilities | Key Technologies |
| :--- | :--- | :--- |
| **`ApplicationController`** | Resolve apps (PATH, Registry, Start Menu), detect running instances, bring to focus, safe close | `winreg`, `shutil`, `psutil`, `pywinauto` |
| **`GUIController`** | Window connect, element locators (auto_id, control_type, name), typing, shortcuts, text extraction | `pywinauto.Application`, `Desktop`, UIA/Win32 |
| **`FileController`** | Open files/folders, create, read, edit with backup, safe delete, system path protection | `pathlib`, `os`, `shutil`, `re` |
| **`CodeWriter`** | Synthesize complete code via Qwen3 1.7B, targeted non-destructive edits, AST syntax checks | `ollama_client`, `ast`, `json` |
| **`VerificationEngine`** | Verify window visible, file exists, content matches, process closed; bounded retries | `os.stat`, `pywinauto`, `time` |

---

## 4. LangGraph, HITL, & Cockpit Integration Plan

1. **Automation Planner**:
   - Updates to deterministic rules and Qwen3 prompt templates for all 20 desktop actions.
   - Ambiguous target detection -> emit `NEEDS_CLARIFICATION`.
2. **Safety Gate (HITL)**:
   - File creation, edits, deletions, and application launches flagged as requiring operator approval.
   - Rejection (`DENY`) cancels immediately with 0 actions taken and state updated.
3. **Execution Node (`desktop_automation_executor_node`)**:
   - Invokes the unified desktop modules.
   - Dispatches step progress, verification metrics, and final summaries to `EventBus` and WebSocket streams.
4. **Pop-up Cockpit Stability**:
   - Seamless live updates without page reload or UI flicker, retaining multi-turn history.
