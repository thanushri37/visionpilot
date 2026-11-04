# VisionPilot

VisionPilot is an AI agent that uses a web browser the way a person does. You type a task in plain English. It looks at the screen, decides what to click, asks you before anything risky, does it, and then looks at the screen again to check it really worked.

Built for the **Meta Global AI Developer Hackathon** (Indie track) with **Muse Spark** through the Meta Model API, and **Muse Code**.

🎬 **Demo video:** _add link here_

---

## Why I built this

I started this hackathon as a beginner. In one week I had to learn PowerShell, git, Python environments, API keys and Meta's tools all at once. I asked chatbots for help a lot, and they gave me good instructions. But they couldn't see my screen. I typed commands into the wrong window, put my API key in the wrong file, and ran tests while my website wasn't even running. Every time, I had to copy the error back and explain what I was looking at.

That's the gap I wanted to close. A helper that only tells you what to do leaves the hard part to you. VisionPilot looks at the screen itself, does the steps, and checks its own work. And when something unexpected shows up, it notices instead of pretending everything went fine.

---

## What it can do

VisionPilot works on a small practice admin website that I built (it runs on my own laptop), so the demo never breaks because someone else's site changed.

| Task | What I type | What VisionPilot does |
| --- | --- | --- |
| **A. Read** | "Find and summarise the errors on this dashboard." | Reads the dashboard and lists the 3 errors (database timeout, payment API 500, disk at 95%) |
| **B. Act** | "Change the alert threshold to 80% and save." | Goes to Settings, types 80, **asks me before clicking Save**, saves, and checks for the green "Saved" message |
| **C. Adapt** | Same as B, but a surprise pop-up appears | Notices the pop-up blocking the page, clicks Dismiss, then finishes the task |

---

## How it works

Every task is the same loop, repeated until the task is done:

```
   ┌─► 📸 look ─► 🧠 decide ─► 🛡 guard ─► ✋ act ─► ✅ check ─┐
   │                                                          │
   └────────────── fresh photo every time ◄───────────────────┘
```

| Part | File | What it does |
| --- | --- | --- |
| 📸 Eyes | `visionpilot/observe.py` | Takes a screenshot and draws a **numbered red box** on every button, link and text box |
| 🧠 Brain | `visionpilot/planner.py` | Sends the task, the numbered screenshot and the list of elements to Muse Spark, and gets back **one** next step, like `type 80 into number 3` |
| 📋 Template | `visionpilot/schema.py` | Every answer must be: action + element number + value. Anything else is rejected |
| 🛡 Guard | `visionpilot/safety.py` | Decides: go, ask the human first, or refuse |
| ✋ Hands | `visionpilot/executor.py` | Does the step in the browser with Playwright |
| ✅ Checker | `visionpilot/verifier.py` | Shows Muse Spark the screen **before and after** the step and asks: did it really work? |
| 🔁 Loop | `visionpilot/agent.py` | Connects everything, keeps a history of what worked and what failed, and decides when to stop |

### The numbered-box trick

AI models are good at understanding *what* is on a screen, but not good at guessing exact pixel positions. So VisionPilot never asks for coordinates. Playwright already knows exactly where every button is, so it numbers them all. The model just answers "click 5", and the code clicks element 5. Each side does the part it's good at.

### How it adapts

Every result goes into a history the model sees on the next turn:

```
OK:     type [3] "Alert threshold (%)" '80'
FAILED: click [5] "Save settings" -> blocked (TimeoutError)
```

So when a click fails, or the checker sees something unexpected, the next decision takes that into account, for example "close the pop-up first".

### When it stops

- ✅ The model says **done** and one more look confirms the task is complete
- ❌ **3 failures in a row**: it stops and says it needs help, instead of guessing forever
- ❌ **15 steps** used
- ⏹ I say **no** at an approval

---

## Safety

I wanted it to be impossible for VisionPilot to save or delete something without me saying yes.

- **Only 5 actions exist:** click, type, select, scroll, done. Anything else the model invents is rejected.
- **Two checks before risky steps:** the model marks a step as risky, **and** the guard reads the button's own words. If it finds a word like *save, submit, delete, remove, pay, confirm* or *apply*, it asks me first, even if the model forgot to flag it.
- **Never types into password boxes.**
- **Only works on my practice site.** There is no "go to any website" action.
- **The API key lives only in `.env`,** which git never uploads.

