import csv
import json
import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response, send_file

app = Flask(__name__)

CSV_FILE = os.environ.get("WEBHOOK_CSV_FILE", "webhook_logs.csv")
CSV_COLUMNS = [
    "received_at_utc",
    "job_number",
    "detrack_number",
    "tracking_number",
    "status",
    "raw_payload_json",
]


def ensure_csv_exists():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()


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


def save_webhook_record(payload):
    ensure_csv_exists()
    job_data = payload.get("data", payload) if isinstance(payload, dict) else {}
    if not isinstance(job_data, dict):
        job_data = {}

    row = {
        "received_at_utc": datetime.now(timezone.utc).isoformat(),
        "job_number": job_data.get("job_number", ""),
        "detrack_number": job_data.get("detrack_number", ""),
        "tracking_number": job_data.get("tracking_number", ""),
        "status": job_data.get("status", ""),
        "raw_payload_json": json.dumps(payload, ensure_ascii=False),
    }

    with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(row)

    return row


@app.route("/api/detrack-webhook", methods=["POST"])
def handle_detrack_webhook():
    payload = extract_payload(request)
    if not payload:
        return jsonify({"error": "Invalid or empty payload"}), 400

    row = save_webhook_record(payload)
    print(
        f"Saved webhook -> Job: {row['job_number']} | "
        f"Detrack #: {row['detrack_number']} | Status: {row['status']}"
    )
    return jsonify({"status": "received", "job_number": row["job_number"]}), 200


@app.route("/webhooks", methods=["GET"])
def view_webhooks():
    ensure_csv_exists()
    with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Show newest entries first
    rows.reverse()
    return jsonify({"count": len(rows), "records": rows}), 200


@app.route("/webhooks/export.csv", methods=["GET"])
def export_webhooks_csv():
    ensure_csv_exists()
    return send_file(
        CSV_FILE,
        mimetype="text/csv",
        as_attachment=True,
        download_name="detrack_webhook_logs.csv",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
