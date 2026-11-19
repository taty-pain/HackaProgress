import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template

load_dotenv()  # reads .env into environment variables

API_KEY = os.getenv("HACKATIME_API_KEY", "")
API_URL = "https://hackatime.hackclub.com/api/hackatime/v1"

app = Flask(__name__)


def fetch_today():
    """Seconds coded today, according to Hackatime."""
    if not API_KEY:
        raise RuntimeError("Put HACKATIME_API_KEY in the .env file.")
    r = requests.get(
        f"{API_URL}/users/current/statusbar/today",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10,
    )
    r.raise_for_status()  # turns HTTP errors (401, 500...) into Python errors
    return float(r.json()["data"]["grand_total"]["total_seconds"])


@app.get("/api/today")
def today():
    try:
        return jsonify(seconds=fetch_today())
    except Exception as e:
        return jsonify(error=str(e)), 502

STATE_FILE = Path(__file__).parent / "data" / "state.json"


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"goal": 3 * 3600, "baseline": 0.0}   # default: 3 hours


def save_state(state):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


@app.get("/api/progress")
def progress():
    state = load_state()
    try:
        total = fetch_today()
    except Exception as e:
        return jsonify(error=str(e)), 502
    done = max(total - state["baseline"], 0)
    return jsonify(done=done, goal=state["goal"],
                   percent=min(done / state["goal"], 1))


@app.post("/api/goal")
def set_goal():
    try:
        hours = float(request.get_json()["hours"])
        if not 0 < hours <= 100:
            raise ValueError
        total = fetch_today()
    except ValueError:
        return jsonify(error="Enter a goal between 0 and 100 hours."), 400
    except Exception as e:
        return jsonify(error=str(e)), 502
    save_state({"goal": hours * 3600, "baseline": total})
    return jsonify(ok=True)

@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)