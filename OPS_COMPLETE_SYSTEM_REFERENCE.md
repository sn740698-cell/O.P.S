# O.P.S. (Over-Engineered Programmed System)
## Complete Architectural & Features Reference Guide

---

## 1. Executive Summary & Vision

**O.P.S.** is a local-first, ambient autonomous Artificial Intelligence Operating System engineered to run directly on your workstation. Inspired by **J.A.R.V.I.S.** from *Iron Man*, O.P.S. does not merely act as an isolated chatbot in a browser tab—it is deeply embedded into your operating system environment. 

With a single global keystroke (`Ctrl + Alt`) or an ambient wake-word (`"Hey OPS"`), O.P.S. appears instantly over any active window (VS Code, Chrome, Terminal, Games, or Desktop). It uses a local Tri-Model cognitive pipeline powered by **Ollama**, allowing specialized sub-agents to browse documentation, execute shell builds, write and refactor code, interact with desktop GUI controls, and report back in a calm, dignified, and polite J.A.R.V.I.S. persona with an authentic **'90s retro typewriter streaming animation**.

---

## 2. Comprehensive Catalog of Built Features

### 🎮 A. Ambient Workstation Interaction & Windows Desktop Overlay
1. **Global System-Wide Hotkey (`Ctrl + Alt`):**
   - Implemented natively via Win32 API (`GetAsyncKeyState`) and Python `keyboard` hooks with active debounce.
   - Summons the floating ambient cockpit from any application without minimizing your workflow.
   - **Unique Starting Acoustic Sound:** Plays a custom synthesized cybernetic chime (`cockpit_appear.wav`) asynchronously on appearance.
2. **Instant Dismissal Hotkey (`Ctrl + Alt + Space`):**
   - Instantly dismisses/hides the Pop-Up Cockpit from anywhere on the system.
   - **Unique Power-Down Acoustic Sound:** Plays a custom synthesized tactical swoop (`cockpit_disappear.wav`) on exit.
3. **Wispr Flow Voice Dictation Hotkey & Indicator (`Ctrl + Windows`):**
   - Pressing `Ctrl + Windows` triggers Wispr Flow voice dictation from anywhere on the OS.
   - **Pop-Up Cockpit Dynamic Indicator:** Real-time visual banner in the cockpit displays `🎙️ [CTRL + WIN]` status, switching dynamically between `[ IDLE ]` and a glowing crimson `[ REC ● ]` `ACTIVE & LISTENING...` state.
   - Can also be clicked directly inside the Pop-Up Cockpit to toggle dictation on/off.
4. **Mandatory Human-in-the-Loop Permission to Open Any Item:**
   - Opening ANY application or website (e.g. Instagram, Calculator, Chrome, LeetCode, terminal commands) strictly requires prior human authorization.
   - The Pop-Up Cockpit immediately surfaces the authorization request:
     `🚨 [AUTHORIZATION REQUIRED: OPEN ITEM] - Open '<ITEM>'`
   - If the user accepts (`[ ✅ ACCEPT / ALLOW ]`), O.P.S. proceeds and opens the item.
   - If the user denies (`[ ❌ DENY / BLOCK ]`), the item remains unopened and O.P.S. reports cancellation.
5. **Universal Website & Application Opener:**
   - Intelligently recognizes any website named by the user (e.g., "Open Instagram", "Open LeetCode", "Launch YouTube").
   - Resolves domains dynamically and requests approval before launching in your native browser.
6. **Ambient Wake-Word Engine ("Hey OPS"):**
   - Continuous background acoustic listener configured for `"Hey OPS"` (and phonetic variants).
   - Automatically surfaces the overlay window and primes the prompt input field when spoken.
7. **'90s Retro Typewriter Streaming Animation:**
   - Real-time word-by-word streaming effect running at 22ms intervals.
   - Authentic retro terminal monospace typography (`Consolas`) rendered in silver-white on pitch-black.
   - Features an animated, blinking block cursor (`█`) that pulses smoothly.
   - Includes **instant skip-on-click**: clicking the response box immediately reveals the entire text.
