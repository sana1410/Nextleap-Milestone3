import json
import os
import subprocess
import threading

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SEED_DIR = os.path.join(BASE_DIR, "data_seed")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.isdir(SEED_DIR):
        for fname in os.listdir(SEED_DIR):
            dest = os.path.join(DATA_DIR, fname)
            if not os.path.exists(dest):
                src = os.path.join(SEED_DIR, fname)
                with open(src, "r", encoding="utf-8") as f_in:
                    with open(dest, "w", encoding="utf-8") as f_out:
                        f_out.write(f_in.read())


ensure_data_dir()


@app.route("/")
def health():
    return jsonify({"status": "ok", "service": "weekly-app-review-pulse"})


@app.route("/api/data")
def get_data():
    themes_path = os.path.join(DATA_DIR, "themes.json")
    if not os.path.exists(themes_path):
        return jsonify({"error": "No data yet. Run the pipeline first."}), 404
    with open(themes_path, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.route("/api/pulse")
def get_pulse():
    pulse_path = os.path.join(DATA_DIR, "pulse.md")
    if not os.path.exists(pulse_path):
        return jsonify({"error": "No pulse yet. Run the pipeline first."}), 404
    with open(pulse_path, "r", encoding="utf-8") as f:
        return jsonify({"pulse": f.read()})


@app.route("/api/run", methods=["POST"])
def run_pipeline_endpoint():
    def _run():
        subprocess.run(
            ["python", "src/main.py", "--dry-run"],
            cwd=BASE_DIR,
        )

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify({"status": "pipeline started"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
