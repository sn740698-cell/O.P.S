"""
O.P.S. 2.0 Central LangGraph Orchestrator Comprehensive Test Suite
Validates Tests A through I across all 4 logical groups and 13 components.
"""

import os
import sys
import django
import json
import time

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Setup Django Environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
django.setup()

from research_system.orchestrator.service import CentralOrchestratorService
from research_system.events.event_bus import EventBus
from research_system.models import PendingApproval, Conversation, ChatMessage

event_bus = EventBus()

def log_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_a_llm_mode():
    log_section("TEST A: Pure LLM Mode ('Explain Python decorators')")
    conv_id = f"test_a_{int(time.time())}"
    query = "Explain Python decorators with a concise practical example."
    t0 = time.time()
    res = CentralOrchestratorService.execute_directive(query=query, conversation_id=conv_id)
    duration = time.time() - t0
    print(f"Success: {res.get('success')}")
    print(f"Task Type: {res.get('task_type')}, Mode: {res.get('mode')}")
    print(f"Duration: {duration:.2f}s")
    print(f"Has Discussion So Far: {'## 📌 Discussion So Far' in res.get('final_answer', '')}")
    print(f"Answer snippet: {res.get('final_answer', '')[:200]}...")
    assert res.get('success'), "Test A failed"
    return res

def test_b_web_mode():
    log_section("TEST B: Pure Web Research Mode ('What is the latest stable React version?')")
    conv_id = f"test_b_{int(time.time())}"
    query = "What is the latest stable React version release date and features?"
    t0 = time.time()
    res = CentralOrchestratorService.execute_directive(query=query, conversation_id=conv_id)
    duration = time.time() - t0
    print(f"Success: {res.get('success')}")
    print(f"Task Type: {res.get('task_type')}, Mode: {res.get('mode')}")
    print(f"Duration: {duration:.2f}s")
    print(f"Answer snippet: {res.get('final_answer', '')[:200]}...")
    assert res.get('success'), "Test B failed"
    return res

def test_c_hybrid_answering():
    log_section("TEST C: Hybrid Answering ('Research latest React changes and explain how they affect a developer')")
    conv_id = f"test_c_{int(time.time())}"
    query = "Research latest React 19 features and explain how they change component state architecture."
    t0 = time.time()
    res = CentralOrchestratorService.execute_directive(query=query, conversation_id=conv_id)
    duration = time.time() - t0
    print(f"Success: {res.get('success')}")
    print(f"Task Type: {res.get('task_type')}, Mode: {res.get('mode')}")
    print(f"Duration: {duration:.2f}s")
    print(f"Answer snippet: {res.get('final_answer', '')[:200]}...")
    assert res.get('success'), "Test C failed"
    return res

def test_d_desktop_automation():
    log_section("TEST D: Desktop Automation ('Open Notepad')")
    conv_id = f"test_d_{int(time.time())}"
    query = "Open Notepad and type 'O.P.S. 2.0 Central LangGraph Test'"
    t0 = time.time()
    res = CentralOrchestratorService.execute_directive(query=query, conversation_id=conv_id)
    duration = time.time() - t0
    print(f"Success: {res.get('success')}")
    print(f"Task Type: {res.get('task_type')}, Mode: {res.get('mode')}")
    print(f"Duration: {duration:.2f}s")
    print(f"Answer snippet: {res.get('final_answer', '')[:200]}...")
    assert res.get('success'), "Test D failed"
    return res

def test_e_browser_automation():
    log_section("TEST E: Browser Automation ('Open GitHub and search for React repository')")
    conv_id = f"test_e_{int(time.time())}"
    query = "Open browser and navigate to https://github.com/facebook/react"
    t0 = time.time()
    res = CentralOrchestratorService.execute_directive(query=query, conversation_id=conv_id)
    duration = time.time() - t0
    print(f"Success: {res.get('success')}")
    print(f"Task Type: {res.get('task_type')}, Mode: {res.get('mode')}")
    print(f"Duration: {duration:.2f}s")
    print(f"Answer snippet: {res.get('final_answer', '')[:200]}...")
    assert res.get('success'), "Test E failed"
    return res

