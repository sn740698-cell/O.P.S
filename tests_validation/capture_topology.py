from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 960}, device_scale_factor=2)
    page.goto("http://localhost:3000/", wait_until="networkidle")
    time.sleep(2)
    
    # Click 02: LIVE ORCHESTRATION button
    btn = page.locator("button:has-text('02: LIVE ORCHESTRATION')")
    if btn.count() > 0:
        btn.first.click()
        time.sleep(3)
        page.screenshot(path="assets/screenshots/agent_orchestration_topology.png")
        print("Saved assets/screenshots/agent_orchestration_topology.png")
    else:
        print("Button not found!")
    browser.close()
