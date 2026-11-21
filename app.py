import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

API_URL = os.getenv("HACKATIME_API_URL", "https://hackatime.hackclub.com/api/hackatime/v1")

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/today")
def today():
    key = request.headers.get("X-Hackatime-Key", "").strip()
    if not key:
        return jsonify(error="Enter your Hackatime API key."), 401
    try:
        r = requests.get(
            f"{API_URL}/users/current/statusbar/today",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
    except requests.RequestException:
        return jsonify(error="Could not reach Hackatime. Try again soon."), 502
    if r.status_code in (401, 403):
        return jsonify(error="Hackatime rejected that key."), 401
    if not r.ok:
        return jsonify(error="Hackatime had a problem. Try again soon."), 502
    try:
        seconds = float(r.json()["data"]["grand_total"]["total_seconds"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Unexpected reply from Hackatime."), 502
    return jsonify(seconds=seconds)


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=False,
    )