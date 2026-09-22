# 🧠 O.P.S. — Over-Engineered Processing System

> **An AI Operating System that can hear, see, think, search, code, and operate your digital world.**

O.P.S. is a **multimodal, agentic AI operating environment** that connects local AI models, web intelligence, computer automation, developer tools, vision, voice perception, RAG vector memory, Model Context Protocol (MCP), and external cloud AI systems through a **strict permission-controlled interface**.

---

## 🌟 Architectural Overview

O.P.S. acts as an **intelligent orchestration layer between the user and the computer**, structured across 7 major architectural layers:

```text
                         ┌───────────────┐
                         │     USER      │
                         └───────┬───────┘
                                 │
                   Voice / Text / Image / Camera
                                 │
                                 ▼
                    ┌─────────────────────┐
                    │    O.P.S. UI        │
                    │ React + Tailwind    │
                    └──────────┬──────────┘
                               │
                         WebSocket Events
                               │
                               ▼
                    ┌─────────────────────┐
                    │   O.P.S. CORE       │
                    │ Django + Python     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   AI ORCHESTRATOR   │
                    │     LangGraph       │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼──────────────────┐
             │                 │                  │
             ▼                 ▼                  ▼
        Knowledge           Local AI            Agents
          RAG               Ollama                │
       ChromaDB               │          ┌────────┼────────┐
             │                │          ↓        ↓        ↓
             │                │       Browser  Developer Vision
             │                │          ↓        ↓        ↓
             │                │       Research  Coding  Camera
             │                │
             └────────────────┼──────────────────┘
                              │
                              ▼
                       Intelligence
                         Escalation
                              │
                  ┌───────────┼───────────┐
                  ↓           ↓           ↓
                Web      External AI    Human
              Browser     Systems      Clarification
                  │           │           │
                  └───────────┼───────────┘
                              │
                              ▼
                       Permission Engine
                              │
                              ▼
                            MCP
                              │
       ┌──────────────┬───────┼────────┬─────────────┐
       ↓              ↓       ↓        ↓             ↓
   Filesystem      GitHub  Browser  Docker       PostgreSQL
       │              │       │        │             │
       └──────────────┴───────┼────────┴─────────────┘
                              │
                              ▼
                     LOCAL O.P.S. AGENT
                              │
       ┌──────────────┬───────┼──────────┬───────────┐
       ↓              ↓       ↓          ↓           ↓
      OS           Camera  Microphone Clipboard    VS Code
                              │
                              ▼
                     Verify / Audit
                              │
                              ▼
                       O.P.S. UI
                              │
                       Text + Voice
```

---

## ⚡ 1. Intelligence Escalation Engine

Rather than relying on a single AI model, O.P.S. operates via a **7-tier cognitive escalation hierarchy**. It maximizes privacy and latency by starting locally, only escalating to more resource-intensive capabilities when required:

```text
LEVEL 1: Conversation Memory (Active Session State)
    ↓ (If not answered by active conversation state)
LEVEL 2: Project Vector RAG (ChromaDB Code & Document Search)
    ↓ (If query requires project/codebase knowledge)
LEVEL 3: Local Tri-Model Serving (Ollama: Qwen 0.5B / Llama 1B / Qwen Coder 1.5B)
    ↓ (If task requires autonomous multi-agent execution)
LEVEL 4: LangGraph Specialized Multi-Agent Orchestration
    ↓ (If information is missing locally)
LEVEL 5: Web & Browser Automation (Playwright / Crawl4AI)
    ↓ (If local model confidence is low or task is extremely complex)
LEVEL 6: External AI Escalation (Gemini 2.5 / Claude 3.5 / GPT-4o)
    ↓ (If intent remains ambiguous or requires user choice)
LEVEL 7: Human Clarification Modal
```

---

## 🛡️ 2. Execution Safety & Permission Engine

All automated actions (browser navigation, DOM clicks, keyboard/mouse macros, terminal execution, git operations) are strictly gatekept by **Django Backend Security & Permission Engine**:

1. **Safety Whitelist & Regex Filters**: Commands like `rm -rf`, `format`, `drop database`, or `reg delete` are immediately blocked.
2. **Interactive Human-in-the-Loop Popup**: Sensitive operations pause agent execution and stream a permission request over WebSockets to the React UI:

