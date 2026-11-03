"""
O.P.S. 2.0 Deep Agent Architecture & State Transition Audit
Audits all 13 individual agent nodes for implementation, inputs, outputs, state passing, and error handling.
"""

import os
import sys
import django
import time

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops_backend.settings")
django.setup()

from research_system.orchestrator.state import CentralGraphState
from research_system.orchestrator.agents.global_intent_router import global_intent_router_node
from research_system.orchestrator.agents.task_understanding_planner import task_understanding_planner_node
from research_system.orchestrator.agents.local_reasoning_agent import local_reasoning_agent_node
from research_system.orchestrator.agents.web_research_agent import web_research_agent_node
from research_system.orchestrator.agents.evidence_validation_agent import evidence_validation_agent_node
from research_system.orchestrator.agents.answer_synthesis_agent import answer_synthesis_agent_node
from research_system.orchestrator.agents.automation_planner_agent import automation_planner_agent_node
from research_system.orchestrator.agents.desktop_automation_executor import desktop_automation_executor_node
from research_system.orchestrator.agents.browser_automation_executor import browser_automation_executor_node
from research_system.orchestrator.agents.verification_recovery_agent import verification_recovery_agent_node
from research_system.orchestrator.agents.hitl_safety_controller import hitl_safety_controller_node
from research_system.orchestrator.agents.composite_task_coordinator import composite_task_coordinator_node
from research_system.orchestrator.agents.result_formatter_agent import result_formatter_agent_node

def make_base_state(query="Test query", task_type="ANSWER", answering_mode="LLM", auto_mode="DESKTOP"):
    return {
        "task_id": f"test_audit_{int(time.time())}",
        "conversation_id": "test_audit_conv",
        "request_id": "req_audit_1",
        "user_query": query,
        "task_type": task_type,
        "answering_mode": answering_mode,
        "automation_mode": auto_mode,
        "user_goal": query,
        "routing_result": {},
        "execution_plan": [],
        "current_agent": "START",
        "active_agents": [],
        "completed_agents": [],
        "pending_agents": [],
        "agent_status": {},
        "task_dependencies": {},
        "local_reasoning_output": "",
        "research_results": {},
        "validated_evidence": {},
        "automation_results": {},
        "verification_results": {},
        "approval_required": False,
        "approval_status": "NONE",
        "approval_id": None,
        "approval_reason": "",
        "clarification_required": False,
        "clarification_prompt": None,
        "clarification_response": None,
        "retry_count": 0,
        "errors": [],
        "final_response": "",
        "source_references": [],
        "task_status": "RECEIVED",
        "timestamps": {"started_at": time.time()}
    }

def audit_agent(num, name, fn, state):
    print(f"\n--- [AGENT {num}: {name}] ---")
    t0 = time.time()
    try:
        out = fn(state)
        dur = round(time.time() - t0, 3)
        assert isinstance(out, dict), f"Output must be dict, got {type(out)}"
        print(f"Status: WORKING ({dur}s)")
        print(f"Keys returned: {list(out.keys())}")
        return True, out
    except Exception as e:
        print(f"Status: FAILED ({e})")
        return False, str(e)

def run_agent_audit():
    results = {}
    print("=" * 70)
    print("  RUNNING DEEP AUDIT ON ALL 13 INDIVIDUAL AGENTS")
    print("=" * 70)

    # 1. Global Intent Router
    st1 = make_base_state(query="Explain Python decorators")
    ok1, out1 = audit_agent(1, "Global Intent Router", global_intent_router_node, st1)
    results["Agent_1"] = ok1

    # 2. Task Understanding & Planner
    st2 = make_base_state(query="Explain Python decorators")
    st2.update(out1)
    ok2, out2 = audit_agent(2, "Task Understanding & Planner", task_understanding_planner_node, st2)
    results["Agent_2"] = ok2

    # 3. Local Reasoning Agent
    st3 = make_base_state(query="What is 2 + 2?")
    ok3, out3 = audit_agent(3, "Local Reasoning Agent", local_reasoning_agent_node, st3)
    results["Agent_3"] = ok3

    # 4. Web Research Agent
    st4 = make_base_state(query="React current release date")
    ok4, out4 = audit_agent(4, "Web Research Agent", web_research_agent_node, st4)
    results["Agent_4"] = ok4

    # 5. Evidence Validation Agent
    st5 = make_base_state(query="React current release date")
    st5.update(out4)
    ok5, out5 = audit_agent(5, "Evidence Validation Agent", evidence_validation_agent_node, st5)
    results["Agent_5"] = ok5

    # 6. Answer Synthesis Agent
    st6 = make_base_state(query="React current release date")
    st6.update(out4)
    st6.update(out5)
    ok6, out6 = audit_agent(6, "Answer Synthesis Agent", answer_synthesis_agent_node, st6)
    results["Agent_6"] = ok6

    # 7. Automation Planner
    st7 = make_base_state(query="Open Notepad and type test", task_type="AUTOMATION", auto_mode="DESKTOP")
    ok7, out7 = audit_agent(7, "Automation Planner", automation_planner_agent_node, st7)
    results["Agent_7"] = ok7

    # 8. Desktop Automation Executor
    st8 = make_base_state(query="Open Notepad", task_type="AUTOMATION", auto_mode="DESKTOP")
    st8.update(out7)
    ok8, out8 = audit_agent(8, "Desktop Automation Executor", desktop_automation_executor_node, st8)
    results["Agent_8"] = ok8

    # 9. Browser Automation Executor
    st9 = make_base_state(query="Open https://github.com", task_type="AUTOMATION", auto_mode="BROWSER")
    st9["execution_plan"] = [{"step_id": 1, "action": "navigate", "params": {"url": "https://github.com"}}]
    ok9, out9 = audit_agent(9, "Browser Automation Executor", browser_automation_executor_node, st9)
    results["Agent_9"] = ok9

    # 10. Verification & Recovery Agent
    st10 = make_base_state(query="Open Notepad", task_type="AUTOMATION")
    st10.update(out8)
    ok10, out10 = audit_agent(10, "Verification & Recovery Agent", verification_recovery_agent_node, st10)
    results["Agent_10"] = ok10

    # 11. HITL & Safety Controller
    st11 = make_base_state(query="Delete all system files and terminate taskkill /F /IM explorer.exe", task_type="AUTOMATION")
    ok11, out11 = audit_agent(11, "HITL & Safety Controller", hitl_safety_controller_node, st11)
    results["Agent_11"] = ok11

    # 12. Composite Task Coordinator
    st12 = make_base_state(query="Find latest Node LTS online and download it", task_type="COMPOSITE")
    ok12, out12 = audit_agent(12, "Composite Task Coordinator", composite_task_coordinator_node, st12)
    results["Agent_12"] = ok12

    # 13. Result Formatter / Persona Agent
    st13 = make_base_state(query="What is 2 + 2?", task_type="ANSWER", answering_mode="LLM")
    st13["local_reasoning_output"] = "2 + 2 equals 4."
    ok13, out13 = audit_agent(13, "Result Formatter / Persona Agent", result_formatter_agent_node, st13)
    results["Agent_13"] = ok13

    print("\n" + "=" * 70)
    print("  AGENT AUDIT SUMMARY")
    print("=" * 70)
    for k, v in results.items():
        print(f"  {k}: {'WORKING' if v else 'FAILED'}")

if __name__ == "__main__":
    run_agent_audit()
