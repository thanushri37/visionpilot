"""VisionPilot's practice website: a small admin dashboard we control.

Run it from the project folder:  python target_app/app.py
Then open http://localhost:5000 in a browser.

Pages:
  /dashboard            Task A - 5 service cards, 3 of them errors
  /settings             Task B - alert threshold, notify-by, Save
  /settings?popup=1     Task C - a pop-up appears the first time
                        something is typed in the threshold box
  /state                the saved settings as data (for checking results)
  /reset  (POST)        puts the settings back to the starting values
"""
from flask import Flask, jsonify, redirect, render_template_string, request

app = Flask(__name__)

START = {"threshold": 70, "notify": "Email"}
STATE = dict(START)  # kept in memory: restarting the app resets it

PAGE = """<!doctype html>
<html><head><title>Acme Ops</title><style>
body{font-family:sans-serif;margin:0}
nav{background:#223;padding:14px}
nav a{color:#fff;margin-right:18px}
main{padding:24px;max-width:760px}
.card{border:1px solid #ccc;border-radius:8px;padding:12px;margin:10px 0}
.err{border-left:6px solid #c33;background:#fff4f4}
.ok{color:#080;font-weight:bold}
#popup{position:fixed;inset:0;background:rgba(0,0,0,.5);display:none;
       align-items:center;justify-content:center}
#popup div{background:#fff;padding:24px;border-radius:8px}
</style></head><body>
<nav><a href="/dashboard">Dashboard</a><a href="/settings">Settings</a></nav>
<main>{{ body|safe }}</main>
{% if popup %}
<div id="popup"><div>
  <p>Your session will expire in 5 minutes.</p>
  <button onclick="document.getElementById('popup').remove()">Dismiss</button>
</div></div>
<script>
  // Task C: show the pop-up the first time something is typed in the
  // threshold box, so it always arrives after the agent has started acting.
  document.getElementById('threshold').addEventListener('input', function () {
    var p = document.getElementById('popup');
    if (p) { p.style.display = 'flex'; }
  }, { once: true });
</script>
{% endif %}
</body></html>"""


@app.route("/")
def home():
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    body = """<h1>Service health</h1>
    <div class="card">API gateway: healthy</div>
    <div class="card err">ERROR: Database timeout on orders-db (3 times in the last hour)</div>
    <div class="card">Search: healthy</div>
    <div class="card err">ERROR: Payment API returned 500 for 12 requests</div>
    <div class="card err">ERROR: Disk usage at 95% on worker-2</div>"""
    return render_template_string(PAGE, body=body, popup=False)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        try:
            STATE["threshold"] = int(request.form["threshold"])
        except (KeyError, ValueError):
            return redirect("/settings?error=1")
        STATE["notify"] = request.form.get("notify", STATE["notify"])
        return redirect("/settings?saved=1")

    message = ""
    if request.args.get("saved"):
        message = f'<p class="ok">Saved: alert threshold is {STATE["threshold"]}%</p>'
    elif request.args.get("error"):
        message = '<p style="color:#c33">Please enter a whole number.</p>'

    options = "".join(
        f'<option{" selected" if o == STATE["notify"] else ""}>{o}</option>'
        for o in ["Email", "Slack", "SMS"]
    )
    body = f"""<h1>Alert settings</h1>{message}
    <form method="post">
      <p><label for="threshold">Alert threshold (%)</label>
         <input id="threshold" name="threshold" type="number"
                aria-label="Alert threshold (%)" value="{STATE['threshold']}"></p>
      <p><label for="notify">Notify by</label>
         <select id="notify" name="notify" aria-label="Notify by">{options}</select></p>
      <button type="submit">Save settings</button>
    </form>"""
    return render_template_string(PAGE, body=body, popup=bool(request.args.get("popup")))


@app.route("/state")
def state():
    return jsonify(STATE)


@app.route("/reset", methods=["POST"])
def reset():
    STATE.clear()
    STATE.update(START)
    return jsonify(STATE)


if __name__ == "__main__":
    app.run(port=5000, debug=False)
