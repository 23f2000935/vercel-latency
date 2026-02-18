import json
import os
import numpy as np
from http.server import BaseHTTPRequestHandler

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')

try:
    with open(DATA_PATH) as f:
        RAW_DATA = json.load(f)
except Exception as e:
    RAW_DATA = []
    LOAD_ERROR = str(e)
else:
    LOAD_ERROR = None

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            if LOAD_ERROR:
                raise Exception(f"Failed to load data file: {LOAD_ERROR}")

            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            regions = body.get("regions", [])
            threshold_ms = body.get("threshold_ms", 180)

            result = {}
            for region in regions:
                records = [r for r in RAW_DATA if r["region"] == region]
                if not records:
                    result[region] = {"error": "no data found for region"}
                    continue

                latencies = [r["latency_ms"] for r in records]
                uptimes   = [r["uptime_pct"] / 100 for r in records]

                result[region] = {
                    "avg_latency": round(float(np.mean(latencies)), 4),
                    "p95_latency": round(float(np.percentile(latencies, 95)), 4),
                    "avg_uptime":  round(float(np.mean(uptimes)), 4),
                    "breaches":    int(sum(1 for l in latencies if l > threshold_ms))
                }

            self._respond(200, result)

        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, code, data):
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')