`tests/safety_test.py` tries 6 risky steps against the guard. All 6 are caught.

---

## What happened when I tested it with the real model

**Task B (Nov 3):** VisionPilot went to Settings, typed 80, asked me before Save, and saved. The checker's own words after the save:

> "After clicking Save settings, the Alert settings page shows green confirmation 'Saved: alert threshold is 80%'…"

**Task C (Nov 4):** after typing 80 the pop-up appeared, and the checker noticed it straight away:

> "Alert threshold input changed from 70 to 80 as intended, but an unexpected modal popup appeared stating 'Your session will expire in 5 minutes'…"

On the next step VisionPilot chose **Dismiss**. In that run the checker also caught something I didn't expect: the settings got saved during the Dismiss step (most likely a stray Enter key reached the browser), and it reported that honestly instead of calling the step a clean success. That's exactly why every step is checked with a second screenshot.

Every run is saved in `runs/<date-time>/` with every screenshot and a `log.json` of each decision, so any run can be replayed.

---

## Meta models used

- **Muse Spark 1.3** (`muse-spark-1.3`) through the **Meta Model API** (`https://api.meta.ai/v1`, OpenAI-compatible). It does three jobs:
  1. **Decide** the next step from the numbered screenshot
  2. **Check** each step by comparing before and after screenshots
  3. **Confirm** the task is really finished before VisionPilot says "done"
- **Muse Code** — I used it on my laptop to create the project files from prompts I reviewed, and to explain each file to me in simple English.

I'm a beginner, so I also used AI assistants (Muse Code and Claude) to help me design, write and understand the code. I made the design decisions step by step and tested every part on my own laptop.

---

## Run it yourself

You need Python 3.11 or newer and a Meta Model API key.

**1. Get the code and install the tools**

```powershell
git clone https://github.com/<your-username>/visionpilot.git
cd visionpilot
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**2. Add your key**

Copy `.env.example` to `.env` and paste your key after `MODEL_API_KEY=`:

```
MODEL_API_KEY=your-key-here
MODEL_API_BASE_URL=https://api.meta.ai/v1
MODEL_API_MODEL=muse-spark-1.3
```

**3. Start the practice website** (leave this window open)

```powershell
python target_app/app.py
```

It runs at http://localhost:5000.

**4. In a second window, give VisionPilot a task**

```powershell
.venv\Scripts\activate
python cli.py "Find and summarise the errors on this dashboard."
python cli.py "Change the alert threshold to 80% and save"
python cli.py "Change the alert threshold to 80% and save" --start "http://localhost:5000/settings?popup=1"
```

When it asks `Approve? [y/N]`, type `y` in the terminal. Don't click inside the browser while it's working.

To start again from 70: `Invoke-RestMethod -Method Post http://localhost:5000/reset` (or restart the website).

### Tests

| Command | What it checks | Needs |
| --- | --- | --- |
| `python -m tests.safety_test` | The guard catches 6 risky steps | Nothing |
| `python -m tests.vision_test` | Muse Spark can describe a screenshot | API key |
| `python -m tests.observe_test` | Numbered boxes on every page | Website running |
| `python -m tests.plan_test` | The model's first decisions for Tasks A and B | Website + API key |
| `python -m tests.executor_test` | The hands and guard on Tasks B and C, no model | Website |

---

## Project layout

```
visionpilot/
  llm.py         the one doorway to the Meta model
  observe.py     eyes: numbered screenshot + element list
  schema.py      the answer template
  planner.py     brain: the next step
  safety.py      guard: go / ask / refuse
  executor.py    hands: click, type, select, scroll
  verifier.py    checker: before/after, and the final check
  agent.py       the loop
target_app/app.py  the practice website (Tasks A, B, C)
cli.py             run a task from the terminal
tests/             the tests above
```

---

## Limitations and what's next

- It only works on my practice website. That's on purpose for safety, but it means it hasn't been tried on real apps yet.
- Each step takes a few seconds, mostly waiting for the model.
- The model's answers can vary between runs. I tested each task with the real model, but I haven't done a proper "run it 5 times and count" evaluation yet.
- Approvals happen in the terminal for now.

Next I'd like to add a simple screen where you watch the numbered screenshots live and press an Approve button, use **SAM 3.1** to highlight the exact part of the screen VisionPilot is working on, and try it on real apps that need a login.

---

## License

MIT. See [LICENSE](LICENSE).
