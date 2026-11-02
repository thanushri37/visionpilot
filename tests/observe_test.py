"""Eyes test: number every clickable thing on the three practice pages.

Start the practice website first (python target_app/app.py), then run
from the project folder:  python -m tests.observe_test
Pictures are saved in runs/observe-test/.
"""
from playwright.sync_api import sync_playwright

from visionpilot.observe import observe

APP = "http://localhost:5000"
OUT = "runs/observe-test"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 800})

    page.goto(f"{APP}/dashboard")
    obs = observe(page, OUT, 1)
    print("DASHBOARD\n" + obs.element_lines() + "\n")

    page.goto(f"{APP}/settings")
    obs = observe(page, OUT, 2)
    print("SETTINGS\n" + obs.element_lines() + "\n")

    page.goto(f"{APP}/settings?popup=1")
    page.locator("#threshold").fill("80")      # typing makes the pop-up appear
    page.wait_for_timeout(500)
    obs = observe(page, OUT, 3)
    print("SETTINGS WITH POP-UP\n" + obs.element_lines())

    browser.close()

print(f"\nOpen the *-labeled.png pictures in {OUT} to check the boxes.")
