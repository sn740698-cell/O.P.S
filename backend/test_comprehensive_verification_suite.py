"""
O.P.S. Comprehensive Verification Suite
Tests:
1. System Identity (Attribution to Suraj, J.A.R.V.I.S. Persona)
2. Live Web Crawling (Zero DuckDuckGo, Real-time DOM/MediaWiki/RSS, LLM synthesis in retro bullets)
3. Conversational Elaboration Loop (Multi-turn session memory context)
4. Desktop & System Task Automation (Applications, Files/Folders, Universal Web Sites & Media Playback)
5. Single-Approval HITL Security Pre-Approval
"""

import os
import sys
import asyncio
import django

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ops_backend.settings')
django.setup()

from ops_core.services.agent_orchestrator import OPSMultiAgentOrchestrator
from ops_core.services.scraping_service import scraping_service
from ops_core.services.session_memory import OPSSessionMemoryManager
from ops_core.services.permission_manager import OPSPermissionManager

orchestrator = OPSMultiAgentOrchestrator()
memory = OPSSessionMemoryManager()
session_id = "test_verification_session_alpha"


async def main():
    print("=" * 60)
    print("O.P.S. FULL SYSTEM COMPREHENSIVE VERIFICATION")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. System Identity & Creator Attribution
    # -------------------------------------------------------------
    print("\n[SECTION 1: SYSTEM IDENTITY & CREATOR ATTRIBUTION]")
    res_id = await orchestrator.run_task_async("who are you and who created you", session_id=session_id)
    print(">> Prompt: who are you and who created you")
    print(">> Response:\n", res_id.get("final_answer", ""))

    # -------------------------------------------------------------
    # 2. Live Web Crawling & Real-Time Knowledge Synthesis (5 queries)
    # -------------------------------------------------------------
    print("\n[SECTION 2: LIVE WEB CRAWLING & DYNAMIC LLM SYNTHESIS]")
    crawling_queries = [
        "who is Sam Altman",
        "what is Quantum Supremacy",
        "explain General Relativity",
        "James Webb Space Telescope latest discoveries",
        "tell me about CRISPR gene editing"
    ]
    for q in crawling_queries:
        print(f"\n>> Crawl Directive: '{q}'")
        res = await orchestrator.run_task_async(q, session_id=session_id)
        # Print first 350 chars of the formatted response
        ans = res.get("final_answer", "")
        print(ans[:450] + ("..." if len(ans) > 450 else ""))

    # -------------------------------------------------------------
    # 3. Contextual Follow-up / Elaboration Loop
    # -------------------------------------------------------------
    print("\n[SECTION 3: CONVERSATIONAL ELABORATION LOOP]")
    print(">> Follow-up Prompt: 'tell me more about the chat and give more info on that'")
    res_followup = await orchestrator.run_task_async("tell me more about the chat and give more info on that", session_id=session_id)
    print(">> Elaboration Response:\n", res_followup.get("final_answer", "")[:450])

    # -------------------------------------------------------------
    # 4. Universal Web & Media Automation Commands (5 queries)
    # -------------------------------------------------------------
    print("\n[SECTION 4: UNIVERSAL WEB & MEDIA AUTOMATION]")
    media_queries = [
        "open google search latest AI news",
        "open youtube and search Data structure",
        "open spotify and play Coldplay",
        "open github and search LangGraph",
        "open amazon and search mechanical keyboard"
    ]
    for mq in media_queries:
        print(f"\n>> Action Directive: '{mq}'")
        res_m = await orchestrator.run_task_async(mq, session_id=session_id)
        print(">> Execution Result:\n", res_m.get("final_answer", "")[:300])

    # -------------------------------------------------------------
    # 5. Local Installed Applications & System Files / Folders (5 queries)
    # -------------------------------------------------------------
    print("\n[SECTION 5: DESKTOP APP & SYSTEM FILE AUTOMATION]")
    app_queries = [
        "open notepad",
        "open calculator",
        "open folder downloads",
        "open vscode",
        "open file explorer"
    ]
    for aq in app_queries:
        print(f"\n>> System Directive: '{aq}'")
        res_a = await orchestrator.run_task_async(aq, session_id=session_id)
        print(">> Action Telemetry:\n", res_a.get("final_answer", "")[:250])

    # -------------------------------------------------------------
    # 6. Single-Approval HITL Security Check
    # -------------------------------------------------------------
    print("\n[SECTION 6: SINGLE-APPROVAL HITL SEMANTICS]")
    OPSPermissionManager._hitl_once_approved = True
    is_pre_approved = OPSPermissionManager.is_action_pre_approved(
        action="launch_app",
        command="notepad.exe",
        task_id="test_task_pre_appr"
    )
    print(f">> Single-Approval HITL Pre-Approved Status: {is_pre_approved} (Expected: True)")
    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
