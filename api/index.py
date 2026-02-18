import json
import os
import numpy as np
from http.server import BaseHTTPRequestHandler

# Load the data once when the function starts
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')
with open(DATA_PATH) as f:
    RAW_DATA = json.load(f)

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        # Read the request body
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))

        regions = body.get("regions", [])
        threshold_ms = body.get("threshold_ms", 180)

        result = {}
        for region in regions:
            # Filter records for this region
            records = [r for r in RAW_DATA if r["region"] == region]

            if not records:
                result[region] = None
                continue

            latencies = [r["latency_ms"] for r in records]
            uptimes   = [r["uptime"]     for r in records]

            result[region] = {
                "avg_latency": round(float(np.mean(latencies)), 4),
                "p95_latency": round(float(np.percentile(latencies, 95)), 4),
                "avg_uptime":  round(float(np.mean(uptimes)), 4),
                "breaches":    int(sum(1 for l in latencies if l > threshold_ms))
            }

        # Send the response
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
