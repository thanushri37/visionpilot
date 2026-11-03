"""VisionPilot's checker: did that step really work?

verify(step, before, after) shows the model the screen before and after
one step and asks whether the step did what it was meant to.
final_check(task, answer, screen) asks whether the whole task is done.
If the model's reply can't be read, the check counts as a failure:
VisionPilot never assumes success.
"""
from pydantic import BaseModel, ValidationError

from .llm import ask
from .planner import _extract_json


class Verdict(BaseModel):
    success: bool
    reason: str


class FinalCheck(BaseModel):
    complete: bool
    reason: str


def verify(step, before_path, after_path):
    target = f" on element [{step.element_id}]" if step.element_id else ""
    value = f' with value "{step.value}"' if step.value else ""
    prompt = (
        f"A browser agent just did: {step.action}{target}{value}.\n"
        f"Its goal for this step: {step.reason}\n"
        "Image 1 is the screen BEFORE the step. Image 2 is the screen AFTER.\n"
        "Did the step achieve its goal? Look for changed values, messages, new "
        "pages, pop-ups and errors. Mention anything unexpected that appeared.\n"
        'Reply with ONLY JSON: {"success": true or false, "reason": "<what you see>"}'
    )
    reply = ask(prompt, images=[before_path, after_path])
    try:
        return Verdict.model_validate_json(_extract_json(reply))
    except (ValidationError, ValueError):
        return Verdict(success=False, reason=f"could not read the check: {reply[:120]}")


def final_check(task, answer, screen_path):
    prompt = (
        f"Task: {task}\n"
        f"The agent says it is finished, with this answer: {answer}\n"
        "Look at the screen. Is the task really complete, and is the answer "
        "correct for what you see?\n"
        'Reply with ONLY JSON: {"complete": true or false, "reason": "<what you see>"}'
    )
    reply = ask(prompt, images=[screen_path])
    try:
        return FinalCheck.model_validate_json(_extract_json(reply))
    except (ValidationError, ValueError):
        return FinalCheck(complete=False, reason=f"could not read the check: {reply[:120]}")
