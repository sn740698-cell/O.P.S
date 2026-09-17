# O.P.S. (Over-Engineered Programmed System)

Local-first, developer-focused AI operating environment with persistent ambient overlay, multi-agent orchestration, web crawling, OS/DOM automation, and mobile companion.

## Project Structure

```text
O.P.S/
├── backend/           # Django backend, LangGraph multi-agent orchestrator, Ollama model router
├── frontend/          # React (JSX) + Tailwind CSS desktop UI & floating avatar overlay
├── mobile/            # React Native Android companion app with floating bubble chat head
├── configs/           # Environment setup & model configuration
├── scripts/           # Windows launcher & environment bootstrap scripts
└── docs/              # Architectural documentation & user guides
```

## Model Serving Strategy (Ollama)
- **Router (`Qwen 0.6B`)**: Fast intent classification & task routing
- **Reasoning (`Llama 3.2 1B`)**: Planning, context evaluation, decision making
- **Coding & Automation (`Qwen 1.7B`)**: Code generation, tool parameter extraction

## Execution Safety
All tool executions (PyAutoGUI, Playwright, Crawl4AI, Terminal) are strictly gatekept and validated by the **Django Backend**, preventing raw models from executing unauthorized computer actions.
