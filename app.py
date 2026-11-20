import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/detrack-webhook', methods=['POST'])
def handle_detrack_webhook():
    payload = request.get_json(silent=True)

    if not payload and request.form:
        form_data = request.form.to_dict()
        # Sometimes a form field holds a JSON string (e.g., 'data' or 'payload')
        for key in ('data', 'payload'):
            if key in form_data:
                try:
                    parsed = json.loads(form_data[key])
                    payload = parsed if isinstance(parsed, dict) else {key: parsed}
                    break
                except (ValueError, TypeError):
                    pass
        if not payload:
            payload = form_data

    if not payload:
        return jsonify({"error": "Invalid or empty payload"}), 400

    job_data = payload.get('data', payload) if isinstance(payload, dict) else {}
    if not isinstance(job_data, dict):
        job_data = {}

    job_number = job_data.get('job_number')
    detrack_number = job_data.get('detrack_number')
    status = job_data.get('status')

    print(f"Webhook received -> Job: {job_number} | Detrack #: {detrack_number} | Status: {status}")
    return jsonify({"status": "received", "job_number": job_number}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
