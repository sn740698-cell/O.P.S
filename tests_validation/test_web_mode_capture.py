import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
COCKPIT_URL = "http://localhost:3000/?mode=cockpit"
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "screenshots"))

# Get active conversation
resp = requests.get(f"{BASE_URL}/api/chat/conversations/active/")
active_data = resp.json()
conv_id = active_data["conversation_id"]
print(f"Active Conversation ID: {conv_id}")

print("\n--- Executing Task in Mode 2: Web Research Mode ---")
prompt_web = "What are the latest breakthrough features and improvements in Django 5.1?"
msg_resp = requests.post(
    f"{BASE_URL}/api/chat/conversations/{conv_id}/messages/",
    json={"content": prompt_web, "input_type": "text"},
    timeout=120
)
print("Web Mode status code:", msg_resp.status_code)
if msg_resp.ok:
    data = msg_resp.json()
    print("Mode:", data.get("response_mode") or data.get("mode"))
    print("Snippet:", data.get("content", "")[:200])

print("\nCapturing live Cockpit screenshot for Web Mode...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 560, "height": 860}, device_scale_factor=2)
    page.goto(COCKPIT_URL, wait_until="networkidle")
    time.sleep(3)
    # Scroll to bottom
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    web_shot = os.path.join(OUTPUT_DIR, "mode_2_web_research.png")
    page.screenshot(path=web_shot)
    print(f"Saved: {web_shot}")
    browser.close()
