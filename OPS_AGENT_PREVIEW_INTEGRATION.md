# O.P.S. 2.0 — Cockpit Agent Preview Integration

## 1. Overview

The O.P.S. Pop-up Cockpit features an interactive, retro-futuristic **Agent Preview** embedded directly into the loading skeleton and execution view. The preview communicates with the backend via Server-Sent Events (SSE), dynamically updating UI cards without window blinking, remounting, or flickering.

---

## 2. Event Model & Telemetry Mapping

The multi-agent architecture publishes granular lifecycle events through `EventBus`:

| Event Pattern | Trigger Point | Visual Presentation |
| :--- | :--- | :--- |
| `agent.started` | Superior Agent begins directive execution | Activates Superior Agent banner and stage stepper |
| `agent.handoff` | Delegation from Superior to Specialist (e.g. B1 -> B3) | Updates Active Specialist card and animated glint badge |
| `agent.progress` | In-flight action (e.g. typing, clicking, navigating) | Updates Directive Action text and glowing status indicator |
| `agent.completed` | Postcondition empirical verification passes | Flashes green `Verified ✅` badge and transitions to output |
| `coordinator.parallel_dispatch` | Hybrid Coordinator dispatches independent subtasks | Shows parallel execution chips and active resource locks |

---

## 3. Non-Blinking Stability Guarantees

Previous iterations suffered from cockpit flickering during browser execution because global DOM events or window blur triggers caused UI unmounts.
Stability was achieved through:
1. **Memoized Skeleton Steppers**: `useMemo` hooks anchor stage collections and avoid array re-allocations on SSE ticks.
2. **Dedicated Playwright Worker**: Playwright executes off the main thread in `OPS-PlaywrightWorker`, preventing OS window focus locks from starving the Vite dev server or Cockpit rendering loop.
3. **Additive Telemetry Updates**: `setAutomationTelemetry((prev) => ({ ...prev, ...parsed }))` updates state incrementally without zeroing out previous context.
