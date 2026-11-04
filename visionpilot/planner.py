"""VisionPilot's decisions: ask the model for the next single step.

next_step(task, obs, history) sends the model the task, the numbered
screenshot and the element list, then checks the answer against the
schema. If the answer is broken, it tells the model what was wrong and
asks once more.
"""
from pydantic import ValidationError

from .llm import ask
from .schema import Step

SYSTEM = """You are VisionPilot, a careful agent that operates a web browser.
You see a screenshot where every element you can use has a red numbered box,
plus a text list of those elements. Decide the ONE next step toward the task.

Reply with ONLY a JSON object, no other text:
{"action": "...", "element_id": <number or null>, "value": <text or null>,
 "reason": "<one short sentence>", "risky": <true or false>}

Actions:
- "click":  click element_id. value is null.
- "type":   type value into element_id (replaces what is there).
- "select": choose the option named value in dropdown element_id.
- "scroll": scroll down to see more. element_id and value are null.
- "done":   the task is finished. element_id is null. value is your answer or
            a short summary of what was achieved.

Rules:
- Only use element_id numbers that are in the list.
- Set risky to true for any step that saves, submits, deletes or pays.
- If a pop-up or dialog is visible, close it (for example, click its Dismiss
  or Close button) BEFORE anything else, even if the task looks almost done.
- Only say "done" when the screen shows the task is complete.

Example. Task: "Set notify to Slack". List has [4] select "Notify by".
{"action": "select", "element_id": 4, "value": "Slack",
 "reason": "Choose Slack in the Notify by dropdown", "risky": false}"""

NEEDS_ELEMENT = {"click", "type", "select"}
NEEDS_VALUE = {"type", "select", "done"}


def _extract_json(text):
    """Cut the JSON object out of the reply, even if the model added words."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("the reply contains no JSON object")
    return text[start:end + 1]


def _check(step, obs):
    """Rules the schema alone can't check."""
    ids = {e["id"] for e in obs.elements}
    if step.action in NEEDS_ELEMENT and step.element_id not in ids:
        raise ValueError(f"element_id {step.element_id} is not in the list")
    if step.action in NEEDS_VALUE and not (step.value or "").strip():
        raise ValueError(f'action "{step.action}" needs a value')


def next_step(task, obs, history=()):
    """Return (Step, raw reply text) for the single next action."""
    prompt = (
        f"Task: {task}\n"
        f"Current page: {obs.url}\n"
        f"Steps so far:\n{chr(10).join(history) or '(none yet)'}\n\n"
        f"Elements on screen:\n{obs.element_lines()}"
    )
    reply = ask(prompt, images=[obs.labeled_path], system=SYSTEM)
    for attempt in range(2):
        try:
            step = Step.model_validate_json(_extract_json(reply))
            _check(step, obs)
            return step, reply
        except (ValidationError, ValueError) as err:
            if attempt == 1:
                raise ValueError(f"model gave an invalid step twice: {err}") from err
            if isinstance(err, ValidationError):
                first = err.errors()[0]
                field = ".".join(str(part) for part in first["loc"]) or "reply"
                reason = f"{field}: {first['msg']}"
            else:
                reason = str(err)
            reply = ask(
                prompt + f"\n\nYour last reply was invalid ({reason}). "
                "Reply with ONLY the corrected JSON object.",
                images=[obs.labeled_path],
                system=SYSTEM,
            )
