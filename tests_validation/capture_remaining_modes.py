import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
COCKPIT_URL = "http://localhost:3000/?mode=cockpit"
DASHBOARD_URL = "http://localhost:3000/"
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "screenshots"))

# 1. Get active conversation
resp = requests.get(f"{BASE_URL}/api/chat/conversations/active/")
conv_id = resp.json()["conversation_id"]
print(f"Active Conversation ID: {conv_id}")

# -------------------------------------------------------------
# Mode 3: Hybrid Mode Execution
# -------------------------------------------------------------
print("\n--- [1/4] Executing Task in Mode 3: Hybrid Mode ---")
prompt_hybrid = "Compare PyTorch vs JAX performance for modern LLM inference with latest benchmarks."
msg_resp = requests.post(
    f"{BASE_URL}/api/chat/conversations/{conv_id}/messages/",
    json={"content": prompt_hybrid, "input_type": "text"},
    timeout=120
)
print("Hybrid Mode status code:", msg_resp.status_code)
if msg_resp.ok:
    data = msg_resp.json()
    print("Mode:", data.get("response_mode") or data.get("mode"))
    print("Snippet:", data.get("content", "")[:180])

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 560, "height": 860}, device_scale_factor=2)
    page.goto(COCKPIT_URL, wait_until="networkidle")
    time.sleep(3)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    hybrid_shot = os.path.join(OUTPUT_DIR, "mode_3_hybrid_reasoning.png")
    page.screenshot(path=hybrid_shot)
    print(f"Saved: {hybrid_shot}")

    # -------------------------------------------------------------
    # Mode 5: Browser Automation Mode
    # -------------------------------------------------------------
    print("\n--- [2/4] Executing Task in Mode 5: Browser Automation Mode ---")
    page.locator("#ops-command-input").click()
    page.locator("#ops-command-input").fill("Search Google for 'OpenAI Sora official documentation'.")
    page.keyboard.press("Enter")
    print("Waiting for Browser HITL Modal...")
    page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=25000)
    time.sleep(1)
    print("Approving browser execution...")
    page.locator("button:has-text('ACCEPT AND EXECUTE')").click()
    print("Waiting for browser execution to complete...")
    time.sleep(6)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    browser_shot = os.path.join(OUTPUT_DIR, "mode_5_browser_automation.png")
    page.screenshot(path=browser_shot)
    print(f"Saved: {browser_shot}")

    # -------------------------------------------------------------
    # Mode 6: Hybrid Automation Mode
    # -------------------------------------------------------------
    print("\n--- [3/4] Executing Task in Mode 6: Hybrid Automation Mode ---")
    page.locator("#ops-command-input").click()
    page.locator("#ops-command-input").fill("Open the Django documentation, copy its actual URL, open Notepad and save that URL in a text file on my Desktop.")
    page.keyboard.press("Enter")
    print("Waiting for Hybrid Automation HITL Modal...")
    page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=25000)
    time.sleep(1)
    print("Approving hybrid automation execution...")
    page.locator("button:has-text('ACCEPT AND EXECUTE')").click()
    print("Waiting for hybrid execution...")
    time.sleep(8)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    hybrid_auto_shot = os.path.join(OUTPUT_DIR, "mode_6_hybrid_automation.png")
    page.screenshot(path=hybrid_auto_shot)
    print(f"Saved: {hybrid_auto_shot}")

    # General Cockpit HUD view
    popup_hud = os.path.join(OUTPUT_DIR, "popup_cockpit_hud.png")
    page.screenshot(path=popup_hud)
    print(f"Saved: {popup_hud}")

    # -------------------------------------------------------------
    # Dashboard & Topology
    # -------------------------------------------------------------
    print("\n--- [4/4] Capturing Main Dashboard & Topology Views ---")
    dash_page = browser.new_page(viewport={"width": 1600, "height": 960}, device_scale_factor=2)
    dash_page.goto(DASHBOARD_URL, wait_until="networkidle")
    time.sleep(3)
    dash_shot = os.path.join(OUTPUT_DIR, "dashboard_main.png")
    dash_page.screenshot(path=dash_shot)
    print(f"Saved: {dash_shot}")

    # Click Fleet Topology / canvas tab
    topo_btn = dash_page.locator("button:has-text('FLEET TOPOLOGY'), button:has-text('TOPOLOGY')")
    if topo_btn.count() > 0:
        topo_btn.first.click()
        time.sleep(2)
        topo_shot = os.path.join(OUTPUT_DIR, "agent_orchestration_topology.png")
        dash_page.screenshot(path=topo_shot)
        print(f"Saved: {topo_shot}")

    # Click Inspector
    agent_box = dash_page.locator(".agent-node, [data-agent-id], canvas")
    if agent_box.count() > 0:
        try:
            agent_box.first.click()
            time.sleep(1)
            inspector_shot = os.path.join(OUTPUT_DIR, "agent_inspector_modal.png")
            dash_page.screenshot(path=inspector_shot)
            print(f"Saved: {inspector_shot}")
        except Exception as e:
            print("Note agent click:", e)

    browser.close()
    print("\n[SUCCESS] All mode executions and screenshots completed!")
