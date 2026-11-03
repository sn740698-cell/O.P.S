import time
import os
from playwright.sync_api import sync_playwright

def capture_screenshots():
    output_dir = r"C:\Users\sn740\.gemini\antigravity\brain\b33e1527-6b85-48e0-91b6-cc515137c118"
    os.makedirs(output_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 950})
        page = context.new_page()
        
        print("Navigating to http://localhost:3000...")
        page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
        
        # If splash screen is showing, wait for it or click
        time.sleep(2)
        
        # Click on Tab 2: LIVE ORCHESTRATION & AGENTS
        print("Clicking LIVE ORCHESTRATION & AGENTS tab...")
        tab_btn = page.locator("button:has-text('LIVE ORCHESTRATION')")
        if tab_btn.is_visible():
            tab_btn.click()
            time.sleep(2)
        
        print("Scrolling canvas into view...")
        canvas = page.locator("canvas")
        canvas.scroll_into_view_if_needed()
        time.sleep(1)
        
        # Capture full live topology canvas
        screenshot_path1 = os.path.join(output_dir, "agent_activity_tab_live.png")
        page.screenshot(path=screenshot_path1, full_page=False)
        print(f"Captured screenshot 1: {screenshot_path1}")
        
        # Click on canvas node (page coordinates 215, 637)
        print("Clicking at node 0,0 page coordinates (215, 637)...")
        page.mouse.click(215, 637)
        time.sleep(1)
        
        screenshot_path2 = os.path.join(output_dir, "agent_inspection_modal_live.png")
        page.screenshot(path=screenshot_path2, full_page=False)
        print(f"Captured screenshot 2: {screenshot_path2}")
        
        browser.close()
        print("Finished capturing screenshots.")

if __name__ == "__main__":
    capture_screenshots()
