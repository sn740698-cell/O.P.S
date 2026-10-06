# 🧠 O.P.S. — Over-Engineered Programmed System

> **A Local-First Agentic AI Operating System that can hear, see, think, search, code, automate, and remember your digital world.**

O.P.S. is an **ambient, multimodal, agentic AI operating system** that transforms your workstation into a J.A.R.V.I.S.-class command cockpit. Built with a **'90s retro tactical Iron Man HUD aesthetic** (Crimson Red, Jet Black, Steel Gray, and Pure White), O.P.S. coordinates local lightweight LLMs, live autonomous web crawling, universal OS and DOM automation, persistent conversational multi-turn session memory, and a persistent PostgreSQL memory vault under a strict safety gatekeeper.

---

## 🌟 Key Architecture & Multi-Agent Hierarchy

```text
                                  [ USER INPUT ]
                                        │
                            [ O.P.S. POP-UP COCKPIT ]
                    (Web Cockpit / Desktop Windows Overlay)
                                        │
                          [ SESSION & CONTEXT MANAGER ]
                  (Contextual pronoun resolution & topic tracking)
                                        │
                         [ PROMPT TEMPLATE AGENT ]
                        (Qwen3 0.6B - Pattern Normalizer)
                                        │
                          [ UNDERSTAND PROMPT / ROUTER ]
                            (Qwen3 1.7B - Global Router)
                                        │
                    ┌───────────────────┴───────────────────┐
                    │ [WEB]                                 │ [AUTOMATION]
                    ▼                                       ▼
         [ WEB SUPERIOR AGENT ]                [ AUTOMATION SUPERIOR AGENT ]
            (Qwen3 1.7B - Superior)                (Qwen3 1.7B - Superior)
                    │                                       │
         [ WEB PROMPT UNDERSTANDING ]           [ AUTO PROMPT UNDERSTANDING ]
                    │                                       │
        ┌───────────┼───────────┐                           │
        ▼           ▼           ▼                           ▼
       [ScrapeGraph][BS4 Parser][Crawlee]               [ HITL APPROVAL GATE ]
        (Llama 3.2) (Qwen 0.6B) (Llama 3.2)             (Deterministic Security)
        └───────────┬───────────┘                           │
                    ▼                                ┌──────┴──────┬──────────┬──────────┐
         [ RETRIEVAL QUALITY AGENT ]                 ▼             ▼          ▼          ▼
           (Qwen3 1.7B - Loop Gate)             [Open Web]    [Installed] [OpenFile] [Desktop]
                    │                            (Playwright)  (PyAutoGUI)  (OS APIs) (PyAutoGUI)
                    │ (If Insufficient -> Loop)      └──────┬──────┴──────────┴──────────┘
                    ▼                                       ▼
                    └───────────────────┬───────────────────┘
                                        │
                                [ RESULT AGENT ]
                      (Qwen3 0.6B - Fact & Result Structurer)
                                        │
                            [ JARVIS PERSONA AGENT ]
                        (Llama 3.2 1B - Neural Persona)
                                        │
                        [ MULTI-TURN CONTEXT STORAGE ]
                                        │
                            [ RETURN TO COCKPIT ]
```

---

## 🚀 Key Features & Architectural Capabilities

