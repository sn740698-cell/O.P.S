# O.P.S. 2.0 — Desktop Automation Superior Agent & Specialist Fleet (D1–D8)

## 1. Executive Summary

The **Desktop Automation Superior Agent** serves as the central operational director for all Windows desktop automation in O.P.S. 2.0. Rather than issuing monolithic scripts, it partitions natural-language directives into structured subtasks delegated to eight specialized sub-agents:

```
                            ┌────────────────────────────────────────┐
                            │        Desktop Superior Agent          │
                            │   (Supervisor, Decomposition, Telemetry)│
                            └───────────────────┬────────────────────┘
                                                │
         ┌───────────┬───────────┬───────────┬──┴────────┬───────────┬───────────┬───────────┐
         ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼
       [ D1 ]      [ D2 ]      [ D3 ]      [ D4 ]      [ D5 ]      [ D6 ]      [ D7 ]      [ D8 ]
        App        Window        GUI        Files       Input       Code      Verifier   Recovery
```

---

## 2. The 8 Specialist Desktop Sub-Agents

| Agent ID | Class Name | Core Responsibility | Key Methods / Capabilities |
| :--- | :--- | :--- | :--- |
| **D1** | `D1_AppAgent` | Application resolution, packaged UWP launcher, & graceful closure | `resolve_app()`, `launch()`, `close()`, `bring_to_front()` |
| **D2** | `D2_WindowAgent` | Interactive desktop window discovery & geometry | `find_window()`, `list_open_windows()`, `focus_window()`, `set_window_state()` |
| **D3** | `D3_GUIAgent` | Pywinauto UIA/Win32 accessible control tree inspection & actuation | `inspect_controls()`, `click_button()`, `read_control()` |
| **D4** | `D4_FileAgent` | File operations, system path protection & `.bak` backups | `create_file()`, `read_file()`, `edit_file()`, `delete_file()`, `open_file()`, `open_folder()` |
| **D5** | `D5_InputAgent` | UIPI-bypassing UIA ValuePattern typing & Win32 `keybd_event` shortcuts | `type_text()`, `send_keys()` |
| **D6** | `D6_CodeAgent` | Qwen3 1.7B code generation with mandatory pre-write AST validation | `generate_and_write()`, `edit_code()`, `type_into_editor()` |
| **D7** | `D7_VerificationAgent` | Empirical postcondition verification for windows, files, and processes | `verify_window()`, `verify_file()`, `verify_file_content()`, `verify_closed()` |
| **D8** | `D8_RecoveryAgent` | Failure classification and bounded recovery interventions | `classify_error()`, `execute_with_recovery()` |

---

## 3. Windows 11 Compatibility Safeguards

1. **UWP Packaged Apps**: Windows 11 Notepad and Calculator cannot be launched simply via `Application.start("notepad.exe")` from services without background process suspension. `D1_AppAgent` delegates to `explorer.exe shell:AppsFolder\Microsoft.WindowsNotepad_8wekyb3d8bbwe!App`.
2. **Interactive Desktop Attachment**: Background worker threads attach to `win32service.OpenDesktop("default", ...)` before window enumeration.
3. **UIPI Privilege Isolation**: Injected keystrokes bypass `SendInput` dropouts via UI Automation `ValuePattern.SetValue(text)` and Win32 `keybd_event`.
4. **AST Code Integrity**: Generated code is parsed by `ast.parse` in memory; syntax errors abort execution before touching the disk.
