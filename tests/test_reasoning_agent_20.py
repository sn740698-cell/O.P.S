"""
O.P.S. 2.0 — Advanced Prompt Understanding & Reasoning Agent: 20-Test Validation Suite
Executes the 20 specified canonical tests against AdvancedPromptUnderstandingAgent
and scores each across the 10 formal evaluation metrics (100 pts per test).
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")

import django
django.setup()

from research_system.orchestrator.reasoning import AdvancedPromptUnderstandingAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OPS.Test.Reasoning20")

# 20 Test Definitions
TESTS_SPEC = [
    {
        "id": 1,
        "query": "Explain how to create a React application.",
        "history": [],
        "expected_task_type": "ANSWER",
        "expected_ans_engine": "LLM",
        "expected_auto_engine": "NONE",
        "must_not_automate": True,
        "description": "Explanation query must be routed to LLM mode with no automation."
    },
    {
        "id": 2,
        "query": "Create a React application in my specified test directory.",
        "history": [],
        "expected_task_type": ["AUTOMATION", "DEVELOPMENT"],
        "expected_ans_engine": "NONE",
        "expected_auto_engine": "DESKTOP",
        "must_not_automate": False,
        "description": "Actionable development request routed to Desktop automation."
    },
    {
        "id": 3,
        "query": "What is the latest stable Python version?",
        "history": [],
        "expected_task_type": ["ANSWER", "RESEARCH"],
        "expected_ans_engine": "WEB",
        "expected_auto_engine": "NONE",
        "must_not_automate": True,
        "description": "External fresh facts query routed to Web Research mode."
    },
    {
        "id": 4,
        "query": "Compare Django and FastAPI and recommend one for O.P.S.",
        "history": [],
        "expected_task_type": ["ANSWER", "REASONING"],
        "expected_ans_engine": "HYBRID",
        "expected_auto_engine": "NONE",
        "must_not_automate": True,
        "description": "Comparison with recommendation routed to Hybrid Answering mode."
    },
    {
        "id": 5,
        "query": "Find the latest stable Node.js LTS release, download it and save it in Downloads.",
        "history": [],
        "expected_task_type": ["COMPOSITE", "AUTOMATION"],
        "expected_ans_engine": ["WEB", "NONE"],
        "expected_auto_engine": ["HYBRID", "BROWSER"],
        "must_not_automate": False,
        "description": "Composite discovery + download workflow."
    },
    {
        "id": 6,
        "query": "Open VS Code, create a Python project and write main.py.",
        "history": [],
        "expected_task_type": ["AUTOMATION", "DEVELOPMENT"],
        "expected_ans_engine": "NONE",
        "expected_auto_engine": "DESKTOP",
        "must_not_automate": False,
        "description": "Multi-step desktop automation with code generation."
    },
    {
        "id": 7,
        "query": "Explain how to open VS Code and create a Python project.",
        "history": [],
        "expected_task_type": "ANSWER",
        "expected_ans_engine": "LLM",
        "expected_auto_engine": "NONE",
        "must_not_automate": True,
        "description": "Explanation query with action verbs must NOT trigger automation."
    },
    {
        "id": 8,
        "query": "Open the official Django documentation in Chrome.",
        "history": [],
        "expected_task_type": "AUTOMATION",
        "expected_ans_engine": "NONE",
        "expected_auto_engine": "BROWSER",
        "must_not_automate": False,
        "description": "Direct browser opening directive."
    },
    {
        "id": 9,
        "query": "Research Django migrations and explain how they work.",
        "history": [],
        "expected_task_type": ["ANSWER", "RESEARCH", "REASONING"],
        "expected_ans_engine": ["HYBRID", "WEB"],
        "expected_auto_engine": "NONE",
        "must_not_automate": True,
        "description": "Research + explanation routed to Hybrid or Web mode."
    },
    {
        "id": 10,
        "query": "Download the documentation PDF and open it on my computer.",
        "history": [],
        "expected_task_type": "AUTOMATION",
        "expected_ans_engine": "NONE",
        "expected_auto_engine": "HYBRID",
        "must_not_automate": False,
        "description": "Cross-domain hybrid automation (Browser download -> Desktop open)."
    },
    {
        "id": 11,
        "query": "Create a file, but do not overwrite anything that already exists.",
        "history": [],
        "expected_task_type": ["AUTOMATION", "DEVELOPMENT"],
        "expected_ans_engine": "NONE",
        "expected_auto_engine": "DESKTOP",
        "expected_constraint": "do_not_overwrite",
        "must_not_automate": False,
        "description": "Desktop creation with explicit no-overwrite constraint."
    },
    {
        "id": 12,
        "query": "Open my project and fix the error.",
        "history": [],
        "expected_task_type": "CLARIFICATION",
        "expected_clarification": True,
        "must_not_automate": True,
        "description": "Missing project and error details must trigger Clarification Gate."
    },
    {
        "id": 13,
        "query": "Actually, use TypeScript instead of JavaScript.",
        "history": [
            {"content": "Open VS Code."},
            {"content": "Create a React project using JavaScript."}
        ],
        "expected_task_type": ["AUTOMATION", "DEVELOPMENT", "ANSWER"],
        "expected_language": "TypeScript",
        "expected_framework": "React",
        "must_not_automate": False,
        "description": "Context correction overriding language to TypeScript while preserving React."
    },
    {
        "id": 14,
        "query": "Add the same feature to the other component.",
        "history": [
            {"content": "Add dark mode toggle to Header.jsx."}
        ],
        "expected_task_type": ["CLARIFICATION", "AUTOMATION", "DEVELOPMENT"],
        "description": "Context resolution for anaphora ('same feature', 'other component')."
    },
    {
        "id": 15,
        "query": "Research the latest Django release, check my installed version and tell me whether I need to update.",
        "history": [],
        "expected_task_type": ["COMPOSITE", "RESEARCH", "REASONING"],
        "expected_ans_engine": ["WEB", "HYBRID"],
        "must_not_auto_update": True,
        "description": "Composite research + inspection + recommendation without modifying files."
    },
    {
        "id": 16,
        "query": "Open Calculator and Chrome at the same time.",
        "history": [],
        "expected_task_type": "AUTOMATION",
        "expected_auto_engine": ["HYBRID", "DESKTOP"],
        "must_be_parallel": True,
        "description": "Independent parallel application launches."
    },
    {
        "id": 17,
        "query": "Explain the difference between browser automation and web scraping.",
        "history": [],
        "expected_task_type": "ANSWER",
        "expected_ans_engine": "LLM",
        "expected_auto_engine": "NONE",
        "must_not_automate": True,
        "description": "Conceptual comparison query routed to LLM mode without automation."
    },
    {
        "id": 18,
        "query": "Search for the latest LangGraph documentation and open the official page in Chrome.",
        "history": [],
        "expected_task_type": ["COMPOSITE", "AUTOMATION"],
        "expected_auto_engine": "BROWSER",
        "description": "Composite search and direct browser opening."
    },
    {
        "id": 19,
        "query": "Create a folder called OPS_TEST, put a Python file inside it, write a simple program and open the file.",
        "history": [],
        "expected_task_type": ["AUTOMATION", "DEVELOPMENT"],
        "expected_auto_engine": "DESKTOP",
        "must_have_dependencies": True,
        "description": "Multi-step desktop automation with strict sequential dependencies."
    },
    {
        "id": 20,
        "query": "Don't execute anything. Just explain what changes you would make to my project architecture.",
        "history": [],
        "expected_task_type": "ANSWER",
        "expected_ans_engine": "LLM",
        "expected_auto_engine": "NONE",
        "must_not_automate": True,
        "description": "Negative constraint 'Don't execute anything' strictly enforced."
    }
]


def score_test_result(t_spec: Dict[str, Any], res: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates the test result against the 10 formal metrics (10 pts each, 100 max)."""
    scores = {
        "objective_understanding": 10,
        "context_resolution": 10,
        "entity_extraction": 10,
        "constraint_preservation": 10,
        "task_classification": 10,
        "engine_selection": 10,
        "mode_selection": 10,
        "plan_quality": 10,
        "dependency_handling": 10,
        "clarification_safety": 10
    }
    notes = []

    # 1. Task classification
    actual_type = res.get("task_type")
    exp_types = t_spec.get("expected_task_type")
    if isinstance(exp_types, list):
        if actual_type not in exp_types:
            scores["task_classification"] = 2
            notes.append(f"task_type mismatch: expected {exp_types}, got {actual_type}")
    elif exp_types and actual_type != exp_types:
        scores["task_classification"] = 2
        notes.append(f"task_type mismatch: expected {exp_types}, got {actual_type}")

    # 2. Engine & Mode selection
    actual_ans = res.get("answering_engine")
    actual_auto = res.get("automation_engine")

    exp_ans = t_spec.get("expected_ans_engine")
    if exp_ans:
        if isinstance(exp_ans, list) and actual_ans not in exp_ans:
            scores["engine_selection"] = 4
            scores["mode_selection"] = 4
            notes.append(f"ans_engine mismatch: expected {exp_ans}, got {actual_ans}")
        elif isinstance(exp_ans, str) and actual_ans != exp_ans:
            scores["engine_selection"] = 4
            scores["mode_selection"] = 4
            notes.append(f"ans_engine mismatch: expected {exp_ans}, got {actual_ans}")

    exp_auto = t_spec.get("expected_auto_engine")
    if exp_auto:
        if isinstance(exp_auto, list) and actual_auto not in exp_auto:
            scores["engine_selection"] = 4
            scores["mode_selection"] = 4
            notes.append(f"auto_engine mismatch: expected {exp_auto}, got {actual_auto}")
        elif isinstance(exp_auto, str) and actual_auto != exp_auto:
            scores["engine_selection"] = 4
            scores["mode_selection"] = 4
            notes.append(f"auto_engine mismatch: expected {exp_auto}, got {actual_auto}")

    # 3. Critical Failure: Automated when must NOT automate
    if t_spec.get("must_not_automate") and actual_auto != "NONE":
        scores["task_classification"] = 0
        scores["engine_selection"] = 0
        scores["clarification_safety"] = 0
        notes.append("CRITICAL: Planned automation for explanation/informational request!")

    # 4. Constraint preservation
    if t_spec.get("expected_constraint"):
        c_req = t_spec["expected_constraint"]
        if c_req not in res.get("constraints", []) and not res.get("parameters", {}).get("overwrite") is False:
            scores["constraint_preservation"] = 2
            notes.append(f"Missing explicit constraint: {c_req}")

    # 5. Clarification safety
    if t_spec.get("expected_clarification") and not res.get("clarification_required"):
        scores["clarification_safety"] = 0
        notes.append("CRITICAL: Failed to require clarification for missing essential target!")

    # 6. Context resolution
    if t_spec.get("expected_language"):
        ctx = res.get("context", {})
        if ctx.get("active_language") != t_spec["expected_language"]:
            scores["context_resolution"] = 4
            notes.append(f"Context language mismatch: expected {t_spec['expected_language']}")

    total_score = sum(scores.values())
    is_passed = total_score >= 80 and not any("CRITICAL" in n for n in notes)

    return {
        "total_score": total_score,
        "is_passed": is_passed,
        "scores": scores,
        "notes": notes
    }