```text
┌──────────────────────────────────────────────────┐
│ 🔐 O.P.S. Permission Required                    │
│                                                  │
│ Action:  Terminal Command Execution             │
│ Command: git push origin main                    │
│ Agent:   Git / Developer Agent                   │
│ Reason:  Deploy completed features to GitHub     │
│                                                  │
│  [ ⛔ DENY ]    [ 🕒 ALLOW ONCE ]   [ ⚡ ALLOW TASK ] │
└──────────────────────────────────────────────────┘
```

3. **Audit Log**: Every approval, denial, and execution event is logged to PostgreSQL for security and traceability.

---

## 📱 3. Mobile Companion Architecture (Bidirectional PC ↔ Phone System)

O.P.S. includes a dedicated **React Native Android Companion App** (`/mobile`) that creates a bidirectional link between your smartphone and your PC:

```text
               ┌─────────────────────────────────┐
               │         O.P.S. BACKEND          │
               │   (Runs heavy LLMs on Laptop)   │
               └────────────────┬────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌──────────────────────────────┐        ┌──────────────────────────────┐
│  1. CONTROLLING YOUR LAPTOP  │        │  2. CONTROLLING YOUR PHONE   │
│         FROM YOUR PHONE      │        │        FROM YOUR LAPTOP      │
├──────────────────────────────┤        ├──────────────────────────────┤
│ • Run terminal commands on PC│        │ • Capture phone camera feed  │
│ • Write & build PC code      │        │ • Inspect phone notifications│
│ • Open browser / web research│        │ • Sync clipboard phone ↔ PC  │
│ • Control VS Code & Docker   │        │ • Vibrate/Alert on approval  │
│ • Take laptop screenshots    │        │ • Record phone microphone    │
└──────────────────────────────┘        └──────────────────────────────┘
```

### Mobile Companion Features:
1. **Persistent Floating Chat Bubble Overlay**: A Messenger-style floating head that stays over any Android app for instant voice/text commands.
2. **Mobile Human-in-the-Loop Gateway**: Approve or deny sensitive PC execution requests (terminal commands, git pushes, script execution) via mobile notifications or popup modals.
3. **Cross-Device Shared Clipboard**: Synchronizes clipboard buffers instantly between phone and desktop.
4. **Mobile Web PWA & Tailscale Remote Access**: Access your desktop O.P.S. cockpit from anywhere over 4G/5G encrypted tunnels.

---

## 🤖 4. Model Suite Strategy

O.P.S. combines lightweight local models with cloud fallback options:

| Role | Selected Model | Target Latency | Function & Responsibilities |
| :--- | :--- | :--- | :--- |
| **Router Model** | `qwen2.5:0.5b` | `< 50ms` | Ultra-fast intent classification & dispatching. |
| **Reasoning Engine** | `llama3.2:1b` | `~150ms` | Context evaluation, multi-step execution graph planning. |
| **Coding & Synthesizer**| `qwen2.5-coder:1.5b`| `~200ms` | Code generation, DOM selector extraction, PyAutoGUI parameter schemas. |
| **RAG Embeddings** | `all-MiniLM-L6-v2` / `nomic-embed-text` | `< 20ms` | Semantic vector search across project files via ChromaDB. |
| **Voice STT** | `Faster-Whisper` | `< 100ms` | High-speed local speech-to-text transcription. |
| **Voice TTS** | `Piper TTS` / `Kokoro-82M` | `< 100ms` | Offline voice synthesis feedback. |
| **Cloud Fallback** | `Gemini 2.5` / `Claude 3.5` / `GPT-4o` | Dynamic | External escalation for high-complexity reasoning or low-confidence vision tasks. |

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, Tailwind CSS, WebSockets |
| **Backend Core** | Django 5, Django Ninja APIs, ASGI Channels |
| **AI Orchestration** | LangGraph, LangChain, Pydantic |
| **Local LLMs** | Ollama (`qwen2.5:0.5b`, `llama3.2:1b`, `qwen2.5-coder:1.5b`) |
| **Vector DB** | ChromaDB, Sentence-Transformers |
| **Voice AI** | Faster-Whisper (STT), Piper / Kokoro (TTS) |
| **Automation** | Playwright, Crawl4AI, PyAutoGUI, Model Context Protocol (MCP) |
| **Mobile App** | React Native Android Companion, `@increase21/rn-floating-bubble` |
| **Database** | PostgreSQL |
| **Deployment** | Docker, Windows 1-Click Batch Launcher |

