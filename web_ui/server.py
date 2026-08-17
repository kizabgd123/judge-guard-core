#!/usr/bin/env python3
"""
Agent Nexus 2 — Live Web Dashboard Server.

Serves the dashboard UI and provides real-time API endpoints
backed by the actual NexusOrchestrator module.

Endpoints:
    GET  /            — Serve index.html
    GET  /api/health  — Proxy to MonitorAgent health endpoint (:7861)
    GET  /api/status  — Return NexusOrchestrator.status()
    POST /api/verify  — Run GuardianAgent verification on an action

Usage:
    python3 web_ui/server.py
    # Open http://localhost:8080
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Path setup — import the real Agent Nexus 2 module
# ---------------------------------------------------------------------------
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(WORKSPACE, ".env"))

from src.antigravity_core.agent_nexus2 import NexusOrchestrator  # noqa: E402

# ---------------------------------------------------------------------------
# Structured JSON logger
# ---------------------------------------------------------------------------
logger = logging.getLogger("Nexus2WebServer")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(json.dumps({
    "time": "%(asctime)s",
    "level": "%(levelname)s",
    "agent": "WebServer",
    "msg": "%(message)s",
})))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PORT = int(os.getenv("WEB_PORT", "8088"))
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
MONITOR_URL = "http://localhost:{}/health".format(
    os.getenv("NEXUS_MONITOR_PORT", "7861")
)

# ---------------------------------------------------------------------------
# Singleton Nexus instance
# ---------------------------------------------------------------------------
nexus = NexusOrchestrator()
if not nexus._started:
    nexus.start()


class Nexus2Handler(BaseHTTPRequestHandler):
    """HTTP handler for Agent Nexus 2 dashboard."""

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.info(fmt % args)

    # --- Routing -----------------------------------------------------------

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        routes: dict[str, Any] = {
            "/": self._serve_index,
            "/index.html": self._serve_index,
            "/manifest.json": self._serve_manifest,
            "/sw.js": self._serve_sw,
            "/api/health": self._api_health,
            "/api/status": self._api_status,
        }
        handler_fn = routes.get(path)
        if handler_fn:
            handler_fn()
        else:
            self.send_error(404)

    def _serve_manifest(self) -> None:
        self._serve_static_file("manifest.json", "application/json")

    def _serve_sw(self) -> None:
        self._serve_static_file("sw.js", "application/javascript")

    def _serve_static_file(self, filename: str, content_type: str) -> None:
        filepath = os.path.join(WEB_DIR, filename)
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self._respond(200, content, content_type)
        except FileNotFoundError:
            self.send_error(404, f"{filename} not found")


    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/verify":
            self._api_verify()
        elif path == "/api/reset_halt":
            self._api_reset_halt()
        else:
            self.send_error(404)

    def _api_reset_halt(self) -> None:
        nexus.reset_safety_halt()
        self._json_response({"status": "RESET", "message": "Safety Halt cleared by operator."})


    def do_OPTIONS(self) -> None:
        self._cors_preflight()

    # --- Handlers ----------------------------------------------------------

    def _serve_index(self) -> None:
        filepath = os.path.join(WEB_DIR, "index.html")
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self._respond(200, content, "text/html; charset=utf-8")
        except FileNotFoundError:
            self.send_error(404, "index.html not found")

    def _api_health(self) -> None:
        """Proxy to MonitorAgent health endpoint."""
        try:
            req = urllib.request.Request(MONITOR_URL, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            self._json_response(data)
        except urllib.error.URLError as exc:
            self._json_response({
                "status": "unreachable",
                "error": str(exc),
                "monitor_url": MONITOR_URL,
            }, status=503)
        except TimeoutError:
            self._json_response({
                "status": "timeout",
                "monitor_url": MONITOR_URL,
            }, status=504)

    def _api_status(self) -> None:
        """Return full NexusOrchestrator status."""
        try:
            status = nexus.status()
            self._json_response(status)
        except RuntimeError as exc:
            self._json_response({"error": str(exc)}, status=500)

    def _api_verify(self) -> None:
        """Verify an action through the GuardianAgent pipeline."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            action = body.get("action", "")
            if not action:
                self._json_response({"error": "Missing 'action' field"}, status=400)
                return
            result = nexus.verify_action(action)
            result["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            self._json_response(result)
        except json.JSONDecodeError:
            self._json_response({"error": "Invalid JSON body"}, status=400)
        except ValueError as exc:
            self._json_response({"error": str(exc)}, status=400)

    # --- Response helpers --------------------------------------------------

    def _respond(self, status: int, content: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def _json_response(self, data: dict, status: int = 200) -> None:
        content = json.dumps(data).encode()
        self._respond(status, content, "application/json")

    def _cors_preflight(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def main() -> None:
    server = ReusableHTTPServer(("0.0.0.0", PORT), Nexus2Handler)
    server.timeout = 30
    logger.info(f"Agent Nexus 2 Dashboard running at http://localhost:{PORT}")
    logger.info(f"MonitorAgent health proxy: {MONITOR_URL}")
    print(f"\n🛡️  Agent Nexus 2 — Live Dashboard")
    print(f"   http://localhost:{PORT}")
    print(f"   Health proxy → {MONITOR_URL}")
    print(f"\n   Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    main()

