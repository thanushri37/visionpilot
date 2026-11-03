"""Run VisionPilot on one task from PowerShell.

Start the practice website first (python target_app/app.py), then:
  python cli.py "Change the alert threshold to 80% and save"
  python cli.py "Find and summarise the errors on this dashboard."
  python cli.py "Change the alert threshold to 80% and save" --start http://localhost:5000/settings?popup=1
"""
import argparse

from visionpilot.agent import run
from visionpilot.safety import terminal_approve

parser = argparse.ArgumentParser(description="Run VisionPilot on one task.")
parser.add_argument("task", help="what you want done, in plain English")
parser.add_argument("--start", default="http://localhost:5000/dashboard",
                    help="the page to start on")
parser.add_argument("--headless", action="store_true", help="hide the browser window")
args = parser.parse_args()

run(args.task, args.start, terminal_approve, headless=args.headless)
