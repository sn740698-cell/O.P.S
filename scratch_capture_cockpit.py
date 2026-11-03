from playwright.sync_api import sync_playwright
import time
import os

artifact_path = r"C:\Users\sn740\.gemini\antigravity\brain\b33e1527-6b85-48e0-91b6-cc515137c118\cockpit_popup_web_mode_live.png"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 640, "height": 820})
    page.goto("http://localhost:3000/?mode=cockpit", wait_until="networkidle", timeout=30000)
    time.sleep(3)
    page.screenshot(path=artifact_path)
    print("Pop-up Cockpit screenshot saved to:", artifact_path)
    browser.close()
