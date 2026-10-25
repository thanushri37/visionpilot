from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # 1. Open a visible Chromium window, always the same size
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 800})

    # 2. Go to a simple test website and take a picture
    page.goto("https://example.com")
    page.screenshot(path="runs/hello-1.png")

    # 3. List every link, button and input box, with its position on screen
    for el in page.query_selector_all("a, button, input"):
        print(el.evaluate("e => e.tagName"), repr(el.inner_text()[:40]), el.bounding_box())

    # 4. Click the first link, wait for the new page, take another picture
    page.get_by_role("link").first.click()
    page.wait_for_load_state()
    page.screenshot(path="runs/hello-2.png")

    browser.close()