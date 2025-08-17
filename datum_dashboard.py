from flask import Flask, render_template_string, jsonify
import json
import os

app = Flask(__name__)

STATUS_FILE = "/tmp/datum_gateway_status.json"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Datum Gateway Status Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; background: #f5f5f5; }
        h1 { color: #333; }
        .status-box {
            background: white; padding: 1rem 2rem; border-radius: 8px; max-width: 400px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .ok { color: green; font-weight: bold; }
        .warn { color: orange; font-weight: bold; }
        .fail { color: red; font-weight: bold; }
        .label { font-weight: bold; }
        .footer { margin-top: 2rem; font-size: 0.9rem; color: #777; }
    </style>
</head>
<body>
    <h1>Datum Gateway Status Dashboard</h1>
    <div class="status-box">
        {% if status_data %}
            <p>Status: 
                {% if status_data.status == "OK" %}
                    <span class="ok">{{ status_data.status }}</span>
                {% elif status_data.status == "WARNING" %}
                    <span class="warn">{{ status_data.status }}</span>
                {% else %}
                    <span class="fail">{{ status_data.status }}</span>
                {% endif %}
            </p>
            <p><span class="label">Heartbeat Age:</span> {{ status_data.heartbeat_age_minutes | round(1) }} minutes ago</p>
            <p><span class="label">Clients Connected:</span> {{ status_data.clients }}</p>
            <p><span class="label">Last Checked:</span> {{ status_data.timestamp }}</p>
        {% else %}
            <p><span class="fail">No status data available.</span></p>
        {% endif %}
    </div>
    <div class="footer">
        Refreshes every time you reload this page.
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f:
                status_data = json.load(f)
        except Exception:
            status_data = None
    else:
        status_data = None
    return render_template_string(HTML_TEMPLATE, status_data=status_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

