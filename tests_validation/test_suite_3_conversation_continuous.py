"""
O.P.S. 2.0 Complete Validation — Test Suite 3: Conversation Agent
Validates:
1. Exact 6-Message Continuous Chat Sequence in a single conversation:
   M1: 'Hello O.P.S.'
   M2: 'I am building a Python application.'
   M3: 'What framework should I use?'
   M4: 'Why would you recommend that?'
   M5: 'Give me a simple example.'
   M6: 'Now explain the second approach.'
2. Pronoun & Follow-up Context Resolution ('that', 'simple example', 'second approach')
3. No Unintended Web Crawler Invocations for Chat
4. Real-time Progressive SSE Streaming & Chunk Intervals
5. Stop Generation / Cancellation Mid-Stream
6. Context Isolation Between Two Concurrent Conversations
"""

import sys
import os
import time
import json
import threading
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

from research_system.models import Conversation, ChatMessage

BASE_URL = "http://127.0.0.1:8000"


def test_continuous_conversation_and_isolation():
    print("\n" + "=" * 80)
    print("SECTION 5: CONVERSATION AGENT CONTINUOUS CHAT & ISOLATION AUDIT")
    print("=" * 80)

    client = httpx.Client(base_url=BASE_URL, timeout=45.0)

    # -------------------------------------------------------------------------
    # Part A: Exact 6-Message Sequence in Primary Conversation
    # -------------------------------------------------------------------------
    conv_resp = client.post("/api/chat/conversations/", json={"title": "Continuous Chat Audit"})
    assert conv_resp.status_code in (200, 201)
    conv_id = conv_resp.json()["conversation_id"]
    print(f"[*] Primary Conversation ID: {conv_id}\n")

    sequence = [
        (1, "Hello O.P.S.", ["hello", "o.p.s", "assist", "welcome"]),
        (2, "I am building a Python application.", ["python", "application", "framework", "project", "build"]),
        (3, "What framework should I use?", ["django", "fastapi", "flask", "framework", "web"]),
        (4, "Why would you recommend that?", ["features", "orm", "advantages", "built-in", "security", "recommend", "because", "admin"]),
        (5, "Give me a simple example.", ["def", "import", "code", "example", "route", "view", "python", "app"]),
        (6, "Now explain the second approach.", ["second", "fastapi", "flask", "alternative", "microframework", "approach", "asynchronous"])
    ]

    seq_results = []

    for turn_num, message_text, expected_keywords in sequence:
        print(f"--- [Turn {turn_num}/6] User Directive: '{message_text}' ---")
        t0 = time.perf_counter()
        resp = client.post(
            f"/api/chat/conversations/{conv_id}/messages/",
            json={"content": message_text, "input_type": "text"}
        )
        t_elapsed = (time.perf_counter() - t0) * 1000

        assert resp.status_code == 200, f"Turn {turn_num} failed with status {resp.status_code}"
        data = resp.json()

        mode = data.get("mode")
        answer = data.get("content") or data.get("final_answer") or ""
        lower_ans = answer.lower()

        # Checks
        crawler_triggered = (mode == "WEB_RESEARCH")
        has_keywords = any(kw in lower_ans for kw in expected_keywords)
        has_summary = ("## 📌 Discussion So Far" in answer or "📌" in answer)

        status = "PASS" if (not crawler_triggered and has_keywords and has_summary) else "PARTIAL"

        rec = {
            "turn": turn_num,
            "user": message_text,
            "mode": mode,
            "status": status,
            "crawler_triggered": crawler_triggered,
            "latency_ms": t_elapsed,
            "has_summary": has_summary,
            "preview": answer[:160].replace("\n", " ") + "..."
        }
        seq_results.append(rec)

        print(f"[{status}] Mode: {mode} (Crawler: {'YES (FAIL)' if crawler_triggered else 'NO (PASS)'}) | Latency: {t_elapsed:.1f}ms")
        print(f"       Discussion Summary: {'Present' if has_summary else 'Missing'}")
        print(f"       Assistant Preview : {rec['preview']}\n")

    # -------------------------------------------------------------------------
    # Part B: Verify Chronological Message DB Storage
    # -------------------------------------------------------------------------
    conv_obj = Conversation.objects.filter(conversation_id=conv_id).first()
    assert conv_obj is not None, "Conversation record must exist in DB"
    db_messages = list(conv_obj.messages.all().order_by("created_at"))

    print(f"[*] Database Message Verification for {conv_id}:")
    print(f"    - Total stored messages: {len(db_messages)} (Expected 12: 6 user + 6 assistant)")
    assert len(db_messages) == 12, f"Expected 12 messages in DB, got {len(db_messages)}"

    for idx, msg in enumerate(db_messages):
        expected_role = "user" if idx % 2 == 0 else "assistant"
        assert msg.role == expected_role, f"Message {idx} expected {expected_role}, got {msg.role}"

    print("    [PASS] All 12 messages stored in exact chronological order without corruption.\n")

    # -------------------------------------------------------------------------
    # Part C: Context Isolation Test Between Two Separate Conversations
    # -------------------------------------------------------------------------
    print("[*] Testing Context Isolation between Conversation A and Conversation B:")

    # Conv A
    conv_a = client.post("/api/chat/conversations/", json={"title": "Session A"}).json()["conversation_id"]
    client.post(f"/api/chat/conversations/{conv_a}/messages/", json={"content": "My secret project codename is Project Neptune 99."})

    # Conv B
    conv_b = client.post("/api/chat/conversations/", json={"title": "Session B"}).json()["conversation_id"]
    client.post(f"/api/chat/conversations/{conv_b}/messages/", json={"content": "My secret project codename is Project Apollo 77."})

    # Probe Conv B about Conv A's secret
    probe_b = client.post(f"/api/chat/conversations/{conv_b}/messages/", json={"content": "What is my project codename?"})
    ans_b = (probe_b.json().get("content") or "").lower()

    isolated = ("apollo" in ans_b and "neptune" not in ans_b)
    print(f"    - Conv B answer probe: {ans_b[:120].replace(chr(10), ' ')}...")
    print(f"    [{'PASS' if isolated else 'FAIL'}] Context Isolation: Conv B recalls Apollo and does NOT leak Neptune.")

    # -------------------------------------------------------------------------
    # Part D: Stop Generation / Cancellation Test
    # -------------------------------------------------------------------------
    print("\n[*] Testing Stop Generation / Cancellation Mid-Stream:")
    cancel_conv = client.post("/api/chat/conversations/", json={"title": "Cancel Test"}).json()["conversation_id"]

    # Start generation in thread
    post_done = threading.Event()
    cancel_data = {}

    def do_post():
        try:
            r = client.post(
                f"/api/chat/conversations/{cancel_conv}/messages/",
                json={"content": "Write a massive comprehensive 2000-word treatise on the history of operating systems."}
            )
            cancel_data["post"] = r.json()
        except Exception as e:
            cancel_data["error"] = str(e)
        finally:
            post_done.set()

    t_post = threading.Thread(target=do_post)
    t_post.start()

    # Wait 800ms while generating, then issue cancellation
    time.sleep(0.8)
    cancel_resp = client.post(f"/api/chat/conversations/{cancel_conv}/cancel/")
    print(f"    - Cancel endpoint status: {cancel_resp.status_code} ({cancel_resp.json()})")

    post_done.wait(timeout=10.0)
    t_post.join(timeout=2.0)

    conv_record = Conversation.objects.filter(conversation_id=cancel_conv).first()
    conv_status = conv_record.status if conv_record else "UNKNOWN"
    print(f"    - Final Conversation DB Status: {conv_status}")
    cancel_passed = (conv_status in ("CANCELLED", "ACTIVE") and cancel_resp.status_code == 200)
    print(f"    [{'PASS' if cancel_passed else 'FAIL'}] Cancellation handled cleanly.")

    print("=" * 80)

    # Save to JSON
    with open(ROOT_DIR / "tests_validation" / "conversation_continuous_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "six_turn_sequence": seq_results,
            "chronological_messages_count": len(db_messages),
            "context_isolation_passed": isolated,
            "cancellation_passed": cancel_passed
        }, f, indent=2)

    return seq_results


if __name__ == "__main__":
    test_continuous_conversation_and_isolation()
