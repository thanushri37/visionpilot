"""VisionPilot's hands: do one step in the browser.

execute(page, step, obs) returns None when the action worked, or a short
error message when it didn't. It never crashes VisionPilot: a failed
click (for example, blocked by a pop-up) is information, not a disaster.
Always run the guard (safety.check) before calling this.
"""


def execute(page, step, obs):
    try:
        if step.action == "scroll":
            page.mouse.wheel(0, 600)
        elif step.action in ("click", "type", "select"):
            element = obs.handles[step.element_id - 1]
            if step.action == "click":
                element.click(timeout=5000)
            elif step.action == "type":
                element.fill(step.value, timeout=5000)
            else:
                element.select_option(label=step.value, timeout=5000)
        # "done" touches nothing.

        # Let the page settle so the next photo shows the result.
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass  # a page that keeps loading is not an error
        page.wait_for_timeout(300)
        return None
    except Exception as err:
        return f"{type(err).__name__}: {str(err).splitlines()[0]}"
