from collections import deque
import html
import json
import os
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# Singapore Standard Time (UTC+8)
SGT_TZ = timezone(timedelta(hours=8))

# Stores the latest event and a capped list of recent history (newest first)
latest_webhook = None
webhook_history = deque(maxlen=100)


def extract_payload(req):
    payload = req.get_json(silent=True)
    if not payload and req.form:
        form_data = req.form.to_dict()
        for key in ("data", "payload"):
            if key in form_data:
                try:
                    parsed = json.loads(form_data[key])
                    payload = parsed if isinstance(parsed, dict) else {key: parsed}
                    break
                except (ValueError, TypeError):
                    pass
        if not payload:
            payload = form_data
    return payload


@app.route("/api/detrack-webhook", methods=["POST"])
def handle_detrack_webhook():
    global latest_webhook
    payload = extract_payload(request)
    if not payload:
        return jsonify({"error": "Invalid or empty payload"}), 400

    job_data = payload.get("data", payload) if isinstance(payload, dict) else {}
    if not isinstance(job_data, dict):
        job_data = {}

    entry = {
        "time_sgt": datetime.now(SGT_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "job_number": str(job_data.get("job_number", "-")),
        "detrack_number": str(job_data.get("detrack_number", "-")),
        "tracking_number": str(job_data.get("tracking_number", "-")),
        "status": str(job_data.get("status", "-")),
    }

    latest_webhook = entry
    webhook_history.appendleft(entry)

    return jsonify({"status": "received", "job_number": entry["job_number"]}), 200


@app.route("/webhooks", methods=["GET"])
def view_latest_webhook():
    if not latest_webhook:
        body = "<p>Waiting for incoming webhook...</p>"
    else:
        body = f"""
        <p><b>Time (SGT, UTC+8):</b> {html.escape(latest_webhook['time_sgt'])}</p>
        <p><b>Job Number:</b> {html.escape(latest_webhook['job_number'])}</p>
        <p><b>Detrack #:</b> {html.escape(latest_webhook['detrack_number'])}</p>
        <p><b>Tracking #:</b> {html.escape(latest_webhook['tracking_number'])}</p>
        <p><b>Status:</b> {html.escape(latest_webhook['status'])}</p>
        """

    return f"""
    <!doctype html>
    <html>
      <head>
        <meta http-equiv="refresh" content="5">
        <title>Latest Detrack Webhook</title>
      </head>
      <body style="font-family: sans-serif; padding: 24px;">
        <h2>Latest Detrack Webhook (Auto-refreshes every 5s)</h2>
        {body}
        <p><a href="/history">View History ({len(webhook_history)})</a></p>
      </body>
    </html>
    """, 200


@app.route("/history", methods=["GET"])
def view_history():
    if not webhook_history:
        list_html = "<p>No webhook history yet.</p>"
    else:
        items = []
        for idx, item in enumerate(webhook_history, start=1):
            items.append(
                f"""
                <li style="margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 6px; list-style: none;">
                  <b>#{idx}</b> &mdash; <b>{html.escape(item['status'])}</b><br>
                  Job: <b>{html.escape(item['job_number'])}</b> |
                  Detrack #: <b>{html.escape(item['detrack_number'])}</b> |
                  Tracking #: <b>{html.escape(item['tracking_number'])}</b><br>
                  <small>Time (SGT, UTC+8): {html.escape(item['time_sgt'])}</small>
                </li>
                """
            )
        list_html = f"<ul style='padding-left: 0; max-width: 650px;'>{''.join(items)}</ul>"

    return f"""
    <!doctype html>
    <html>
      <head>
        <meta http-equiv="refresh" content="5">
        <title>Detrack Webhook History</title>
      </head>
      <body style="font-family: sans-serif; padding: 24px;">
        <h2>Webhook History (Newest First, Auto-refreshes every 5s)</h2>
        <p><a href="/webhooks">&larr; Back to Latest Webhook</a></p>
        {list_html}
      </body>
    </html>
    """, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
