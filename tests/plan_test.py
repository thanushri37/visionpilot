"""Decisions test: ask the real model for the next step on two pages.

Start the practice website first (python target_app/app.py), then run
from the project folder:  python -m tests.plan_test
This makes 3 real calls to Meta's model.
"""
from playwright.sync_api import sync_playwright

from visionpilot.observe import observe
from visionpilot.planner import next_step

APP = "http://localhost:5000"
OUT = "runs/plan-test"
TASK_A = "Find and summarise the errors on this dashboard."
TASK_B = "Change the alert threshold to 80% and save."


def show(title, step):
    print(f"{title}\n  action={step.action}  element_id={step.element_id}  "
          f"value={step.value!r}  risky={step.risky}\n  reason: {step.reason}\n")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 800})

    page.goto(f"{APP}/dashboard")
    obs = observe(page, OUT, 1)
    show("TASK A on dashboard (expect: done, with the 3 errors)", next_step(TASK_A, obs)[0])
    show("TASK B on dashboard (expect: click 2, Settings)", next_step(TASK_B, obs)[0])

    page.goto(f"{APP}/settings")
    obs = observe(page, OUT, 2)
    show("TASK B on settings (expect: type 80 into 3)", next_step(TASK_B, obs)[0])

    browser.close()