8. **Frameless Draggable Cyber HUD:**
   - Frameless, always-on-top, alpha-blended (`0.96` opacity) floating overlay with a glowing Crimson Red border.
   - Smooth title-bar drag-and-drop repositioning anywhere across multi-monitor setups.

---

### 🧠 B. Local-First Tri-Model Cognitive Engine (Ollama)
O.P.S. strictly applies the architectural rule: *"Use the smallest model that can reliably complete the current stage of the task."*

1. **Model 1: Qwen3 0.6B / Qwen2.5 3B — Fast Router & Intent Detection:**
   - Runs in `<50ms` on CPU/GPU.
   - Identifies intents: `OPEN_APPLICATION`, `OPEN_WEBSITE`, `WEB_SEARCH`, `FILE_OPERATION`, `SYSTEM_COMMAND`, `DEVELOPMENT`, `DEBUGGING`, `CONTENT_GENERATION`, `CONVERSATION`.
   - Determines task `complexity` (`simple` vs `complex`).
   - Extracts essential parameters (application name, URLs, search queries, file paths).
   - **Fast-Path Bypass:** Routes simple commands straight to tools, skipping heavier models completely.
2. **Model 2: Qwen3 1.7B / DeepSeek-R1 7B — Main Reasoning & Planning Model:**
   - Handles deep technical reasoning, task decomposition, and multi-step execution plans.
   - Powers the **Developer Agent** for code generation, syntax validation, and refactoring.
   - Powers the **Debugger Agent** for analyzing crash logs, stack traces, and suggesting fixes.
   - Coordinates sub-agent task distribution across files, terminal, and browser.
3. **Model 3: Llama 3.2 1B Instruct — Conversation, Content & J.A.R.V.I.S. Persona:**
   - High-quality instruction-following for drafting emails, formal letters, documentation, and technical summaries.
   - **Shared O.P.S. Personality Layer:** Translates raw tool execution logs into calm, articulate, dignified, and polite responses (*"Certainly, sir. Chrome is open and ready."*).

---

### 🤖 C. LangGraph Multi-Agent Orchestration Engine
A directed acyclic state graph (`StateGraph`) governing autonomous collaboration:
1. **Supervisor Router Node:** Classifies directives, decomposes goals, and determines execution paths.
2. **Developer Agent Node:** Queries codebase RAG, generates code, and scaffolds file projects.
3. **Browser Agent Node:** Automates Playwright, crawls web documentation, and performs live searches.
4. **System Automation Agent Node:** Controls desktop GUI coordinates and launches desktop apps & websites.
5. **Synthesizer / J.A.R.V.I.S. Exit Node:** Consolidates multi-agent telemetry and generates the user briefing.

---

### 🛡️ D. Tool Sandbox & Human-in-the-Loop Security Gatekeeper
1. **Sandboxed File Operations:**
   - Safe file reader with slice notation (e.g. read lines 10 to 50 without loading massive files).
   - Safe file writer with overwrite safeguards and path validation.
2. **Safe Terminal Runner:**
   - Non-interactive shell execution with strict timeout controls.
   - Blacklist enforcement: automatically blocks destructive commands (e.g., `rm -rf /`, `format`, `del /f /s /q C:\Windows`).
3. **Interactive Security Approval System:**
   - High-risk operations prompt real-time approval modals in both Web Cockpit and Desktop Overlay (`ALLOW_ONCE`, `ALLOW_TASK`, `DENY`).
4. **Execution Audit Logging:**
   - Every agent command, tool invocation, exit code, and stdout/stderr snippet is permanently recorded in SQLite.

---

### 🌐 E. Live Web Scraping & Browser Automation
1. **Headless Browser Automation (Playwright):** Launches controlled browser instances for DOM extraction and page interaction.
2. **Crawl4AI & ScrapeGraphAI Integration:** Converts raw HTML web pages into clean, LLM-ready markdown.
3. **Live Web Search:** Built-in multi-engine search aggregator for finding real-time documentation and code snippets.

---

