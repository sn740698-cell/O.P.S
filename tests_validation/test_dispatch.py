import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 540, "height": 840})
    conv_id = f"test_conv_{int(time.time())}"
    print(f"Opening cockpit with conv_id={conv_id}...")
    page.goto(f"http://localhost:3000/?mode=cockpit&conv_id={conv_id}", wait_until="networkidle")
    time.sleep(2)
    
    print("Typing prompt into input...")
    page.locator("#ops-command-input").click()
    page.locator("#ops-command-input").fill("What is Python GIL?")
    page.keyboard.press("Enter")
    print("Pressed Enter, waiting 5 seconds...")
    time.sleep(5)
    
    print("Checking status on page...")
    body_text = page.inner_text("body")
    print("Snippet:", body_text[:400])
    browser.close()
