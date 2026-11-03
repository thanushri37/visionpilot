"""VisionPilot's guard: checks every step before the hands move.

check(step, obs) answers one of three things:
  "go"     - safe, do it now
  "ask"    - wait for the human to approve first
  "refuse" - never allowed
The guard doesn't only trust the model's "risky" flag: it also reads the
element's own words and asks first if it finds a danger word.
"""
import re

GO, ASK, REFUSE = "go", "ask", "refuse"

# Words that usually mean "this changes something".
DANGER_WORDS = ("save", "submit", "delete", "remove", "pay", "confirm", "apply")
_DANGER = re.compile(r"\b(" + "|".join(DANGER_WORDS) + r")\b", re.IGNORECASE)

TARGETED = {"click", "type", "select"}


def check(step, obs):
    """Return (decision, reason) for one step."""
    if step.action not in TARGETED:          # scroll and done touch nothing
        return GO, "does not touch any element"

    ids = {e["id"] for e in obs.elements}
    if step.element_id not in ids:
        return REFUSE, f"element {step.element_id} is not on screen"

    element = obs.elements[step.element_id - 1]
    if step.action == "type" and element["type"] == "password":
        return REFUSE, "typing into a password box is never allowed"

    found = _DANGER.search(element["text"])
    if step.risky and found:
        return ASK, f'model marked it risky, and "{element["text"]}" contains "{found.group(1)}"'
    if step.risky:
        return ASK, "the model marked this step as risky"
    if found:
        return ASK, f'"{element["text"]}" contains the danger word "{found.group(1)}"'
    return GO, "no danger found"


def terminal_approve(step, obs, why):
    """Ask the human in the terminal. Returns True only for 'y'."""
    element = obs.elements[step.element_id - 1] if step.element_id else None
    target = f'[{step.element_id}] "{element["text"]}"' if element else ""
    print(f"\n>> APPROVAL NEEDED: {step.action} {target} {step.value or ''}".rstrip())
    print(f"   why it's asking: {why}")
    print(f"   model's reason:  {step.reason}")
    try:
        return input("   Approve? [y/N] ").strip().lower() == "y"
    except EOFError:          # no answer possible: treat it as "no"
        return False
