"""The single Vercel Python entrypoint (declared in pyproject.toml), serving all
/api/* routes internally via Flask. Vercel's Python runtime expects exactly one
entrypoint per project - four separate api/*.py files each exporting their own
`handler` produced an ambiguous-entrypoint build error, so all routes live here
instead, backed by plain modules under server/ (kept outside api/ so they aren't
picked up as additional entrypoint candidates).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, send_file  # noqa: E402

from server.agent_info import AGENT_INFO  # noqa: E402
from server.execute import handle_prompt  # noqa: E402
from server.team_info import TEAM_INFO  # noqa: E402

app = Flask(__name__)

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PNG_PATH = os.path.join(_REPO_ROOT, "assets", "model_architecture.png")
_INDEX_HTML_PATH = os.path.join(_REPO_ROOT, "index.html")


@app.after_request
def _add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/", methods=["GET"])
def gui():
    # Declaring a single Vercel entrypoint puts this project in "backend framework"
    # mode, which disables Vercel's usual automatic static-file serving - so the
    # GUI has to be served explicitly here instead of relying on index.html being
    # picked up on its own.
    return send_file(_INDEX_HTML_PATH, mimetype="text/html")


@app.route("/api/team_info", methods=["GET"])
def team_info():
    return jsonify(TEAM_INFO)


@app.route("/api/agent_info", methods=["GET"])
def agent_info():
    return jsonify(AGENT_INFO)


@app.route("/api/model_architecture", methods=["GET"])
def model_architecture():
    return send_file(_PNG_PATH, mimetype="image/png")


@app.route("/api/execute", methods=["POST", "OPTIONS"])
def execute():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt") if isinstance(payload, dict) else None

    try:
        result = handle_prompt(prompt)
    except Exception as e:
        result = {"status": "error", "error": f"Agent run failed: {e}", "response": None, "steps": []}

    return jsonify(result)
