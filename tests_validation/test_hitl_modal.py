import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 540, "height": 840})
    print("Navigating to Cockpit...")
    page.goto("http://localhost:3000/?mode=cockpit", wait_until="networkidle")
    time.sleep(2)
    
    print("Sending desktop automation prompt...")
    page.locator("#ops-command-input").click()
    page.locator("#ops-command-input").fill("Open Notepad and type 'O.P.S. 2.0 Test'.")
    page.keyboard.press("Enter")
    
    print("Waiting for HITL Modal...")
    modal = page.wait_for_selector("text=HUMAN-IN-THE-LOOP // EXECUTION APPROVAL", timeout=15000)
    print("HITL Modal detected successfully!")
    
    # Take screenshot of HITL modal
    os.makedirs("assets/screenshots", exist_ok=True)
    page.screenshot(path="assets/screenshots/hitl_approval_modal_live.png")
    print("Saved assets/screenshots/hitl_approval_modal_live.png")
    
    # Click Accept
    print("Clicking ACCEPT AND EXECUTE...")
    page.locator("button:has-text('ACCEPT AND EXECUTE')").click()
    
    print("Waiting 6 seconds for execution...")
    time.sleep(6)
    
    page.screenshot(path="assets/screenshots/mode_4_desktop_automation.png")
    print("Saved assets/screenshots/mode_4_desktop_automation.png")
    
    browser.close()
    print("Test passed!")
