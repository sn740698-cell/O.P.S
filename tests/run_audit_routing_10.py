"""
Audit Test Runner for Part 6: Answering Mode and Routing Validation (10 checks)
Verifies Global Intent Router & Understanding Agent routing across 10 canonical queries.
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from research_system.router import classify_request_mode

ROUTING_TESTS = [
    {
        "id": "ROUTE-01",
        "prompt": "Explain Python classes",
        "expected_task": "ANSWER",
        "expected_engine": "ANSWERING",
        "expected_mode": "LLM"
    },
    {
        "id": "ROUTE-02",
        "prompt": "Explain what LangGraph is",
        "expected_task": "ANSWER",
        "expected_engine": "ANSWERING",
        "expected_mode": "LLM"
    },
    {
        "id": "ROUTE-03",
        "prompt": "What is today's date?",
        "expected_task": "ANSWER",
        "expected_engine": "ANSWERING",
        "expected_mode": ["LLM", "WEB"]  # Temporal / Local context
    },
    {
        "id": "ROUTE-04",
        "prompt": "Latest stable Python version",
        "expected_task": "ANSWER",
        "expected_engine": "ANSWERING",
        "expected_mode": "WEB"
    },
    {
        "id": "ROUTE-05",
        "prompt": "Latest Django release",
        "expected_task": "ANSWER",
        "expected_engine": "ANSWERING",
        "expected_mode": "WEB"
    },
    {
        "id": "ROUTE-06",
        "prompt": "Compare Django and FastAPI",
        "expected_task": "ANSWER",
        "expected_engine": "ANSWERING",
        "expected_mode": "HYBRID"
    },
    {
        "id": "ROUTE-07",
        "prompt": "Research and explain LangGraph architecture",
        "expected_task": "ANSWER",
        "expected_engine": "ANSWERING",
        "expected_mode": "HYBRID"
    },
    {
        "id": "ROUTE-08",
        "prompt": "Open VS Code",
        "expected_task": "AUTOMATION",
        "expected_engine": "AUTOMATION",
        "expected_mode": "DESKTOP"
    },
    {
        "id": "ROUTE-09",
        "prompt": "Search YouTube",
        "expected_task": "AUTOMATION",
        "expected_engine": "AUTOMATION",
        "expected_mode": "BROWSER"
    },
    {
        "id": "ROUTE-10",
        "prompt": "Research and install Node.js",
        "expected_task": "COMPOSITE",
        "expected_engine": "COMPOSITE",
        "expected_mode": "HYBRID"
    }
]

print(f"Running Part 6 Routing Audit on {len(ROUTING_TESTS)} prompts...")
results = []
for t in ROUTING_TESTS:
    res = classify_request_mode(t["prompt"])
    task = res.get("task_type")
    engine = res.get("engine")
    mode = res.get("mode")

    # Evaluate match
    task_ok = (task == t["expected_task"]) if not isinstance(t["expected_task"], list) else (task in t["expected_task"])
    engine_ok = (engine == t["expected_engine"]) if not isinstance(t["expected_engine"], list) else (engine in t["expected_engine"])
    mode_ok = (mode == t["expected_mode"]) if not isinstance(t["expected_mode"], list) else (mode in t["expected_mode"])
    passed = task_ok and engine_ok and mode_ok

    results.append({
        "id": t["id"],
        "prompt": t["prompt"],
        "expected": f"Task={t['expected_task']} | Engine={t['expected_engine']} | Mode={t['expected_mode']}",
        "actual": f"Task={task} | Engine={engine} | Mode={mode}",
        "passed": passed,
        "details": res
    })
    status_str = "PASS" if passed else "FAIL"
    print(f"[{t['id']}] '{t['prompt']}' -> {task}/{engine}/{mode} [{status_str}]")

output_file = os.path.join(os.path.dirname(__file__), "audit_routing_10_results.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Routing results written to {output_file}")
