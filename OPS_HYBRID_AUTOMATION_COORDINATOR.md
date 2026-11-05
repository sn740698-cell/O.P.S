# O.P.S. 2.0 — Hybrid Automation Coordinator

## 1. Executive Overview

The **Hybrid Automation Coordinator** (`hybrid_coordinator.py`) bridges the gap between browser execution and local desktop execution. Complex developer directives often span both environments—such as downloading an installer in Chrome and running it in Windows, or scraping API keys online and injecting them into a local `.env` configuration file.

---

## 2. DAG Decomposition and Dependency Management

Each composite mission is decomposed into an acyclic directed graph (DAG) of atomic subtasks:

```
                          [ Composite Directive ]
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
            [ Browser Subtask A ]             [ Desktop Subtask B ]
            (e.g. Download file)              (e.g. Prep destination)
                    │                                 │
                    └────────────────┬────────────────┘
                                     │
                           [ Desktop Subtask C ]
                           (Run installer with file)
```

1. **Topological Evaluation**: Evaluates which subtasks have all prerequisites satisfied.
2. **Parallel Scheduling**: Independent subtasks without shared resource locks are executed concurrently via `concurrent.futures.ThreadPoolExecutor`.
3. **Sequential Gating**: Dependent subtasks block until prerequisite outputs become available.

---

## 3. Concurrency Protection & Resource Locking

To prevent race conditions on local files or applications:
- **`ResourceLockManager`**: Implements thread-safe locking on canonical file paths and application handles.
- If two tasks target the same file (e.g. `parallel_1.txt`), the coordinator forces sequential serialization, preventing write corruption.

---

## 4. State Handoff

Dynamic parameters can reference earlier task outcomes using template tokens:
`$task_id.output` or `$task_id.file_path`
The coordinator resolves these tokens before delegating execution to the target Superior Agent.
