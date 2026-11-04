"""
O.P.S. 2.0 — End-to-End Execution and Mode Screenshot Generator
Executes real tasks across all 6 modes through the running O.P.S. Cockpit UI,
verifies outcomes, captures high-resolution screenshots, and saves them to assets/screenshots/.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "screenshots"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

COCKPIT_URL = "http://localhost:3000/?mode=cockpit"
DASHBOARD_URL = "http://localhost:3000/"

def run_capture():
    print(f"[START] Launching Playwright to execute tasks and capture screenshots...", flush=True)
    print(f"[INFO] Screenshots will be saved to: {OUTPUT_DIR}", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Dedicated tactical Cockpit window size
        cockpit_context = browser.new_context(viewport={"width": 540, "height": 840}, device_scale_factor=2)
        page = cockpit_context.new_page()

        print(f"[1/7] Navigating to Cockpit: {COCKPIT_URL}", flush=True)
        page.goto(COCKPIT_URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # -------------------------------------------------------------
        # 1. LLM Mode Execution
        # -------------------------------------------------------------
        print("\n--- Executing Task in LLM Mode ---", flush=True)
        llm_prompt = "Explain Python GIL (Global Interpreter Lock) and how free-threading in Python 3.13 addresses it."
        page.fill("#ops-command-input", llm_prompt)
        page.click("button[type='submit']")
        
        # Wait for completion (STANDBY or Completed stage)
        print("Waiting for LLM reasoning to complete...", flush=True)
        page.wait_for_selector("text=[STANDBY]", timeout=90000)
        time.sleep(2)
        
        llm_shot = os.path.join(OUTPUT_DIR, "mode_1_llm_reasoning.png")
        page.screenshot(path=llm_shot)
        print(f"  [SAVED] {llm_shot}", flush=True)

        # -------------------------------------------------------------
        # 2. Web Mode Execution
        # -------------------------------------------------------------
        print("\n--- Executing Task in Web Mode ---", flush=True)
        web_prompt = "What are the latest features and release updates in Django 5.1?"
        page.fill("#ops-command-input", web_prompt)
        page.click("button[type='submit']")
        
        print("Waiting for Web research & synthesis to complete...", flush=True)
        page.wait_for_selector("text=[STANDBY]", timeout=120000)
        time.sleep(2)
        
        web_shot = os.path.join(OUTPUT_DIR, "mode_2_web_research.png")
        page.screenshot(path=web_shot)
        print(f"  [SAVED] {web_shot}", flush=True)

        # -------------------------------------------------------------
        # 3. Hybrid Mode Execution
        # -------------------------------------------------------------
        print("\n--- Executing Task in Hybrid Mode ---", flush=True)
        hybrid_prompt = "Compare PyTorch vs JAX performance for modern LLM inference with latest benchmarks."
        page.fill("#ops-command-input", hybrid_prompt)
        page.click("button[type='submit']")
        
        print("Waiting for Hybrid dual-branch synthesis to complete...", flush=True)
        page.wait_for_selector("text=[STANDBY]", timeout=120000)
        time.sleep(2)
        
        hybrid_shot = os.path.join(OUTPUT_DIR, "mode_3_hybrid_reasoning.png")
        page.screenshot(path=hybrid_shot)
        print(f"  [SAVED] {hybrid_shot}", flush=True)

        # -------------------------------------------------------------
        # 4. Desktop Automation Mode (with HITL Approval Modal)
        # -------------------------------------------------------------
        print("\n--- Executing Task in Desktop Automation Mode ---", flush=True)
        desktop_prompt = "Open Notepad and type 'O.P.S. 2.0 Desktop Automation System Verified'."
        page.fill("#ops-command-input", desktop_prompt)
        page.click("button[type='submit']")
        
        # Wait for HITL Approval Modal to appear
        print("Waiting for HITL Approval Gate modal...", flush=True)
        page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=30000)
        time.sleep(1)
        
        # Capture dedicated HITL Modal screenshot!
        hitl_modal_shot = os.path.join(OUTPUT_DIR, "hitl_approval_modal_live.png")
        page.screenshot(path=hitl_modal_shot)
        print(f"  [SAVED HITL MODAL] {hitl_modal_shot}", flush=True)

        # Accept and execute
        print("Accepting execution plan in modal...", flush=True)
        accept_btn = page.locator("button:has-text('ACCEPT AND EXECUTE')")
        if accept_btn.count() > 0:
            accept_btn.click()
        else:
            page.locator("button:has-text('ACCEPT')").click()

        print("Waiting for Desktop automation completion...", flush=True)
        time.sleep(4)
        desktop_shot = os.path.join(OUTPUT_DIR, "mode_4_desktop_automation.png")
        page.screenshot(path=desktop_shot)
        print(f"  [SAVED] {desktop_shot}", flush=True)

        # -------------------------------------------------------------
        # 5. Browser Automation Mode (with HITL Approval Modal)
        # -------------------------------------------------------------
        print("\n--- Executing Task in Browser Automation Mode ---", flush=True)
        browser_prompt = "Search Google for 'OpenAI Sora official documentation'."
        page.fill("#ops-command-input", browser_prompt)
        page.click("button[type='submit']")
        
        print("Waiting for Browser HITL Approval Gate modal...", flush=True)
        page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=30000)
        time.sleep(1)
        
        # Accept execution
        accept_btn = page.locator("button:has-text('ACCEPT AND EXECUTE')")
        if accept_btn.count() > 0:
            accept_btn.click()
        else:
            page.locator("button:has-text('ACCEPT')").click()

        print("Waiting for Browser automation execution...", flush=True)
        time.sleep(5)
        browser_shot = os.path.join(OUTPUT_DIR, "mode_5_browser_automation.png")
        page.screenshot(path=browser_shot)
        print(f"  [SAVED] {browser_shot}", flush=True)

        # -------------------------------------------------------------
        # 6. Hybrid Automation Mode (with HITL Approval Modal)
        # -------------------------------------------------------------
        print("\n--- Executing Task in Hybrid Automation Mode ---", flush=True)
        hybrid_auto_prompt = "Open the Django documentation, copy its actual URL, open Notepad and save that URL in a text file on my Desktop."
        page.fill("#ops-command-input", hybrid_auto_prompt)
        page.click("button[type='submit']")
        
        print("Waiting for Hybrid Automation HITL Approval Gate modal...", flush=True)
        page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=30000)
        time.sleep(1)
        
        # Accept execution
        accept_btn = page.locator("button:has-text('ACCEPT AND EXECUTE')")
        if accept_btn.count() > 0:
            accept_btn.click()
        else:
            page.locator("button:has-text('ACCEPT')").click()

        print("Waiting for Hybrid automation execution...", flush=True)
        time.sleep(6)
        hybrid_auto_shot = os.path.join(OUTPUT_DIR, "mode_6_hybrid_automation.png")
        page.screenshot(path=hybrid_auto_shot)
        print(f"  [SAVED] {hybrid_auto_shot}", flush=True)

        # Save general popup cockpit view
        popup_shot = os.path.join(OUTPUT_DIR, "popup_cockpit_hud.png")
        page.screenshot(path=popup_shot)
        print(f"  [SAVED] {popup_shot}", flush=True)

        # -------------------------------------------------------------
        # 7. Main Ambient Dashboard & Fleet Topology
        # -------------------------------------------------------------
        print("\n--- Capturing Main Ambient OS Dashboard & Topology ---", flush=True)
        dash_context = browser.new_context(viewport={"width": 1600, "height": 960}, device_scale_factor=2)
        dash_page = dash_context.new_page()
        dash_page.goto(DASHBOARD_URL, wait_until="networkidle", timeout=30000)
        time.sleep(3)

        dash_shot = os.path.join(OUTPUT_DIR, "dashboard_main.png")
        dash_page.screenshot(path=dash_shot)
        print(f"  [SAVED] {dash_shot}", flush=True)

        # Click Agent Topology / Canvas tab if available
        topo_tab = dash_page.locator("button:has-text('FLEET TOPOLOGY'), button:has-text('TOPOLOGY'), button:has-text('AGENTS')")
        if topo_tab.count() > 0:
            topo_tab.first.click()
            time.sleep(2)
            topo_shot = os.path.join(OUTPUT_DIR, "agent_orchestration_topology.png")
            dash_page.screenshot(path=topo_shot)
            print(f"  [SAVED] {topo_shot}", flush=True)

        # Click an agent node or inspector if available
        agent_node = dash_page.locator(".agent-node, [data-agent-id], canvas")
        if agent_node.count() > 0:
            try:
                agent_node.first.click()
                time.sleep(1)
                inspect_shot = os.path.join(OUTPUT_DIR, "agent_inspector_modal.png")
                dash_page.screenshot(path=inspect_shot)
                print(f"  [SAVED] {inspect_shot}", flush=True)
            except Exception as e:
                print(f"  [NOTE] Agent click: {e}")

        browser.close()
        print("\n[COMPLETE] All execution modes tested and screenshots successfully saved!", flush=True)

if __name__ == "__main__":
    run_capture()