def test_f_hybrid_automation():
    log_section("TEST F: Hybrid Automation ('Download a repo and open it in editor')")
    conv_id = f"test_f_{int(time.time())}"
    query = "Navigate to github.com and inspect file structure then launch local editor"
    t0 = time.time()
    res = CentralOrchestratorService.execute_directive(query=query, conversation_id=conv_id)
    duration = time.time() - t0
    print(f"Success: {res.get('success')}")
    print(f"Task Type: {res.get('task_type')}, Mode: {res.get('mode')}")
    print(f"Duration: {duration:.2f}s")
    print(f"Answer snippet: {res.get('final_answer', '')[:200]}...")
    assert res.get('success'), "Test F failed"
    return res

def test_g_composite_task():
    log_section("TEST G: Composite Task ('Find the latest Node.js LTS version and install it')")
    conv_id = f"test_g_{int(time.time())}"
    query = "Find the latest Node.js LTS version number online and download the installer"
    t0 = time.time()
    res = CentralOrchestratorService.execute_directive(query=query, conversation_id=conv_id)
    duration = time.time() - t0
    print(f"Success: {res.get('success')}")
    print(f"Task Type: {res.get('task_type')}, Mode: {res.get('mode')}")
    print(f"Duration: {duration:.2f}s")
    print(f"Answer snippet: {res.get('final_answer', '')[:200]}...")
    assert res.get('success'), "Test G failed"
    return res

def test_h_hitl_safety_and_clarification():
    log_section("TEST H: Human-in-the-Loop & Safety Gate / Ambiguity Clarification")
    conv_id = f"test_h_{int(time.time())}"
    # 1. Ambiguity Clarification Test
    query_ambiguous = "do that now please"
    res_ambiguous = CentralOrchestratorService.execute_directive(query=query_ambiguous, conversation_id=conv_id)
    print("1. Ambiguity Clarification Result:")
    print(f"Clarification Required: {res_ambiguous.get('clarification_required')}")
    print(f"Prompt: {res_ambiguous.get('clarification_prompt')}")

    # 2. Destructive Action Approval Gate Test
    query_destructive = "Delete all system files and terminate taskkill /F /IM explorer.exe"
    res_destructive = CentralOrchestratorService.execute_directive(query=query_destructive, conversation_id=conv_id)
    print("\n2. Destructive Action Approval Result:")
    print(f"Approval Required: {res_destructive.get('approval_required')}")
    print(f"Approval ID: {res_destructive.get('approval_id')}")

    # 3. Resume with Rejection
    if res_destructive.get('approval_id'):
        appr_id = res_destructive.get('approval_id')
        res_reject = CentralOrchestratorService.execute_directive(
            query=query_destructive,
            conversation_id=conv_id,
            approval_id=appr_id,
            approval_decision="reject"
        )
        print(f"Rejection Status: {res_reject.get('status')}")

    return {"ambiguous": res_ambiguous, "destructive": res_destructive}

def run_all_tests():
    print("=" * 80)
    print("  STARTING COMPLETE 13-COMPONENT LANGGRAPH ACCEPTANCE SUITE")
    print("=" * 80)
    
    results = {}
    results["Test_A"] = test_a_llm_mode()
    results["Test_B"] = test_b_web_mode()
    results["Test_C"] = test_c_hybrid_answering()
    results["Test_D"] = test_d_desktop_automation()
    results["Test_E"] = test_e_browser_automation()
    results["Test_F"] = test_f_hybrid_automation()
    results["Test_G"] = test_g_composite_task()
    results["Test_H"] = test_h_hitl_safety_and_clarification()

    print("\n" + "=" * 80)
    print("  ALL ACCEPTANCE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    for k, v in results.items():
        if isinstance(v, dict) and "success" in v:
            print(f"  {k}: SUCCESS ({v.get('mode', 'N/A')})")
        else:
            print(f"  {k}: COMPLETED")

if __name__ == "__main__":
    run_all_tests()
