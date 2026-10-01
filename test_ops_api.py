import json
import urllib.request

base_url = "http://localhost:8000/api/v1"

def test_endpoint(name, url, method="GET", payload=None):
    print(f"Testing [{name}] {method} {url}...")
    try:
        data = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if payload else {}, method=method)
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            status_code = response.status
            print(f"  --> PASS (Status {status_code}): {res_body[:120]}...\n")
            return True
    except Exception as e:
        print(f"  --> FAIL: {e}\n")
        return False

results = []
results.append(test_endpoint("Health Check", f"{base_url}/health/"))
results.append(test_endpoint("Intent Router", f"{base_url}/router/", "POST", {"prompt": "Scrape latest news"}))
results.append(test_endpoint("Plan Reasoning", f"{base_url}/plan/", "POST", {"prompt": "Build React app"}))
results.append(test_endpoint("Code Synthesizer", f"{base_url}/coding/", "POST", {"task": "Write python function"}))
results.append(test_endpoint("Wispr Voice Status", f"{base_url}/voice/status/"))
results.append(test_endpoint("Wispr Voice Toggle", f"{base_url}/voice/toggle/", "POST"))
results.append(test_endpoint("Wispr Voice Transcript", f"{base_url}/voice/transcript/", "POST", {"transcript": "Hey OPS open chrome", "auto_dispatch": False}))
results.append(test_endpoint("Full Orchestration", f"{base_url}/orchestrate/", "POST", {"prompt": "Hello OPS"}))

passed = sum(1 for r in results if r)
total = len(results)
print(f"==================================================")
print(f"VERIFICATION RESULT: {passed}/{total} ENDPOINTS PASSED")
print(f"==================================================")
