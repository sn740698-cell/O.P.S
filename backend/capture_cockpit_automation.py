import os
import time
from playwright.sync_api import sync_playwright

artifact_dir = r"C:\Users\sn740\.gemini\antigravity\brain\b33e1527-6b85-48e0-91b6-cc515137c118"
os.makedirs(artifact_dir, exist_ok=True)
screenshot_path = os.path.join(artifact_dir, "cockpit_automation_live.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    # Visit popup cockpit
    page.goto("http://localhost:3000/cockpit/popup/", wait_until="networkidle", timeout=15000)
    time.sleep(2)
    # Scroll to bottom if messages exist
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.screenshot(path=screenshot_path, full_page=True)
    print("Screenshot saved to:", screenshot_path)
    browser.close()
