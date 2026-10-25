from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 800})

    page.goto("https://www.wikipedia.org")

    # Find the search box by what it IS (a search box), not by its position
    box = page.get_by_role("searchbox").first
    box.fill("hello")                       # type into it
    print("Typed:", box.input_value())      # read back what's in the box

    page.wait_for_timeout(1500)             # pause 1.5 s so you can see it
    page.screenshot(path="runs/typed.png")
    browser.close()