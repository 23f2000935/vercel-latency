from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os
import numpy as np

app = Flask(__name__)
CORS(app)  # This handles ALL CORS automatically

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')
with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

@app.route('/api', methods=['POST', 'OPTIONS'])
def analytics():
    body = request.get_json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        records = [r for r in RAW_DATA if r["region"] == region]
        if not records:
            result[region] = {"error": "no data found"}
            continue
        latencies = [r["latency_ms"] for r in records]
        uptimes   = [r["uptime_pct"] / 100 for r in records]
        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 4),
            "p95_latency": round(float(np.percentile(latencies, 95)), 4),
            "avg_uptime":  round(float(np.mean(uptimes)), 4),
            "breaches":    int(sum(1 for l in latencies if l > threshold_ms))
        }

    return jsonify(result)