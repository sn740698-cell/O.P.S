# 🧠 O.P.S. — Over-Engineered Programmed System

> **A Local-First Agentic AI Operating System that can hear, see, think, search, code, automate, and remember your digital world.**

O.P.S. is an **ambient, multimodal, agentic AI operating system** that transforms your workstation into a J.A.R.V.I.S.-class command cockpit. Built with a **'90s retro tactical Iron Man HUD aesthetic** (Crimson Red, Jet Black, Steel Gray, and Pure White), O.P.S. coordinates local lightweight LLMs, live autonomous web crawling, universal OS and DOM automation, conversational session memory, and a persistent PostgreSQL memory vault under a strict safety gatekeeper.

---

## 🌟 Key Architecture & Upgrades Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                      O.P.S. AMBIENT OPERATING ENVIRONMENT                   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                Voice / Hotkeys / Text / Camera / Screen
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │               UNIFIED USER SURFACES & SYSTEM-WIDE OVERLAYS                │
 ├─────────────────────────────────────┬─────────────────────────────────────┤
 │ • 90s Tactical HUD (React + Vite)   │ • System-Wide Pop-Up Cockpit        │
 │   - Tab 01: [ Command Cockpit ]     │   - Global Hotkey: Ctrl + Alt       │
 │   - Tab 02: [ Live Orchestration ]  │   - Disappear: Ctrl + Alt + Space   │
 │   - Tab 03: [ Workstation Memories ]│   - Wispr Voice: Ctrl + Win         │
 │ • Ambient Floating Avatar Cockpit   │ • Frameless Always-On-Top Overlay   │
 └─────────────────────────────────────┴─────────────────────────────────────┘
                                       │
                         Bidirectional WebSocket Events
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                       CENTRAL DJANGO BACKEND ENGINE                       │
 │        Async Channels WebSockets • REST APIs • Safety Gatekeeper          │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                TRI-MODEL LANGGRAPH MULTI-AGENT ORCHESTRATOR               │
 ├───────────────────────────────────────────────────────────────────────────┤
 │ 1. Fast Intent Router (<50ms):         Qwen3 0.6B                         │
 │ 2. Reasoning, Planning & Developer:    Qwen3 1.7B + Codebase RAG          │
 │ 3. Content Specialist & J.A.R.V.I.S.:  Llama 3.2 1B Instruct              │
 │ 4. Autonomous Web Crawling Agent:      Crawlee + ScrapeGraphAI Pipeline   │
 │ 5. Browser Automation Agent:           Playwright Universal DOM Engine    │
 │ 6. Physical OS Automation Agent:       PyAutoGUI Keyboard & Mouse Macros  │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