### 🖥️ F. Cyber Web Cockpit HUD (`frontend/`)
The web cockpit features 3 dedicated pages with a strict **Crimson Red (`#dc2626`), Pure White (`#ffffff`), Pitch Black (`#09090b`), and Zinc Gray (`#27272a`)** retro HUD palette:

1. **Tab 1: Mission Control & Ambient Telemetry:**
   - **Ops Heart (The Living Neural Brain of O.P.S.):**
     - Positioned in the right-top corner of the main dashboard.
     - Custom high-performance WebGL shader rendering an organic, animated red/black/white/gray plasma brain.
     - Always moving and rotating smoothly in real-time with rhythmic synaptic heartbeat pulses, breathing lumpy silhouette, domain-warped glowing filaments, and drifting embers.
     - Fully interactive in 3D: drag to rotate, click/tap to discharge an electric shockwave pulse with telemetry counter.
   - Tri-Model Status Dashboard tracking health, active role, and Ollama connection for all 3 models.
   - Real-Time Command Core with quick directives (`[ OPEN INSTAGRAM ]`, `[ OPEN LEETCODE ]`, `[ SYSTEM HEALTH ]`, `[ SEARCH WEB ]`).
   - Real-time WebSocket connectivity ribbon for `/ws/agent/`, `/ws/permissions/`, `/ws/terminal/`, and `/ws/mobile/`.
   - Executive synthesis briefing card with typewriter response streaming.
   - Interactive terminal console & live browser intelligence feed.
2. **Tab 2: Live Agent Orchestration Canvas (`ORCHESTRATION ENGINE v0.1`):**
   - Faithful retro pixel-art architecture canvas inspired by tactical HUD diagrams:
     - `ENVIRONMENT v1.0`: User at dual-monitor workstation with query speech bubbles, sensor panel (`Ctrl+Alt`), and J.A.R.V.I.S. robot agent avatar.
     - `PERCEPTION ENGINE`: Multimodal inputs (`IMAGE` via `minicpm-v:8b`, `DOC` via DOM/files, `INPUT_DATA` via prompt).
     - `DECISION CORE`: Long-term `Memory` (`ChromaDB`) and `Knowledge` (Local RAG).
     - `ORCHESTRATION LOGIC`: Supervisor Brain (`qwen2.5:3b`) connected to Deep Reasoner (`deepseek-r1:7b`) with live animated neural network graph.
     - `ACTION OUTPUT`: `TEXT` (typewriter/TTS) and `TOOLS` (app launcher, shell execution).
     - Active circulating signal feedback loop returning to agent.
     - Interactive benchmark bar with one-click multi-agent pipeline simulations.
3. **Tab 3: Application Features Dashboard (`APPLICATION FEATURES DASHBOARD`):**
   - Pixel-art node matrix with central glowing Brain Node and connecting signal buses:
     - `FEATURE 1: SMART SEARCH & FILTER` (magnifier and filter funnel)
     - `FEATURE 2: REAL-TIME ANALYTICS` (performance bar chart with rising trend)
     - `FEATURE 3: CLOUD SYNC` (bidirectional cloud synchronization)
     - `FEATURE 4: AUTOMATED REPORTING` (automated PDF reports)
     - `FEATURE 5: COLLABORATION TOOLS` (HITL security permissions team)
     - `FEATURE 6: AUTOMATED REPORTING / TASKS` (chat automation)
     - `FEATURE 7: API INTEGRATION HUB` (REST & WebSocket connectors)
     - Glowing Red CRT Telemetry Monitor (`STATUS: ALL SYSTEMS GO`) updating dynamically on node interaction.

---

## 3. Technology Stack Reference: Where & Why

The following table lists **every technology, framework, and Python library** used in O.P.S., exactly where it is utilized in the codebase, and the architectural rationale for its inclusion:

### 🐍 Python Backend & AI Stack

