import time
import json
import urllib.request
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def run_test(prompt, expected_mode=None):
    print(f"\n========================================================")
    print(f"PROMPT: {prompt}")
    print(f"EXPECTED MODE: {expected_mode}")
    print(f"========================================================")
    t0 = time.time()
    url = "http://127.0.0.1:8000/api/research/execute/"
    payload = json.dumps({
        "query": prompt,
        "input_type": "text"
    }).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"REQUEST FAILED: {e}")
        return None
        
    t1 = time.time()
    duration = t1 - t0
    mode = data.get("response_mode") or data.get("mode")
    answer = data.get("final_answer") or data.get("content") or ""
    citations = data.get("citations", [])
    stages = data.get("stages", [])
    
    print(f"ACTUAL MODE: {mode} (Match: {mode == expected_mode if expected_mode else 'N/A'})")
    print(f"TOTAL DURATION: {duration:.2f}s")
    print(f"CITATIONS COUNT: {len(citations)}")
    for c in citations[:3]:
        print(f"  - [{c.get('index')}] {c.get('title')} -> {c.get('url')}")
    print(f"HAS DISCUSSION SO FAR: {'## 📌 Discussion So Far' in answer}")
    print(f"ANSWER PREVIEW:\n{answer[:400]}...")
    
    return {
        "prompt": prompt,
        "expected_mode": expected_mode,
        "actual_mode": mode,
        "duration": duration,
        "citations": citations,
        "has_discussion_summary": "## 📌 Discussion So Far" in answer,
        "answer_length": len(answer),
        "answer": answer
    }

if __name__ == "__main__":
    test_type = sys.argv[1] if len(sys.argv) > 1 else "A"
    if test_type == "A":
        run_test("Explain how a Python decorator works with an example.", "LLM")
    elif test_type == "B":
        run_test("What is the latest stable Python release?", "WEB")
    elif test_type == "C":
        run_test("Explain the architecture of LangGraph and research its latest major features.", "HYBRID")
    elif test_type == "D":
        run_test("Is Python 2 still officially supported or completely deprecated?", "WEB")
    elif test_type == "E":
        run_test("What are the new syntax additions in Python 4.2?", "WEB")
    elif test_type == "ALL":
        for t in ["A", "B", "C", "D", "E"]:
            run_test(t)
