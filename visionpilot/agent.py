"""VisionPilot's loop: look, decide, guard, act, check, repeat.

run(task, start_url, approve) does a whole task by itself and returns a
log. It stops when:
  - the model says "done" and a final look confirms it   -> status "done"
  - 3 steps fail in a row                                -> status "needs_help"
  - 15 steps have been used                              -> status "stopped"
  - the human says no at an approval                     -> status "stopped"
Every photo and decision is saved in runs/<date-time>/ with a log.json.
"""
import json
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from .executor import execute
from .observe import observe
from .planner import next_step
from .safety import ASK, REFUSE, check
from .verifier import final_check, verify


def _describe(step, obs):
    """A short human-readable line for one step, e.g. click [5] "Save settings"."""
    text = ""
    if step.element_id and 1 <= step.element_id <= len(obs.elements):
        text = f' "{obs.elements[step.element_id - 1]["text"]}"'
    target = f" [{step.element_id}]{text}" if step.element_id else ""
    value = f" {step.value!r}" if step.value and step.action != "done" else ""
    return f"{step.action}{target}{value}"


def run(task, start_url, approve, max_steps=15, max_failures=3,
        headless=False, run_dir=None):
    run_dir = Path(run_dir or f"runs/{datetime.now():%Y%m%d-%H%M%S}")
    run_dir.mkdir(parents=True, exist_ok=True)
    log = {"task": task, "status": "running", "message": "", "steps": []}

    def save():
        (run_dir / "log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")

    def finish(status, message):
        log.update(status=status, message=message)
        save()
        print(f"\n== {status.upper()}: {message}\n   (photos and log in {run_dir})")
        return log

    history, failures = [], 0
    print(f"Task: {task}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        try:
            page.goto(start_url)
            page.wait_for_timeout(2000)            # let the page finish loading

            for n in range(1, max_steps + 1):
                obs = observe(page, run_dir, n)
                entry = {"n": n, "url": obs.url, "labeled": obs.labeled_path}
                log["steps"].append(entry)

                # 1. Decide
                try:
                    step, _ = next_step(task, obs, history)
                except ValueError as err:
                    entry["error"] = str(err)
                    history.append(f"FAILED: no valid step ({err})")
                    failures += 1
                    print(f"Step {n}: could not get a valid step")
                    save()
                    if failures >= max_failures:
                        return finish("needs_help", f"{max_failures} failures in a row")
                    continue

                label = _describe(step, obs)
                entry.update(step=step.model_dump(), label=label)
                print(f"Step {n}: {label}  ({step.reason})")

                # 2. Finished? Confirm with one more look.
                if step.action == "done":
                    fc = final_check(task, step.value, obs.raw_path)
                    entry["final"] = fc.model_dump()
                    if fc.complete:
                        return finish("done", step.value)
                    history.append(f"DONE REJECTED by final check: {fc.reason}")
                    failures += 1
                    print(f"   final check says not finished: {fc.reason}")
                else:
                    # 3. Guard
                    decision, why = check(step, obs)
                    entry["guard"] = {"decision": decision, "why": why}
                    if decision == REFUSE:
                        history.append(f"REFUSED: {label} ({why})")
                        failures += 1
                        print(f"   refused: {why}")
                    elif decision == ASK and not approve(step, obs, why):
                        entry["approved"] = False
                        return finish("stopped", "not approved by the human")
                    else:
                        # 4. Act, then 5. Check with a second photo
                        error = execute(page, step, obs)
                        after = str(run_dir / f"step-{n:02d}-after.png")
                        page.screenshot(path=after)
                        if error:
                            ok, reason = False, error
                        else:
                            verdict = verify(step, obs.raw_path, after)
                            ok, reason = verdict.success, verdict.reason
                        entry["check"] = {"success": ok, "reason": reason}
                        if ok:
                            history.append(f"OK: {label}")
                            failures = 0
                            print(f"   worked: {reason}")
                        else:
                            history.append(f"FAILED: {label} -> {reason}")
                            failures += 1
                            print(f"   FAILED: {reason}")
                save()
                if failures >= max_failures:
                    return finish("needs_help", f"{max_failures} failures in a row: {history[-1]}")

            return finish("stopped", f"step limit of {max_steps} reached")
        finally:
            browser.close()