---

## 📁 Repository Structure

```text
O.P.S/
├── backend/                  # Django REST, Django Ninja & Async WebSockets Engine
│   ├── manage.py             # Django entrypoint
│   ├── ops_backend/          # Core configuration (settings, asgi, urls)
│   ├── ops_core/             # App domain logic, views, models & safety gatekeeper
│   └── requirements.txt      # Backend Python dependencies
│
├── ai/                       # LangGraph Orchestrator & Intelligence Escalation
│   ├── agents/               # Supervisor, Planner, Developer, Researcher, Vision, Tester
│   ├── escalation.py         # 7-Tier Intelligence Escalation Router
│   └── rag/                  # ChromaDB vector store manager
│
├── mcp/                      # Model Context Protocol servers (Filesystem, Git, Terminal, Docker)
├── perception/               # Faster-Whisper STT, Piper TTS & Computer Vision drivers
├── local_agent/              # Host OS desktop integration daemon
│
├── frontend/                 # React 18 + Vite + Tailwind CSS Cockpit Dashboard
│   ├── src/
│   │   ├── components/       # FloatingAvatar, AutomationTerminal, PermissionModal
│   │   ├── hooks/            # useWebSocket, usePermission
│   │   ├── App.jsx           # Main dashboard UI
│   │   └── main.jsx
│   └── package.json
│
├── mobile/                   # React Native Android Companion App
│   ├── package.json          # Floating bubble overlay & draw-overlay dependencies
│   └── App.js                # Mobile companion application entrypoint
│
└── start_ops.bat             # 1-Click Windows Launcher
```

---

## 🔌 API Reference Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health/` | System health check & Ollama model availability status |
| `POST` | `/api/v1/router/` | Route request via `qwen2.5:0.5b` intent router |
| `POST` | `/api/v1/plan/` | Generate multi-step execution plan via `llama3.2:1b` |
| `POST` | `/api/v1/coding/` | Synthesize code or tool parameter schemas via `qwen2.5-coder:1.5b` |
| `POST` | `/api/v1/orchestrate/` | Run full tri-model pipeline end-to-end |
| `POST` | `/api/v1/scrape/` | Trigger web crawling and clean markdown extraction |
| `POST` | `/api/v1/automation/` | Dispatch validated DOM (Playwright) or GUI (PyAutoGUI) action |

---

## 🚀 Quick Start Guide

### ⚡ 1-Click Launcher (Windows)
Double-click **`start_ops.bat`** in the root directory!
It automatically launches:
1. **Django Backend Engine** on `http://localhost:8000`.
2. **React Dashboard Cockpit** on `http://localhost:3000`.

---

### 🛠️ Manual Setup

#### 1. Pull Ollama Models
```bash
ollama pull qwen2.5:0.5b
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:1.5b
```

#### 2. Start Backend Engine
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate      # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

#### 3. Start Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000` to access the O.P.S. Cockpit.

#### 4. Run Mobile Companion (Android)
```bash
cd mobile
npm install
npx react-native run-android
```

---

## 🛣️ Implementation Roadmap

- [x] Initial Repository Architecture & Directory Blueprint
- [x] Django Backend Skeleton & Security Safety Gatekeeper
- [x] Ollama Tri-Model Service Layer (`Qwen 0.5B`, `Llama 1B`, `Qwen Coder 1.5B`)
- [x] Web Scraping (Crawl4AI) & Automation (Playwright / PyAutoGUI) Wrappers
- [x] React 18 + Tailwind CSS Cockpit Dashboard & Ambient Overlay
- [ ] Django Ninja Typed API Service Layer & Channels WebSockets
- [ ] 7-Tier Intelligence Escalation Engine & LangGraph Agent Nodes
- [ ] Interactive Permission Popup Modal with Human-in-the-Loop Gateway
- [ ] ChromaDB Vector RAG integration for long-term project memory
- [ ] Faster-Whisper STT & Piper TTS Perception Subsystem
- [ ] React Native Android companion floating bubble deployment

---

## 📄 License
Distributed under the **MIT License**. Built for privacy-first, developer-centric AI productivity.