| Technology / Library | Where It Is Used in O.P.S. | Why We Are Using It (Architectural Rationale) |
|---|---|---|
| **Python 3.12+** | Core runtime for backend and desktop overlay | Universal standard for AI engineering, native async support, and rich AI ecosystem. |
| **Django 5.0+** | `backend/ops_backend/settings.py`, `backend/ops_core/` | Provides enterprise-grade ORM, database migrations, security configurations, and REST views. |
| **Django REST Framework** | `backend/ops_core/views.py` | Exposes clean, serialized HTTP REST endpoints for agent execution, health checks, and tool APIs. |
| **Channels 4.0+** | `backend/ops_backend/asgi.py`, `ops_core/consumers.py` | Upgrades standard Django to handle asynchronous full-duplex WebSockets for real-time telemetry streaming. |
| **Daphne** | `backend/ops_backend/asgi.py` | High-performance ASGI HTTP/WebSocket server that runs Django Channels in production. |
| **Ollama Python SDK** | `backend/ops_core/services/ollama_service.py` | Communicates directly with local GGUF models running in Ollama with zero cloud latency. |
| **LangGraph** | `backend/ops_core/services/agent_orchestrator.py` | Implements cyclic state graphs and conditional branching for multi-agent coordination. |
| **LangChain Core** | `backend/ops_core/services/agent_orchestrator.py` | Supplies structured prompt templates, runnables, and output parsers. |
| **ChromaDB** | `backend/ops_core/services/session_memory.py`, `tool_sandbox.py` | Embedded vector database for storing and querying codebase embeddings and long-term conversation memory. |
| **Sentence-Transformers** | `backend/ops_core/services/session_memory.py` | Generates fast local dense vector embeddings (`all-MiniLM-L6-v2`) without third-party API dependencies. |
| **Playwright** | `backend/ops_core/services/scraping_service.py`, `automation_service.py` | Headless Chromium automation for scraping dynamic JavaScript-heavy websites and taking screenshots. |
| **Crawl4AI / ScrapeGraph** | `backend/ops_core/services/scraping_service.py` | AI-native web crawler that transforms messy web DOM structures into clean markdown for local LLMs. |
| **PyAutoGUI** | `backend/ops_core/services/automation_service.py` | Cross-platform desktop GUI automation: controls mouse clicks, keyboard typing, and window switching. |
| **SpeechRecognition** | `local_agent/desktop_overlay.py` | Background acoustic microphone listener for detecting the `"Hey OPS"` wake phrase. |
| **Piper TTS** | `backend/ops_core/services/voice_service.py` | Ultra-fast, lightweight, offline neural text-to-speech synthesis running locally on CPU. |
| **Faster-Whisper** | `backend/ops_core/services/voice_service.py` | Highly optimized local automatic speech recognition (ASR) engine for voice transcription. |
| **SQLite / PostgreSQL** | `backend/ops_db.sqlite3`, `settings.py` | Zero-configuration local database storing session memory, audit logs, and permission rules. |
| **Pydantic v2** | `backend/ops_core/services/ollama_service.py` | High-speed data validation and JSON schema enforcement for model inputs and tool outputs. |
| **Python-Dotenv** | `backend/ops_backend/settings.py` | Loads environment configurations (`OLLAMA_HOST`, model tags) cleanly from `.env`. |

---

### 💻 Windows Native & Desktop Integration Stack

| Technology / Library | Where It Is Used in O.P.S. | Why We Are Using It (Architectural Rationale) |
|---|---|---|
| **Tkinter** | `local_agent/desktop_overlay.py` | Standard Python GUI toolkit used to create the frameless, always-on-top, draggable ambient overlay window without heavy webview overhead. |
| **ctypes & Win32 API (`user32.dll`)** | `local_agent/desktop_overlay.py` | Calls native Windows `GetAsyncKeyState` for fail-safe, operating-system-level `Ctrl + Alt` and `Ctrl + Alt + Space` capture across all third-party software. |
| **Keyboard** | `local_agent/desktop_overlay.py` | Cross-application global key listener for rapid hotkey dispatching (`Ctrl+Alt`, `Ctrl+Alt+Space`, `Ctrl+Shift+K`). |
| **winsound & wave** | `local_agent/desktop_overlay.py`, `local_agent/sounds/` | Asynchronous low-latency sound synthesis and playback for HUD appearance and disappearance acoustic cues. |
| **urllib.request / json** | `local_agent/desktop_overlay.py` | Built-in zero-dependency HTTP client for streaming agent requests between the overlay daemon and Django backend. |
| **re (Regular Expressions)** | `local_agent/desktop_overlay.py` | Splits text into tokens while preserving whitespace to enable rhythmic '90s typewriter animation. |

