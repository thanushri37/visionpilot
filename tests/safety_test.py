"""Guard test: try dangerous steps and prove the guard catches each one.

No browser and no model needed. Run:  python -m tests.safety_test
"""
from visionpilot.observe import Observation
from visionpilot.safety import ASK, GO, REFUSE, check
from visionpilot.schema import Step

# A pretend screen with four elements.
obs = Observation("raw.png", "labeled.png", "http://localhost:5000/settings", elements=[
    {"id": 1, "tag": "a", "type": "", "text": "Dashboard", "value": "", "box": {}},
    {"id": 2, "tag": "input", "type": "password", "text": "Password", "value": "", "box": {}},
    {"id": 3, "tag": "button", "type": "submit", "text": "Save settings", "value": "", "box": {}},
    {"id": 4, "tag": "input", "type": "number", "text": "Alert threshold (%)", "value": "70", "box": {}},
])

CASES = [
    ("Save, but the model forgot risky",  Step(action="click", element_id=3, reason="r", risky=False), ASK),
    ("type into a password box",          Step(action="type", element_id=2, value="hunter2", reason="r"), REFUSE),
    ("element 9 is not on screen",        Step(action="click", element_id=9, reason="r"), REFUSE),
    ("model marks a plain link risky",    Step(action="click", element_id=1, reason="r", risky=True), ASK),
    ("type 80 into the threshold box",    Step(action="type", element_id=4, value="80", reason="r"), GO),
    ("done with an answer",               Step(action="done", value="3 errors", reason="r"), GO),
]

passed = 0
for name, step, expected in CASES:
    decision, why = check(step, obs)
    ok = decision == expected
    passed += ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:34} -> {decision:6}  ({why})")
print(f"\n{passed}/{len(CASES)} passed")