### 1. 🤖 Local-First Tri-Model Architecture
Implementation strictly follows [`OPS_Local_LLM_Model_Roles.md`](file:///d:/Projects/O.P.S/OPS_Local_LLM_Model_Roles.md) and [`OPS_COMPLETE_SYSTEM_REFERENCE.md`](file:///d:/Projects/O.P.S/OPS_COMPLETE_SYSTEM_REFERENCE.md):
* **Model 1 — Qwen3 0.6B (Fast Pattern Matcher, HTML Parser & Fact Structurer):**
  * Extremely low latency (`<50ms`).
  * Powers **Prompt Template Agent**, **BeautifulSoup Agent**, **Open File Agent**, and **Result Agent**.
* **Model 2 — Qwen3 1.7B (Global Router, Superior Coordinators & Quality Loop):**
  * Powers **Understand Prompt / Router Agent**, **Web Superior Agent**, **Automation Superior Agent**, **Web Prompt Understanding Agent**, **Automation Prompt Understanding Agent**, and **Retrieval Quality Agent**.
* **Model 3 — Llama 3.2 1B Instruct (Persona Layer & Complex Automators):**
  * Powers **Jarvis Persona Agent**, **ScrapeGraphAI Agent**, **Crawlee Agent**, **Open Web Agent**, **Installed Apps Agent**, and **Desktop Control Agent**.

---

### 2. 💬 Continuous Multi-Turn Conversation Loop (`user :` / `bot :`)
* **Persistent Dialogue Stream:** Both the **Web Cockpit HUD** and the **Desktop Windows Overlay** render a continuous, scrollable multi-turn conversation stream:
  ```text
  user : Open YouTube
  bot  : Done. YouTube is open.
  user : Search for Believer
  bot  : Done. I have searched for 'Believer' on YouTube.
  user : Play it
  bot  : Done. Playing 'Believer'.
  ```
* **Contextual Pronoun Resolution:** Resolves pronouns (*"it"*, *"its"*, *"the first result"*, *"tell me more"*, *"try Documents"*) deterministically without hallucinating random actions.
* **Refresh Button Contract (`[ ↻ REFRESH ]`):** Wipes active conversational RAM context and starts a clean session with a fresh `session_id` while preserving permanent memory vaults (ChromaDB and PostgreSQL).

---

### 3. 🌐 Web Superior Domain & Self-Correcting Quality Loop
* **Distinct Extractors:** ScrapeGraphAI for structured schemas, BeautifulSoup4 for clean HTML, and Crawlee for multi-page crawling.
* **Self-Correcting Quality Gate:** The **Retrieval Quality Agent** validates whether retrieved data fulfills the original objective. If insufficient, it automatically triggers a re-planning cycle back to the Web Prompt Understanding Agent (up to 2 retries) before passing facts to the Result Agent.

---

### 4. 🖱️ Automation Superior Domain & Pre-Execution HITL Gate
* **Specialist Sub-Agents:**
  * **Open Web Agent:** Controls browser web applications (Instagram Reels, YouTube search, Gemini, Claude, DOM actions) via Playwright.
  * **Installed Apps Agent:** Launches and interacts with native desktop software (VLC, Spotify, WhatsApp, VS Code, Calculator) via PyAutoGUI.
  * **Open File Agent:** Resolves and opens files/folders (Downloads, PDFs, project folders) and accurately reports missing paths.
  * **Desktop Control Agent:** Executes desktop operations (creating folders/files, notes, move, rename, system actions).
* **Mandatory Human-in-the-Loop Gate:** Intercepts action plans **before** low-level tool execution. Halts cleanly with 0 actions performed if declined.

---

### 5. 🎛️ 3-Tab Tactical Iron Man HUD Cockpit
* **Tab 01: [ 01: COMMAND COCKPIT ]**
  * **Ops Heart:** High-performance WebGL plasma brain with rhythmic synaptic pulses and electric shockwaves.
  * **Tri-Model Status:** Live telemetry for Qwen 0.6B, Qwen 1.7B, and Llama 3.2 1B.
  * **Briefing Card & Terminal Console:** Continuous multi-turn chat stream with Piper TTS speech synthesis and live sandbox log feed.
* **Tab 02: [ 02: LIVE ORCHESTRATION & AGENTS ]**
  * Live neural synaptic network animating all 14 agents and the amber quality loop in real time during directive execution.
  * Interactive benchmark presets for Web and Automation domains.
* **Tab 03: [ 03: MY WORKSTATION MEMORIES ]**
  * PostgreSQL memory vault with quick-capture and automatic playback actions.

---

### 6. 🎧 '90s Retro Audio Synthesizer
* **Client-Side Web Audio Engine ([`retroSounds.js`](file:///d:/Projects/O.P.S/frontend/src/utils/retroSounds.js)):**
  * Real-time synthesized acoustic chimes for cockpit appearance, disappearance, memory purge, and telemetry pulses.
* **Native Workstation Audio ([`local_agent/sounds/`](file:///d:/Projects/O.P.S/local_agent/sounds/)):**
  * 16-bit 44.1 kHz PCM audio files (`cockpit_appear.wav`, `cockpit_disappear.wav`, `memory_added.wav`) played through Windows speakers.

---

## 🛠️ Tech Stack & Database Architecture

| Layer | Technology |
| :--- | :--- |
| **Frontend Cockpit** | React 18, Vite, Tailwind CSS, Lucide Icons, WebGL Plasma Shader, Web Audio API |
| **Backend Core** | Django 5, ASGI Channels (WebSockets), Django REST Framework |
| **Multi-Agent Orchestration** | LangGraph, LangChain, Pydantic |
| **Local LLM Models** | Ollama (`qwen:0.6b`, `qwen:1.7b`, `llama3.2:1b`) |
| **Web Crawling & Extraction** | Crawlee, ScrapeGraphAI, BeautifulSoup4, Playwright |
| **Desktop Automation** | PyAutoGUI, Windows Win32 APIs, PowerShell `Get-StartApps`, `winsound` |
| **Relational Database** | **PostgreSQL 18 (`ops_db`)** for Workstation Memories & Audit Logs |
| **Vector Database** | ChromaDB (`ops_codebase` and `ops_chatbot_memory`) |
| **Speech & Voice** | Wispr Flow (`Ctrl + Win`), Faster-Whisper, Piper TTS |

---

## ⚡ Quick Start Guide (Windows)

### 1. 1-Click Launch
Double-click **`start_ops.bat`** in the project root to automatically start:
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

## 📄 Validation & Audit Report
For the complete architectural validation matrix, consult [`OPS_VALIDATION_REPORT.md`](file:///d:/Projects/O.P.S/OPS_VALIDATION_REPORT.md).

## 📄 License
Distributed under the **MIT License**. Built for privacy-first, local-first AI productivity.
