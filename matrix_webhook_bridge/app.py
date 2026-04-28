import os
import uuid
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

MATRIX_BASE_URL = os.environ["MATRIX_BASE_URL"].rstrip("/")
MATRIX_ROOM_ID = os.environ["MATRIX_ROOM_ID"]
MATRIX_ACCESS_TOKEN = os.environ["MATRIX_ACCESS_TOKEN"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]


def build_message(payload: dict) -> str:
    status = payload.get("status", "unknown").upper()
    alerts = payload.get("alerts", [])

    lines = [f"[Grafana] {status}"]

    for alert in alerts:
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        name = labels.get("alertname", "unnamed-alert")
        summary = annotations.get("summary", "")
        description = annotations.get("description", "")

        lines.append(f"- {name}")
        if summary:
            lines.append(f"  summary: {summary}")
        if description:
            lines.append(f"  description: {description}")

    if not alerts:
        title = payload.get("title")
        message = payload.get("message")
        if title:
            lines.append(f"title: {title}")
        if message:
            lines.append(f"message: {message}")

    return "\n".join(lines)


def send_matrix_message(text: str) -> requests.Response:
    txn_id = str(uuid.uuid4())
    url = (
        f"{MATRIX_BASE_URL}/_matrix/client/v3/rooms/"
        f"{MATRIX_ROOM_ID}/send/m.room.message/{txn_id}"
    )
    headers = {
        "Authorization": f"Bearer {MATRIX_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "msgtype": "m.text",
        "body": text,
    }
    return requests.put(url, headers=headers, json=body, timeout=15)


@app.post("/grafana-webhook")
def grafana_webhook():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {WEBHOOK_SECRET}":
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    text = build_message(payload)

    resp = send_matrix_message(text)
    if resp.ok:
        return jsonify({"ok": True}), 200

    return jsonify({
        "ok": False,
        "status_code": resp.status_code,
        "response": resp.text,
    }), 502


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