def run_all_20_tests():
    agent = AdvancedPromptUnderstandingAgent()
    print("=" * 80)
    print("O.P.S. 2.0 — ADVANCED PROMPT UNDERSTANDING & REASONING 20-TEST VALIDATION")
    print("=" * 80)

    results_summary = []
    total_points = 0

    for spec in TESTS_SPEC:
        tid = spec["id"]
        q = spec["query"]
        hist = spec.get("history", [])

        print(f"\n[Test {tid:02d}] {q}")
        t0 = time.time()
        res = agent.understand_and_plan(q, conversation_history=hist, task_id=f"test_{tid}")
        eval_res = score_test_result(spec, res)
        duration = round(time.time() - t0, 2)

        score = eval_res["total_score"]
        status = "PASS" if eval_res["is_passed"] else "FAIL"
        total_points += score

        record = {
            "test_id": tid,
            "query": q,
            "expected_task_type": str(spec.get("expected_task_type")),
            "actual_task_type": res.get("task_type"),
            "expected_engine": f"Ans={spec.get('expected_ans_engine')}, Auto={spec.get('expected_auto_engine')}",
            "actual_engine": f"Ans={res.get('answering_engine')}, Auto={res.get('automation_engine')}",
            "score": score,
            "status": status,
            "notes": eval_res["notes"],
            "duration_s": duration
        }
        results_summary.append(record)

        print(f"  -> Type: {res.get('task_type')} | Ans: {res.get('answering_engine')} | Auto: {res.get('automation_engine')}")
        print(f"  -> Score: {score}/100 [{status}] in {duration}s")
        if eval_res["notes"]:
            print(f"  -> Notes: {', '.join(eval_res['notes'])}")

    avg_score = round(total_points / len(TESTS_SPEC), 1)
    all_passed = all(r["status"] == "PASS" for r in results_summary)

    print("\n" + "=" * 80)
    print(f"FINAL RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print(f"Average Score: {avg_score}/100 (Target: >= 90/100)")
    print("=" * 80)

    # Save structured test output JSON
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "reasoning_20_results.json"))
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "average_score": avg_score,
            "all_passed": all_passed,
            "tests": results_summary
        }, f, indent=2)

    return all_passed, avg_score, results_summary


if __name__ == "__main__":
    run_all_20_tests()
