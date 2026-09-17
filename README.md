# O.P.S. (Over-Engineered Programmed System)

> **Local-First, Developer-Focused AI Operating Environment** featuring persistent ambient overlay, 3-model Ollama orchestration, web crawling, OS/DOM automation, and mobile companion.

---

## 🌟 Project Vision & Architectural Overview

O.P.S. is designed as a privacy-centric, low-latency, autonomous local AI operating system. It bridges LLM reasoning with deterministic OS and web automation through a **Strict Execution Safety Gatekeeper**.

Rather than trusting raw LLM output to execute bash/PowerShell commands or GUI actions directly, O.P.S. uses a **Django-managed gatekeeper pipeline** where models generate structured tool intents (JSON) which are validated against security policies before execution.

```text
[ User Input / Ambient Overlay ]
              │
              ▼
[ Django Backend Gatekeeper & API ]
              │
      ┌───────┼───────┐
      ▼       ▼       ▼
┌──────────┐┌──────────┐┌──────────┐
│  Router  ││Reasoning ││  Coding  │  <── Ollama Local Tri-Model Serving
│Qwen 0.5B ││Llama 1B  ││ Qwen 1.5B│
└──────────┘└──────────┘└──────────┘
      │       │       │
      └───────┼───────┘
              ▼
  [ Safety & Schema Validation ]
              │
      ┌───────┴───────┐
      ▼               ▼
┌───────────┐   ┌───────────┐
│ Web Crawl │   │ GUI / OS  │  <── Automation Drivers (Crawl4AI, Playwright, PyAutoGUI)
│ & Scrape  │   │ Control   │
└───────────┘   └───────────┘
```

---

## 🧠 Tri-Model Ollama Serving Strategy

O.P.S. splits cognitive workload across three lightweight, fast, local Ollama models:

| Model Role | Selected Model | Target Latency | Function & Responsibilities |
| :--- | :--- | :--- | :--- |
| **1. Router Model** | `qwen2.5:0.5b` | `< 50ms` | Ultra-fast intent classification (CODING, AUTOMATION, REASONING, CONVERSATION) & dispatching |
| **2. Reasoning Engine** | `llama3.2:1b` | `~150ms` | Context evaluation, multi-step execution graph planning, system state reasoning |
| **3. Coding & Synthesizer**| `qwen2.5-coder:1.5b`| `~200ms` | Code generation, DOM selector extraction, PyAutoGUI parameter extraction |

---

## 🛡️ Execution Safety & Gatekeeper Policy

All automated actions (browser navigation, DOM clicks, keyboard/mouse macros, terminal commands) are strictly gatekept by **Django Backend Security Policy**:

1. **No Direct Execution**: Models are never given shell handles. They only produce JSON schemas.
2. **Whitelist Gatekeeping**: Actions must match approved tool definitions (`web_scrape`, `dom_click`, `gui_click`, `take_screenshot`).
3. **Regex Command Blocking**: Destructive patterns (`rm -rf`, `format`, `reg delete`, `drop database`) trigger immediate drop & audit alert.
4. **URL Protocol Verification**: Enforces valid `http://`, `https://`, or `file://` targets.

---

## 📁 Repository Structure

```text
O.P.S/
├── backend/                  # Django REST & Async WebSockets Engine
│   ├── manage.py             # Django entrypoint
│   ├── ops_backend/          # Project core configuration (settings, urls, wsgi, asgi)
│   ├── ops_core/             # Core app domain logic
│   │   ├── services/         # Service layer (Ollama tri-model, Automation, Scraping)
│   │   │   ├── ollama_service.py     # 3-Model routing & orchestration engine
│   │   │   ├── automation_service.py # Playwright & PyAutoGUI driver wrappers
│   │   │   └── scraping_service.py   # Crawl4AI & ScrapeGraphAI web extraction
│   │   ├── safety.py         # Safety Gatekeeper & security rules
│   │   ├── views.py          # REST API view endpoints
│   │   └── urls.py           # App URL patterns
│   └── requirements.txt      # Python dependencies (Django, Ollama, Crawl4AI, Playwright, PyAutoGUI)
│
├── frontend/                 # React 18 + Vite + Tailwind CSS Desktop Dashboard & Overlay
│   ├── index.html            # Vite HTML template
│   ├── vite.config.js        # Vite configuration & backend proxy rules
│   ├── tailwind.config.js    # Tailwind CSS styling setup
│   ├── src/
│   │   ├── components/       # UI components (FloatingAvatar, ModelStatusCard, AutomationTerminal)
│   │   ├── App.jsx           # Main dashboard UI
│   │   └── main.jsx          # React app DOM mounting
│   └── package.json          # Node dependencies (React, Framer Motion, Lucide Icons, Tailwind)
│
├── mobile/                   # React Native Android Companion App
│   └── package.json          # Floating bubble overlay & mobile chat head setup
│
├── configs/                  # System environment & model configuration templates
└── docs/                     # Architectural documentation & API spec
```

---

## 🔌 API Reference Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health/` | Health check & Ollama model status |
| `POST` | `/api/v1/router/` | Invokes Model 1 (`qwen2.5:0.5b`) for intent classification |
| `POST` | `/api/v1/plan/` | Invokes Model 2 (`llama3.2:1b`) for multi-step reasoning |
| `POST` | `/api/v1/coding/` | Invokes Model 3 (`qwen2.5-coder:1.5b`) for tool parameter synthesis |
| `POST` | `/api/v1/orchestrate/` | Runs the full 3-model tri-pipeline end-to-end |
| `POST` | `/api/v1/scrape/` | Triggers web scraping and LLM-friendly markdown extraction |
| `POST` | `/api/v1/automation/` | Dispatches validated DOM (Playwright) or GUI (PyAutoGUI) actions |

---

## 🚀 Quick Start Guide

### 1. Ollama Model Setup
Ensure [Ollama](https://ollama.ai) is installed and pull the required 3 lightweight models:
```bash
ollama pull qwen2.5:0.5b
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:1.5b
```

### 2. Backend Setup (Django & AI Services)
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 3. Frontend Setup (React + Tailwind CSS)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` to access the O.P.S. Dashboard & Ambient Overlay.

---

## 🛣️ Project Implementation Roadmap

- [x] Initial Repository Architecture & Directory Blueprint
- [x] Django Backend Skeleton & Security Gatekeeper Implementation
- [x] Ollama Tri-Model Service Layer (`Qwen 0.5B`, `Llama 1B`, `Qwen Coder 1.5B`)
- [x] Web Scraping (Crawl4AI / ScrapeGraphAI) & Automation (Playwright / PyAutoGUI) Wrappers
- [x] React 18 + Tailwind CSS Dashboard & Floating Avatar Overlay Component
- [ ] Active WebSockets / Channels pipeline for streaming model tokens & DOM events
- [ ] Chromadb Vector RAG integration for long-term developer context memory
- [ ] React Native Android companion floating bubble deployment

---

## 📄 License
Distributed under the MIT License. Built for local-first developer productivity.
