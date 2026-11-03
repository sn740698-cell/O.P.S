"""
O.P.S. 2.0 Complete Validation — Test Suite 2:
Section 3: Reasoning & Planning Agent (Qwen3 1.7B)
Section 4: Reviewer Agent (Llama 3.2 1B)
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

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
import django
django.setup()

from research_system.llm.ollama_client import (
    ollama_client,
    MODEL_QWEN_1_7B,
    MODEL_LLAMA_1B
)

BASE_URL = "http://127.0.0.1:8000"


def test_section_3_reasoning_and_planning():
    print("\n" + "=" * 80)
    print("SECTION 3: REASONING & PLANNING AGENT AUDIT (Qwen3 1.7B)")
    print("=" * 80)

    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    prompts = [
        (1, "Explain how LangGraph works and how it differs from LangChain."),
        (2, "Plan a React frontend with a Django backend for a developer dashboard."),
        (3, "Identify possible causes of a Django API returning HTTP 500."),
        (4, "Break down the process of creating a Python desktop application."),
        (5, "Analyze the following requirement and divide it into implementation steps: create a desktop assistant that accepts voice commands and executes approved system actions.")
    ]

    conv_resp = client.post("/api/chat/conversations/", json={"title": "Reasoning & Planning Audit"})
    assert conv_resp.status_code in (200, 201)
    conv_id = conv_resp.json()["conversation_id"]
    print(f"[*] Active Reasoning Conversation ID: {conv_id}\n")

    results = []
    for p_id, prompt in prompts:
        t0 = time.perf_counter()
        resp = client.post(
            f"/api/chat/conversations/{conv_id}/messages/",
            json={"content": prompt, "input_type": "text"}
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert resp.status_code == 200, f"Error on prompt {p_id}: {resp.status_code}"
        data = resp.json()

        answer = data.get("content") or data.get("final_answer") or ""
        timings = data.get("timings", {})
        mode = data.get("mode")

        # Criteria verification
        has_structure = ("##" in answer or "###" in answer or "1." in answer or "- " in answer)
        has_discussion = ("Discussion So Far" in answer or "📌" in answer)
        not_empty = len(answer.strip()) > 100
        is_actionable = any(k in answer.lower() for k in ["step", "phase", "layer", "architecture", "component", "frontend", "backend", "cause"])

        status = "PASS" if (has_structure and not_empty and is_actionable) else "FAIL"

        rec = {
            "id": p_id,
            "prompt": prompt,
            "mode": mode,
            "status": status,
            "latency_ms": elapsed_ms,
            "has_structure": has_structure,
            "has_discussion_summary": has_discussion,
            "length_chars": len(answer),
            "preview": answer[:140].replace("\n", " ") + "..."
        }
        results.append(rec)

        print(f"[{status}] Prompt #{p_id}: '{prompt}'")
        print(f"       Mode: {mode} | Latency: {elapsed_ms:.1f}ms | Length: {len(answer)} chars")
        print(f"       Structured Output: {has_structure} | Discussion Section: {has_discussion}")
        print(f"       Preview: {rec['preview']}\n")

    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"Reasoning & Planning Summary: {passed}/{len(results)} Passed\n")
    return results


def test_section_4_reviewer_agent():
    print("\n" + "=" * 80)
    print("SECTION 4: REVIEWER AGENT AUDIT (Llama 3.2 1B)")
    print("=" * 80)

    # 1. First, verify whether Reviewer Agent is wired into live graph / endpoints
    import inspect
    from research_system.graph import builder
    from research_system import views

    builder_source = inspect.getsource(builder.build_research_graph)
    views_source = inspect.getsource(views.conversation_messages)

    wired_in_graph = "reviewer" in builder_source.lower()
    wired_in_views = "reviewer" in views_source.lower() or "evaluator" in views_source.lower()

    print(f"[*] Architectural Integration Check:")
    print(f"    - Reviewer node in LangGraph workflow : {'YES' if wired_in_graph else 'NO (NOT IMPLEMENTED in Graph)'}")
    print(f"    - Reviewer called in Views Fast Path  : {'YES' if wired_in_views else 'NO (NOT IMPLEMENTED in Fast Path)'}")

    # 2. Test Llama 3.2 1B capabilities directly via Ollama
    print(f"\n[*] Direct LLM Evaluation of Llama 3.2 1B ({MODEL_LLAMA_1B}):")

    test_cases = [
        {
            "id": 1,
            "name": "Correct Python Function",
            "content": "def calculate_factorial(n: int) -> int:\n    if n < 0:\n        raise ValueError('Negative numbers not supported')\n    if n <= 1:\n        return 1\n    return n * calculate_factorial(n - 1)",
            "expected_verdict": "ACCEPT",
            "instruction": "Review this Python code. If correct, respond with 'STATUS: ACCEPT'. If errors exist, respond with 'STATUS: REJECT' and explanation."
        },
        {
            "id": 2,
            "name": "Intentional Syntax Error",
            "content": "def add_numbers(a, b)\n    return a + b",
            "expected_verdict": "REJECT",
            "instruction": "Review this Python code for syntax and correctness. If correct, respond 'STATUS: ACCEPT'. If syntax or logic errors exist, respond 'STATUS: REJECT' and specify the exact error."
        },
        {
            "id": 3,
            "name": "Unsupported Factual Claim",
            "content": "Python was originally invented in 1687 by Sir Isaac Newton to compute planetary orbits.",
            "expected_verdict": "REJECT",
            "instruction": "Fact-check this statement. If historically accurate, respond 'STATUS: ACCEPT'. If factually incorrect or unsupported, respond 'STATUS: REJECT' and give the correct fact."
        },
        {
            "id": 4,
            "name": "Plan with Missing Implementation Step",
            "content": "Plan for user authentication in Django:\nStep 1: Create a login HTML form in React.\nStep 2: Deploy to production on AWS EC2.",
            "expected_verdict": "REJECT",
            "instruction": "Review this technical plan. If complete, respond 'STATUS: ACCEPT'. If critical steps (e.g. backend endpoints, auth tokens, database) are missing, respond 'STATUS: REJECT' and name the missing steps."
        },
        {
            "id": 5,
            "name": "Contradictory Statements",
            "content": "This function is completely pure and has zero side effects. It also writes user telemetry directly to disk and alters global state.",
            "expected_verdict": "REJECT",
            "instruction": "Review this statement for logical contradictions. If coherent, respond 'STATUS: ACCEPT'. If contradictory, respond 'STATUS: REJECT' explaining the contradiction."
        }
    ]

    reviewer_results = []
    for tc in test_cases:
        t0 = time.perf_counter()
        prompt = f"{tc['instruction']}\n\nContent to review:\n```\n{tc['content']}\n```\n\nYour review:"
        sys_prompt = "You are a strict, objective Code and Content Reviewer. Evaluate the provided submission for correctness, syntax errors, factual inaccuracies, missing plan steps, and logical contradictions. Be concise and start with STATUS: ACCEPT or STATUS: REJECT."

        try:
            output = ollama_client.generate(
                model=MODEL_LLAMA_1B,
                prompt=prompt,
                system_prompt=sys_prompt,
                temperature=0.1,
                num_predict=300,
                timeout=40.0
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000
            upper_out = output.upper()

            if "REJECT" in upper_out and tc["expected_verdict"] == "REJECT":
                verdict_match = True
            elif "ACCEPT" in upper_out and "REJECT" not in upper_out and tc["expected_verdict"] == "ACCEPT":
                verdict_match = True
            else:
                verdict_match = False

            status = "PASS" if verdict_match else "FAIL"

            rec = {
                "id": tc["id"],
                "name": tc["name"],
                "expected": tc["expected_verdict"],
                "status": status,
                "latency_ms": elapsed_ms,
                "output_preview": output[:120].replace("\n", " ") + "..."
            }
            reviewer_results.append(rec)
            print(f"[{status}] Case #{tc['id']}: {tc['name']}")
            print(f"       Expected: {tc['expected_verdict']} | Latency: {elapsed_ms:.1f}ms")
            print(f"       Output Preview: {rec['output_preview']}\n")

        except Exception as e:
            print(f"[FAIL] Case #{tc['id']}: {tc['name']} encountered error: {e}")
            reviewer_results.append({
                "id": tc["id"],
                "name": tc["name"],
                "expected": tc["expected_verdict"],
                "status": "FAIL",
                "error": str(e)
            })

    passed_reviewer = sum(1 for r in reviewer_results if r["status"] == "PASS")
    print(f"Reviewer Capability Summary: {passed_reviewer}/{len(reviewer_results)} Cases Correctly Identified.")
    print("Architectural Status of Reviewer Agent in O.P.S. 2.0: NOT_APPLICABLE / DISABLED in active workflow.")
    print("=" * 80)

    # Save to JSON
    with open(ROOT_DIR / "tests_validation" / "reasoning_and_reviewer_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "architectural_status": "DISABLED_IN_WORKFLOW",
            "model_tested": MODEL_LLAMA_1B,
            "test_cases": reviewer_results
        }, f, indent=2)

    return reviewer_results


if __name__ == "__main__":
    test_section_3_reasoning_and_planning()
    test_section_4_reviewer_agent()
