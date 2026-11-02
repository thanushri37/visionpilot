"""Hands test: do Task B and the Task C pop-up by hand, through the guard.

No model is used: the steps are written here. Start the practice website
first (python target_app/app.py), then run:  python -m tests.executor_test
You will be asked to approve the Save click: type y and press Enter.
"""
import json
import urllib.request

from playwright.sync_api import sync_playwright

from visionpilot.executor import execute
from visionpilot.observe import observe
from visionpilot.safety import ASK, REFUSE, check, terminal_approve
from visionpilot.schema import Step

APP = "http://localhost:5000"
OUT = "runs/executor-test"
n = 0


def number_of(obs, text):
    """Find an element's number by its words (the model does this normally)."""
    return next(e["id"] for e in obs.elements if text.lower() in e["text"].lower())


def do(page, action, text=None, value=None):
    """Look, build one step, pass it through the guard, then act."""
    global n
    n += 1
    obs = observe(page, OUT, n)
    step = Step(action=action, element_id=number_of(obs, text) if text else None,
                value=value, reason="test step")
    decision, why = check(step, obs)
    if decision == REFUSE:
        return f"REFUSED: {why}"
    if decision == ASK and not terminal_approve(step, obs, why):
        return "NOT APPROVED"
    error = execute(page, step, obs)
    return error or "ok"


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    urllib.request.urlopen(urllib.request.Request(f"{APP}/reset", method="POST"))

    print("TASK B by hand")
    page.goto(f"{APP}/dashboard")
    print("  click Settings      ->", do(page, "click", "Settings"))
    print("  type 80             ->", do(page, "type", "Alert threshold", "80"))
    print("  click Save          ->", do(page, "click", "Save settings"))
    print("  page now says       ->", page.locator(".ok").inner_text())
    print("  /state              ->", json.load(urllib.request.urlopen(f"{APP}/state")))

    print("\nTASK C pop-up by hand")
    page.goto(f"{APP}/settings?popup=1")
    print("  type 90 (pop-up!)   ->", do(page, "type", "Alert threshold", "90"))
    print("  click Save (blocked)->", do(page, "click", "Save settings"))
    print("  click Dismiss       ->", do(page, "click", "Dismiss"))

    browser.close()
print("\nExpected: Task B saved 80. In Task C the Save click fails with a")
print("TimeoutError while the pop-up is showing, then Dismiss works.")