---

### ⚛️ Frontend Cockpit Web Stack

| Technology / Library | Where It Is Used in O.P.S. | Why We Are Using It (Architectural Rationale) |
|---|---|---|
| **React 18** | `frontend/src/App.jsx`, `components/` | Component-based reactive UI framework powering the cockpit, real-time telemetry ribbons, and feeds. |
| **Vite 5** | `frontend/vite.config.js` | Next-generation build tool and dev server providing near-instant hot module replacement (HMR) and fast bundling (<3s). |
| **Tailwind CSS 3** | `frontend/src/index.css`, `tailwind.config.js` | Utility-first styling framework enabling the Crimson Red, Pure White, Pitch Black, and Zinc Gray cyber aesthetic. |
| **Web Audio API** | `frontend/src/utils/retroSounds.js` | Generates procedural 8-bit / retro synthesizer audio in the browser for tab transitions and node interactions. |
| **Lucide React** | All frontend components | High-performance, clean, futuristic SVG icon system representing agents, tools, terminals, and hardware states. |
| **Native WebSockets API** | `frontend/src/App.jsx` | Connects directly to Daphne/Channels endpoints (`/ws/agent/`, `/ws/terminal/`) for zero-lag streaming updates. |

---

## 4. End-to-End Execution Flowchart

```
1. USER ACTION
   • Press [ Ctrl + Alt ] on Windows (Acoustic Chime: cockpit_appear.wav)
   • OR Type directive into Web HUD
       │
2. DISPATCH
   • Overlay or Web HUD sends POST /api/v1/agent/run/ with user prompt
       │
3. ROUTING (Model 1: Qwen3 0.6B / Qwen2.5 3B)
   • Evaluates intent and complexity in <50ms
   • Decides between DIRECT_TOOL, CONTENT_GENERATOR, or REASONING_PLANNER
       │
   ├─► IF Simple Tool (e.g., "Open Instagram", "Open Chrome", "Open LeetCode"):
   │   • Resolves domain dynamically and launches browser or native desktop app
   │   • Skips reasoning model completely
   │
   ├─► IF Content Writing (e.g., "Draft an email"):
   │   • Directly calls Model 3 (Llama 3.2 1B Instruct) for drafting
   │
   └─► IF Complex Task (e.g., "Build a React component"):
       • Routes to Model 2 (Qwen3 1.7B / DeepSeek-R1 7B) in LangGraph
       • Decomposes task into sequential steps
       • Invokes Developer Agent (Codebase RAG + Terminal execution)
       • Invokes Browser Agent (Playwright web scraping)
       │
4. HUMAN-IN-THE-LOOP (IF HIGH RISK)
   • Surfaces approval dialog directly on Pop-Up Cockpit & Web Cockpit
   • User selects [ ✅ ACCEPT / ALLOW ] or [ ❌ DENY / BLOCK ]
       │
5. J.A.R.V.I.S. PERSONALITY LAYER (Model 3: Llama 3.2 1B Instruct)
   • Consolidates execution results and outputs
   • Formulates calm, dignified response: "Certainly, sir. Operations completed."
       │
6. REAL-TIME STREAMING
   • Streams response character-by-character / word-by-word with retro '90s typewriter animation █
   • Press [ Ctrl + Alt + Space ] to dismiss overlay with power-down swoop sound
```

---

## 5. How to Run the Complete System

### 1. Launch the Backend API & WebSocket Server
```powershell
cd d:\Projects\O.P.S\backend
.\venv\Scripts\python.exe -m uvicorn ops_backend.asgi:application --host 0.0.0.0 --port 8000
```

