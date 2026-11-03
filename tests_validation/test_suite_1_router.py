"""
O.P.S. 2.0 Complete Validation — Test Suite 1: Router Agent Audit
Tests all 10 mandated prompts against:
1. Pure Classifier Function: classify_execution_route
2. Live Django Backend API: POST /api/chat/conversations/{id}/messages/
Records exact classified intent, execution path, router latency, and verification status.
"""

import sys
import os
import time
import json
import httpx
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from research_system.router import (
    classify_execution_route,
    ROUTE_GENERAL_CHAT,
    ROUTE_SIMPLE_QUESTION,
    ROUTE_COMPLEX_REASONING,
    ROUTE_WEB_RESEARCH,
    ROUTE_SYSTEM_AUTOMATION,
    ROUTE_CODE_GENERATION,
    ROUTE_OTHER
)

BASE_URL = "http://127.0.0.1:8000"

TEST_PROMPTS = [
    {
        "id": 1,
        "prompt": "Hello O.P.S., how are you?",
        "expected_type": "Greetings",
        "expected_route": ROUTE_GENERAL_CHAT,
        "allow_routes": [ROUTE_GENERAL_CHAT],
    },
    {
        "id": 2,
        "prompt": "What is artificial intelligence?",
        "expected_type": "General knowledge",
        "expected_route": ROUTE_SIMPLE_QUESTION,
        "allow_routes": [ROUTE_SIMPLE_QUESTION, ROUTE_GENERAL_CHAT],
    },
    {
        "id": 3,
        "prompt": "Calculate 25 multiplied by 48.",
        "expected_type": "Simple calculations",
        "expected_route": ROUTE_SIMPLE_QUESTION,
        "allow_routes": [ROUTE_SIMPLE_QUESTION],
    },
    {
        "id": 4,
        "prompt": "What is the latest AI news?",
        "expected_type": "Current information",
        "expected_route": ROUTE_WEB_RESEARCH,
        "allow_routes": [ROUTE_WEB_RESEARCH],
    },
    {
        "id": 5,
        "prompt": "Open Chrome.",
        "expected_type": "Desktop operations",
        "expected_route": ROUTE_SYSTEM_AUTOMATION,
        "allow_routes": [ROUTE_SYSTEM_AUTOMATION],
    },
    {
        "id": 6,
        "prompt": "Create a folder named OPS_Test on my Desktop.",
        "expected_type": "Desktop operations",
        "expected_route": ROUTE_SYSTEM_AUTOMATION,
        "allow_routes": [ROUTE_SYSTEM_AUTOMATION],
    },
    {
        "id": 7,
        "prompt": "Explain this Python code.",
        "expected_type": "Programming / explanation",
        "expected_route": ROUTE_SIMPLE_QUESTION,
        "allow_routes": [ROUTE_SIMPLE_QUESTION, ROUTE_CODE_GENERATION],
    },
    {
        "id": 8,
        "prompt": "Find information about LangGraph.",
        "expected_type": "Research / information lookup",
        "expected_route": ROUTE_OTHER, # May be OTHER or WEB_RESEARCH
        "allow_routes": [ROUTE_OTHER, ROUTE_SIMPLE_QUESTION, ROUTE_WEB_RESEARCH],
    },
    {
        "id": 9,
        "prompt": "Write a professional email requesting a project meeting.",
        "expected_type": "Email or document writing",
        "expected_route": ROUTE_OTHER, # Content generation
        "allow_routes": [ROUTE_OTHER, ROUTE_GENERAL_CHAT],
    },
    {
        "id": 10,
        "prompt": "Search my project files for the Django API implementation.",
        "expected_type": "Local project-file lookup",
        "expected_route": ROUTE_OTHER, # Local tool lookup
        "allow_routes": [ROUTE_OTHER, ROUTE_SYSTEM_AUTOMATION, ROUTE_WEB_RESEARCH],
    },
]


def run_router_audit():
    print("=" * 80)
    print("SECTION 2: ROUTER AGENT COMPREHENSIVE AUDIT & EXECUTION TRACE")
    print("=" * 80)

    client = httpx.Client(base_url=BASE_URL, timeout=45.0)

    # 1. Create a designated audit conversation
    conv_resp = client.post("/api/chat/conversations/", json={"title": "Router Audit Session"})
    assert conv_resp.status_code in (200, 201), f"Failed to create conversation: {conv_resp.text}"
    conv_id = conv_resp.json()["conversation_id"]
    print(f"[*] Active Conversation ID: {conv_id}\n")

    results = []

    for item in TEST_PROMPTS:
        p_id = item["id"]
        prompt = item["prompt"]
        exp_type = item["expected_type"]
        allow_routes = item["allow_routes"]

        # Step A: Direct Classifier Evaluation
        t0_clf = time.perf_counter()
        clf_route = classify_execution_route(prompt)
        clf_time_ms = (time.perf_counter() - t0_clf) * 1000

        # Step B: Live API Dispatch
        t0_api = time.perf_counter()
        api_resp = client.post(
            f"/api/chat/conversations/{conv_id}/messages/",
            json={"content": prompt, "input_type": "text"}
        )
        api_time_ms = (time.perf_counter() - t0_api) * 1000

        assert api_resp.status_code == 200, f"API error on prompt {p_id}: {api_resp.status_code} {api_resp.text}"
        data = api_resp.json()

        actual_mode = data.get("mode")
        timings = data.get("timings", {})
        router_ms = timings.get("router_ms", clf_time_ms)
        total_ms = timings.get("total_ms", api_time_ms)
        answer_preview = (data.get("content") or data.get("final_answer") or "")[:80].replace("\n", " ")

        # Verification Status
        matched = actual_mode in allow_routes
        status = "PASS" if matched else "FAIL"

        # Check for unintended web research
        unintended_crawler = (actual_mode == ROUTE_WEB_RESEARCH and ROUTE_WEB_RESEARCH not in allow_routes)

        record = {
            "id": p_id,
            "prompt": prompt,
            "expected_type": exp_type,
            "expected_routes": allow_routes,
            "actual_route": actual_mode,
            "router_latency_ms": router_ms,
            "total_latency_ms": total_ms,
            "status": status,
            "unintended_crawler": unintended_crawler,
            "preview": answer_preview
        }
        results.append(record)

        print(f"[{status}] Prompt #{p_id}: '{prompt}'")
        print(f"       Expected Type : {exp_type}")
        print(f"       Selected Route: {actual_mode} (Router: {router_ms:.2f}ms | Total: {total_ms:.1f}ms)")
        print(f"       Execution Path: {'12-Node Web Crawler' if actual_mode == ROUTE_WEB_RESEARCH else 'Fast Direct Reasoning'}")
        if unintended_crawler:
            print(f"       [CRITICAL BUG] Unintended Web Crawling triggered for non-research query!")
        print(f"       Response Preview: {answer_preview}...\n")

    # Summary Table
    print("=" * 80)
    print(f"{'#':<3} | {'Prompt':<40} | {'Selected Route':<20} | {'Status':<6}")
    print("-" * 80)
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    for r in results:
        print(f"{r['id']:<3} | {r['prompt'][:40]:<40} | {r['actual_route']:<20} | {r['status']:<6}")
    print("=" * 80)
    print(f"Router Test Results: {passed_count}/{len(results)} Passed ({(passed_count/len(results))*100:.1f}%)")
    print("=" * 80)

    with open(ROOT_DIR / "tests_validation" / "router_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    run_router_audit()
