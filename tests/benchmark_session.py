import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.antigravity_core.notion_client import NotionClient

class MockNotionHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"results": []}')

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"id": "db_id"}')

    def log_message(self, format, *args):
        return

def run_mock_server(port):
    server = HTTPServer(('localhost', port), MockNotionHandler)
    server.serve_forever()

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def benchmark():
    port = 8888
    server_thread = threading.Thread(target=run_mock_server, args=(port,), daemon=True)
    server_thread.start()
    time.sleep(1) # Wait for server to start

    os.environ["NOTION_API_KEY"] = "test_key"
    client = NotionClient()
    client.base_url = f"http://localhost:{port}"

    iterations = 50

    print(f"Running benchmark with {iterations} iterations...")

    # Benchmark session-based calls
    start_time = time.time()
    for _ in range(iterations):
        client.test_connection()
    end_time = time.time()
    session_duration = end_time - start_time
    print(f"Session requests total time: {session_duration:.4f}s")
    print(f"Average time per request: {session_duration/iterations:.4f}s")

    # To show the difference, we compare it against a client that doesn't use a session for its calls
    # We'll monkeypatch the client's session.post to use requests.post directly
    original_post = client.session.post
    client.session.post = requests.post

    start_time = time.time()
    for _ in range(iterations):
        client.test_connection()
    end_time = time.time()
    individual_duration = end_time - start_time
    print(f"Simulated Individual requests total time: {individual_duration:.4f}s")
    print(f"Average time per request: {individual_duration/iterations:.4f}s")

    client.session.post = original_post # Restore

    improvement = (individual_duration - session_duration) / individual_duration * 100
    print(f"Performance Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    benchmark()