### 2. Launch the Web Cockpit HUD (Frontend)
```powershell
cd d:\Projects\O.P.S\frontend
npm run dev
```
*Open `http://localhost:5173` in your browser.*

### 3. Launch the Windows Desktop Overlay (`Ctrl + Alt`)
```powershell
cd d:\Projects\O.P.S
.\backend\venv\Scripts\python.exe .\local_agent\desktop_overlay.py
```

*Press `Ctrl + Alt` to summon O.P.S. and `Ctrl + Alt + Space` to dismiss!*

---

## 6. Universal Workstation, Web & Command Protocols

### 1. Universal Website & DOM Search Engine (ANY Website on Earth)
* **Zero Hardcoded Limits:** Operates dynamically across all websites, e-commerce stores, streaming platforms, coding hubs, research portals, social networks, and arbitrary domains.
* **Universal Parsing:** Intelligently extracts `(website, query)` regardless of phrasing:
  - `"Go to <site> and search for <query>"`
  - `"Search for <query> in/on/at <site>"`
  - `"In <site> search <query>"`
  - `"Search on <site> for <query>"`
* **Direct Template Resolution & Fallback:**
  - 40+ Pre-optimized platform templates (Google, YouTube, Amazon, Reddit, GitHub, Wikipedia, Netflix, Spotify, Pinterest, eBay, Twitter/X, LinkedIn, Twitch, Bilibili, ArXiv, Medium, etc.).
  - Universal domain resolution for unlisted or custom domains (`<name>` ➔ `https://www.<name>.com`).
* **Autonomous Playwright DOM Interaction:**
  - Navigates to target website with Google Chrome.
  - Deploys a universal selector cascade (`input[type='search']`, `input[name*='search']`, `input[placeholder*='Search']`, `input[aria-label*='Search']`, `input[id*='search']`, `input[role='searchbox']`, etc.) to locate search inputs dynamically.
  - Types the query, presses Enter, captures screenshot previews for the Web HUD, and opens the destination URL in the desktop default browser.

### 2. Universal Installed Application Engine (185+ Applications)
* **Dual Discovery Pipeline:**
  1. PowerShell `Get-StartApps` for packaged Windows Store and UWP applications.
  2. Windows Start Menu shortcut indexing (`%ProgramData%` and `%AppData%` `.lnk` trees) for all win32 desktop software, portable tools, and games.
* **Multi-Strategy Launcher:**
  - `.lnk` shortcuts ➔ `os.startfile(lnk_path)`
  - `.exe` binaries ➔ `subprocess.Popen(exe_path)`
  - UWP AppIDs ➔ `explorer.exe shell:AppsFolder\<AppID>`
  - System PATH CLI tools ➔ `start cmd /k "<tool>"`
  - Web applications ➔ Dynamic URL resolution (`https://www.<app>.com`).

### 3. Universal Command & Terminal Execution
* **Shell Execution:** Executes arbitrary terminal commands (`dir`, `ipconfig`, `git status`, `npm test`, `python script.py`, `docker ps`, etc.) with real-time stdout/stderr WebSocket streaming.
* **Claude Workflow Routine:** Dedicated autonomous sequence for `"run Claude"` (`cd D:\freellmapi && npm run dev` ➔ launch `claude`).
* **VS Code Integration:** Opens files and workspaces on command (`code "<target>"`).
* **File System Operations:** Opens, creates, reads, and edits files and folders across any workstation drive.

### 4. Universal Human-In-The-Loop Safety Gatekeeper Policy
* **Comprehensive Gatekeeping:** Every open application, web search, browser DOM task, file/folder open, VS Code command, and terminal execution is classified as **`HIGH`** risk.
* **Interactive Prompts:** Halts execution until the user explicitly clicks `[ ✅ ACCEPT / ALLOW ]` in either the Pop-Up Cockpit (`Ctrl + Alt`) or Web HUD.
* **Verification:** Validated across all 9 automated tests with 100% passing results (`test_new_automation_features.py`).

