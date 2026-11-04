"""
O.P.S. 2.0 — Complete Mode Execution and Live Screenshot Capture
Runs dedicated tasks across all 6 execution modes through the running O.P.S. 2.0
Cockpit and Ambient OS Dashboard, verifying end-to-end responses and saving high-res
screenshots for the documentation.
"""

import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "screenshots"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

COCKPIT_URL = "http://localhost:3000/?mode=cockpit"
DASHBOARD_URL = "http://localhost:3000/"

def run():
    print("=" * 70, flush=True)
    print(" O.P.S. 2.0 — LIVE MODE EXECUTION & SCREENSHOT ENGINE", flush=True)
    print("=" * 70, flush=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Dedicated Cockpit context (High-DPI 2x scale, 560x860)
        cockpit_ctx = browser.new_context(
            viewport={"width": 560, "height": 860},
            device_scale_factor=2
        )
        page = cockpit_ctx.new_page()

        # Helper to send directive and wait for completion
        def send_directive(prompt: str):
            print(f"\n[DISPATCH] \"{prompt}\"", flush=True)
            page.locator("#ops-command-input").click()
            page.locator("#ops-command-input").fill(prompt)
            page.keyboard.press("Enter")

        # -------------------------------------------------------------
        # Mode 1: LLM Reasoning Mode
        # -------------------------------------------------------------
        print("\n>>> [1/6] EXECUTING LLM MODE...", flush=True)
        page.goto(COCKPIT_URL, wait_until="networkidle")
        time.sleep(2)
        
        send_directive("Explain the architecture of Transformer Multi-Head Attention and its computational complexity.")
        # Wait until response completes (SEND button re-appears)
        print("Waiting for LLM reasoning to complete...", flush=True)
        page.wait_for_selector("button:has-text('SEND')", timeout=90000)
        time.sleep(2)
        
        llm_path = os.path.join(OUTPUT_DIR, "mode_1_llm_reasoning.png")
        page.screenshot(path=llm_path)
        print(f"  [SAVED] {llm_path}", flush=True)

        # -------------------------------------------------------------
        # Mode 2: Web Research Mode
        # -------------------------------------------------------------
        print("\n>>> [2/6] EXECUTING WEB RESEARCH MODE...", flush=True)
        send_directive("What are the key new features and improvements in Django 5.1 and Python 3.13?")
        print("Waiting for Web research, validation, and citation synthesis...", flush=True)
        page.wait_for_selector("button:has-text('SEND')", timeout=120000)
        time.sleep(2)
        
        web_path = os.path.join(OUTPUT_DIR, "mode_2_web_research.png")
        page.screenshot(path=web_path)
        print(f"  [SAVED] {web_path}", flush=True)

        # -------------------------------------------------------------
        # Mode 3: Hybrid Reasoning Mode
        # -------------------------------------------------------------
        print("\n>>> [3/6] EXECUTING HYBRID MODE...", flush=True)
        send_directive("Compare PyTorch vs JAX performance for modern LLM inference with latest benchmarks.")
        print("Waiting for Hybrid dual-branch synthesis to complete...", flush=True)
        page.wait_for_selector("button:has-text('SEND')", timeout=120000)
        time.sleep(2)
        
        hybrid_path = os.path.join(OUTPUT_DIR, "mode_3_hybrid_reasoning.png")
        page.screenshot(path=hybrid_path)
        print(f"  [SAVED] {hybrid_path}", flush=True)

        # -------------------------------------------------------------
        # Mode 4: Desktop Automation Mode & HITL Approval Modal
        # -------------------------------------------------------------
        print("\n>>> [4/6] EXECUTING DESKTOP AUTOMATION MODE...", flush=True)
        send_directive("Open Notepad and type 'O.P.S. 2.0 Desktop Automation System Verified'.")
        print("Waiting for HITL Approval Gate modal...", flush=True)
        page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=25000)
        time.sleep(1)
        
        # Capture dedicated HITL Modal screenshot
        hitl_path = os.path.join(OUTPUT_DIR, "hitl_approval_modal_live.png")
        page.screenshot(path=hitl_path)
        print(f"  [SAVED HITL MODAL] {hitl_path}", flush=True)
        
        # Click Accept
        print("Accepting execution in modal...", flush=True)
        accept_btn = page.locator("button:has-text('ACCEPT AND EXECUTE')")
        if accept_btn.count() > 0:
            accept_btn.click()
        else:
            page.locator("button:has-text('ACCEPT')").click()
            
        print("Waiting for desktop execution to complete...", flush=True)
        page.wait_for_selector("button:has-text('SEND')", timeout=45000)
        time.sleep(2)
        
        desktop_path = os.path.join(OUTPUT_DIR, "mode_4_desktop_automation.png")
        page.screenshot(path=desktop_path)
        print(f"  [SAVED] {desktop_path}", flush=True)

        # -------------------------------------------------------------
        # Mode 5: Browser Automation Mode
        # -------------------------------------------------------------
        print("\n>>> [5/6] EXECUTING BROWSER AUTOMATION MODE...", flush=True)
        send_directive("Search Google for 'OpenAI Sora official documentation'.")
        print("Waiting for Browser HITL Approval Gate modal...", flush=True)
        page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=25000)
        time.sleep(1)
        
        print("Accepting browser execution in modal...", flush=True)
        accept_btn = page.locator("button:has-text('ACCEPT AND EXECUTE')")
        if accept_btn.count() > 0:
            accept_btn.click()
        else:
            page.locator("button:has-text('ACCEPT')").click()
            
        print("Waiting for browser execution to complete...", flush=True)
        page.wait_for_selector("button:has-text('SEND')", timeout=45000)
        time.sleep(2)
        
        browser_path = os.path.join(OUTPUT_DIR, "mode_5_browser_automation.png")
        page.screenshot(path=browser_path)
        print(f"  [SAVED] {browser_path}", flush=True)

        # -------------------------------------------------------------
        # Mode 6: Hybrid Automation Mode
        # -------------------------------------------------------------
        print("\n>>> [6/6] EXECUTING HYBRID AUTOMATION MODE...", flush=True)
        send_directive("Open the Django documentation, copy its actual URL, open Notepad and save that URL in a text file on my Desktop.")
        print("Waiting for Hybrid Automation HITL Approval Gate modal...", flush=True)
        page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=25000)
        time.sleep(1)
        
        print("Accepting hybrid automation execution in modal...", flush=True)
        accept_btn = page.locator("button:has-text('ACCEPT AND EXECUTE')")
        if accept_btn.count() > 0:
            accept_btn.click()
        else:
            page.locator("button:has-text('ACCEPT')").click()
            
        print("Waiting for hybrid automation to complete...", flush=True)
        page.wait_for_selector("button:has-text('SEND')", timeout=60000)
        time.sleep(2)
        
        hybrid_auto_path = os.path.join(OUTPUT_DIR, "mode_6_hybrid_automation.png")
        page.screenshot(path=hybrid_auto_path)
        print(f"  [SAVED] {hybrid_auto_path}", flush=True)

        # Save general standalone cockpit hud screenshot
        popup_path = os.path.join(OUTPUT_DIR, "popup_cockpit_hud.png")
        page.screenshot(path=popup_path)
        print(f"  [SAVED] {popup_path}", flush=True)

        cockpit_ctx.close()

        # -------------------------------------------------------------
        # Ambient Dashboard & Fleet Topology Views
        # -------------------------------------------------------------
        print("\n>>> [DASHBOARD] CAPTURING AMBIENT DASHBOARD & FLEET TOPOLOGY...", flush=True)
        dash_ctx = browser.new_context(
            viewport={"width": 1600, "height": 960},
            device_scale_factor=2
        )
        dash_page = dash_ctx.new_page()
        dash_page.goto(DASHBOARD_URL, wait_until="networkidle")
        time.sleep(3)
        
        dash_main_path = os.path.join(OUTPUT_DIR, "dashboard_main.png")
        dash_page.screenshot(path=dash_main_path)
        print(f"  [SAVED] {dash_main_path}", flush=True)

        # Topology canvas view
        topo_tab = dash_page.locator("button:has-text('FLEET TOPOLOGY'), button:has-text('TOPOLOGY'), button:has-text('AGENTS')")
        if topo_tab.count() > 0:
            topo_tab.first.click()
            time.sleep(2)
            topo_path = os.path.join(OUTPUT_DIR, "agent_orchestration_topology.png")
            dash_page.screenshot(path=topo_path)
            print(f"  [SAVED] {topo_path}", flush=True)

        # Agent Inspector modal
        agent_node = dash_page.locator(".agent-node, [data-agent-id], canvas")
        if agent_node.count() > 0:
            try:
                agent_node.first.click()
                time.sleep(1)
                inspector_path = os.path.join(OUTPUT_DIR, "agent_inspector_modal.png")
                dash_page.screenshot(path=inspector_path)
                print(f"  [SAVED] {inspector_path}", flush=True)
            except Exception as e:
                print(f"  [NOTE] Inspector click: {e}")

        dash_ctx.close()
        browser.close()
        print("\n" + "=" * 70, flush=True)
        print(" ALL MODES EXECUTED & SCREENSHOTS SUCCESSFULLY CAPTURED!", flush=True)
        print("=" * 70, flush=True)

if __name__ == "__main__":
    run()
