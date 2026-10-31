"""Hello Vision: can VisionPilot see a screenshot?

Run from the project folder:  python -m tests.vision_test
"""
from pathlib import Path

from visionpilot.llm import MODEL, ask

SHOT = Path("runs/hello-1.png")

if not SHOT.exists():
    raise SystemExit("runs/hello-1.png not found. Run tests/hello_browser.py first.")

print(f"Asking {MODEL} about {SHOT} ...\n")
print(ask(
    "Describe this screen in two sentences. "
    "Then list every button and link you can see.",
    images=[SHOT],
))
