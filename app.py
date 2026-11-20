import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/detrack-webhook', methods=['POST'])
def handle_detrack_webhook():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid or empty JSON payload"}), 400

    job_data = payload.get('data', payload)
    job_number = job_data.get('job_number')
    detrack_number = job_data.get('detrack_number')
    status = job_data.get('status')

    print(f"Webhook received -> Job: {job_number} | Detrack #: {detrack_number} | Status: {status}")

    # Add downstream logic here (save to database, forward to another service, etc.)
    return jsonify({"status": "received", "job_number": job_number}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)