┌───────────────┐              ┌───────────────┐              ┌───────────────┐
│ TEMPORARY CHAT│              │ CHATBOT VECTOR│              │  POSTGRESQL 18│
│    MEMORY     │              │   DATABASE    │              │  MEMORY VAULT │
│ (Session RAM) │              │  (ChromaDB)   │              │   (ops_db)    │
├───────────────┤              ├───────────────┤              ├───────────────┤
│ Contextual    │              │ Isolated      │              │ Persistent    │
│ Pronoun &     │              │ partition:    │              │ workstation   │
│ Follow-Up     │              │ ops_chatbot_  │              │ memories      │
│ Resolution    │              │ memory        │              │ (songs, reels)│
└───────────────┘              └───────────────┘              └───────────────┘
```

---

## 🚀 All Upgrades & New Capabilities

### 1. 🤖 Local-First Tri-Model Architecture
Implementation strictly follows [`OPS_Local_LLM_Model_Roles.md`](file:///d:/Projects/O.P.S/OPS_Local_LLM_Model_Roles.md):
* **Model 1 — Qwen3 0.6B (Fast Router & Intent Classifier):**
  * Extremely low latency (`<50ms`).
  * Classifies prompts into: `SYSTEM_COMMAND`, `MEDIA_CONTROL`, `WORKSTATION_MEMORY_CAPTURE`, `WORKSTATION_MEMORY_RECALL`, `WEB_SEARCH`, `CONTENT_CREATION`, `CODE_DEVELOPMENT`, or `REASONING_PLANNER`.
* **Model 2 — Qwen3 1.7B (Deep Reasoning, Planning & Developer Agent):**
  * Analyzes complex multi-step directives.
  * Formulates structured execution plans and writes verified Python/JavaScript code.
* **Model 3 — Llama 3.2 1B Instruct (Persona Layer & Content Specialist):**
  * Unifies the system voice with the polite, capable J.A.R.V.I.S. personality.
  * Crafts structured bullet-point responses, summaries, and correspondence.

---

### 2. 🌐 Autonomous Web Crawling Pipeline (Crawlee & ScrapeGraphAI)
* Pure informational and live research queries (*"Who is Brad Pitt?"*, *"Latest quantum computing theories"*, *"Live news"*) are routed to the **Web Crawling Agent**.
* Integrates **Crawlee** and **ScrapeGraphAI** to extract clean, ad-free markdown dossiers without triggering unwanted desktop browser popups.
* Automatically synthesizes spoken briefings dispatched through the local **Piper TTS** voice pipeline.

---

### 3. 🖱️ Universal Physical OS & DOM Automation
* **Any Website on Earth:** Supports natural language DOM search across 40+ pre-mapped platforms (Google, YouTube, Instagram, Spotify, Netflix, Amazon, Reddit, GitHub, Wikipedia, etc.) and dynamically resolves any custom web address.
* **Application Control:** Launches any Windows Start Menu application, executable binary, control panel applet, or browser deep link.
* **Developer Routines:** Supports custom scripted routines like navigating to `D:\freellmapi`, executing `npm run dev`, and launching the Claude CLI automatically.
* **VS Code & Filesystem Integration:** Resolves file paths, opens workspaces in VS Code, and navigates directories.

---

### 4. 🧠 Multi-Tier Memory Engine

#### A. Temporary Chat Session Memory (RAM)
* Retains conversational turns only during the active browser session.
* Seamlessly resolves contextual follow-ups and pronouns (*"him"*, *"her"*, *"it"*, *"that"*, *"tell me more"*).
* Completely purged on page refresh or when clicking the **`[ ↺ ERASE MEMORY ]`** button with authentic retro degauss sound effects.

#### B. Dedicated Chatbot Vector Database (ChromaDB)
* Isolated vector collection **`ops_chatbot_memory`** strictly partitioned away from project codebase RAG (`ops_codebase`).
* Enables semantic relevance search across recent dialogue history.

#### C. Persistent Workstation Memory Vault (PostgreSQL 18 `ops_db`)
* **Dynamic Capture:** When viewing any YouTube song, Instagram reel, Google search, or application, simply say:
  > *"add it to this, my memory, this is my favorite song"*
  * O.P.S. captures the label, category, active window title, and target URL, committing it permanently into PostgreSQL (`ops_db`).
* **Dynamic Recall & Automatic Playback:** Command:
  > *"Add my favorite song from the memory"* *(or "Play my favorite song from memory")*
  * O.P.S. retrieves the record from PostgreSQL, navigates directly to the window/URL, and initiates automatic playback.
* **Sound Feedback:** Every memory capture triggers an authentic '90s cybernetic data-lock chime across speakers and HUD.

---

### 5. 🎛️ 3-Tab Tactical Iron Man HUD Cockpit

* **Tab 01: [ 01: COMMAND COCKPIT ]**
  * Central JARVIS command console with retro typewriter streaming.
  * Real-time WebSocket connectivity status (Agent, Permissions, Terminal, Mobile).
  * Glowing animated Arc Reactor Core representing multi-model brain telemetry.
  * Terminal console and live web research stream.
* **Tab 02: [ 02: LIVE ORCHESTRATION & AGENTS ]**
  * Live model-to-agent mapping inspector showing which local LLM runs each agent.
  * Real-time LangGraph workflow visualizer with active agent indicators.
  * Temporary conversation session inspector and vector DB partition status.
* **Tab 03: [ 03: MY WORKSTATION MEMORIES ]**
  * Complete personal memory vault dashboard backed by PostgreSQL 18.
  * Starts with a clean 0-memory state and clear interactive guidance.
  * Tactical cards for each memory with **`[ ▶ PLAY / OPEN NOW ]`** and **`[ 🗑 DELETE MEMORY ]`** controls.
  * Quick-memorize console form to commit any active window or custom media on demand.

---

### 6. 🎧 '90s Retro Audio Synthesizer
* **Client-Side Web Audio Engine ([`retroSounds.js`](file:///d:/Projects/O.P.S/frontend/src/utils/retroSounds.js)):**
  * Zero-latency acoustic chimes for cockpit appearance (`playAppear`), disappearance (`playDisappear`), memory purge (`playMemoryErase`), memory store (`playMemoryStore`), and memory execution (`playMemoryExecute`).
* **Native Workstation Audio ([`local_agent/sounds/`](file:///d:/Projects/O.P.S/local_agent/sounds/)):**
  * High-fidelity 16-bit 44.1 kHz PCM audio files (`cockpit_appear.wav`, `cockpit_disappear.wav`, `memory_added.wav`) played through Windows speakers via `winsound`.

---

## 🔮 Upcoming Upgrades Roadmap

As the architect of O.P.S., here are the next major upgrades planned for future releases:

1. **Local Vision Model Integration (Qwen2-VL 2B / 7B):**
   * Direct visual desktop understanding without relying on OCR or bounding-box heuristics.
   * Enables the agent to inspect canvas elements, complex desktop games, and GUI dialogs visually.
2. **On-Device Whisper Fine-Tuning:**
   * Transition from cloud/hybrid STT to an offline quantized `faster-whisper-medium` running with CUDA acceleration.
3. **Autonomous Tool Synthesizer (Zero-Shot MCP Generation):**
   * When encountering an unmapped application or CLI, the Developer Agent will dynamically generate, test, and register a new Model Context Protocol (MCP) server in seconds.
4. **Multi-Workstation Mesh Telemetry (Tailscale P2P):**
   * Link multiple PCs, laptops, and Android devices into a unified O.P.S. cluster with shared clipboard and cross-device memory recall.
5. **Self-Healing Code Sandbox:**
   * Execution loop where errors in generated scripts are automatically diagnosed by the Debugger Agent, patched, and re-executed until verified.
6. **Smart Media Ducking & Interception:**
   * When speaking voice commands, O.P.S. will automatically duck system background audio (Spotify/YouTube) for crisp microphone transcription.

---

## 🛠️ Tech Stack & Database Architecture

| Layer | Technology |
| :--- | :--- |
| **Frontend Cockpit** | React 18, Vite, Tailwind CSS, Lucide Icons, Framer Motion, Web Audio API |
| **Backend Core** | Django 5, ASGI Channels (WebSockets), Django REST Framework |
| **AI Orchestration** | LangGraph, LangChain, Pydantic |
| **Local LLMs** | Ollama (`qwen:0.6b` / `qwen:1.7b` / `llama3.2:1b`) |
| **Web Crawling** | Crawlee, ScrapeGraphAI, Playwright |
| **Desktop Automation**| PyAutoGUI, Windows PowerShell `Get-StartApps`, `winsound` |
| **Relational Database**| **PostgreSQL 18 (`ops_db`)** for Workstation Memories & Audit Logs |
| **Vector Database** | ChromaDB (`ops_codebase` and `ops_chatbot_memory`) |
| **Speech & Voice** | Wispr Flow (`Ctrl + Win`), Faster-Whisper, Piper TTS |

---

## ⚡ Quick Start Guide (Windows)

### 1. 1-Click Launch
Double-click **`start_ops.bat`** in the project root!
It automatically checks and initializes:
1. **PostgreSQL 18 Engine** on port `5432` (`ops_db`).
2. **Django Backend Engine** on `http://127.0.0.1:8000`.
3. **React Cockpit HUD** on `http://localhost:3000`.
4. **Desktop Overlay Daemon** on global hotkeys (`Ctrl + Alt`).

---

### 2. Manual Startup
```bash
# 1. Start PostgreSQL 18
"D:\Program Files\program Files (postgreSQL)\18\bin\postgres.exe" -D "D:\Program Files\program Files (postgreSQL)\18\data"

# 2. Start Django Backend
cd backend
.\venv\Scripts\activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# 3. Start React Frontend
cd frontend
npm install
npm run dev

# 4. Start Desktop Overlay Daemon
python local_agent\desktop_overlay.py
```

---

## 📄 License
Distributed under the **MIT License**. Built for privacy-first, local-first AI productivity.
