#!/usr/bin/env python3
"""
Guardian Agent Web UI Server
Serves the dashboard and relays agent execution requests.

Usage:
    python3 web_ui/server.py
    # Open http://localhost:8080
"""

import os
import sys
import json
import time
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = int(os.getenv("PORT", 8080))
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_SCRIPT = os.path.join(os.path.dirname(WEB_DIR), "guardian_agent_demo.py")


class GuardianHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {format % args}")
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/" or path == "/index.html":
            self.serve_file(os.path.join(WEB_DIR, "index.html"), "text/html")
        elif path == "/health":
            self.json_response({"status": "ok", "agent": "GuardianAgent v1.0"})
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        if path == "/execute":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            action = body.get("action", "")
            scope = body.get("scope", "read:data")
            result = self.run_agent(action, scope)
            self.json_response(result)
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def serve_file(self, path, content_type):
        try:
            with open(path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"File not found: {path}")
    
    def json_response(self, data):
        content = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(content))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)
    
    def run_agent(self, action: str, scope: str) -> dict:
        """Run the guardian agent and return structured results."""
        try:
            result = subprocess.run(
                [sys.executable, AGENT_SCRIPT],
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "MOCK_AUTH0": "true", "MOCK_GEMINI_JUDGE": "true"}
            )
            return {
                "action": action,
                "scope": scope,
                "stdout": result.stdout,
                "returncode": result.returncode,
                "approved": result.returncode == 0
            }
        except Exception as e:
            return {"action": action, "error": str(e), "approved": False}


def main():
    server = HTTPServer(("0.0.0.0", PORT), GuardianHandler)
    print(f"\n🛡️  Guardian Agent Web UI")
    print(f"   Running at: http://localhost:{PORT}")
    print(f"   Mode: MOCK Demo (no real Auth0 required)")
    print(f"\n   Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Server stopped.")


if __name__ == "__main__":
    main()
