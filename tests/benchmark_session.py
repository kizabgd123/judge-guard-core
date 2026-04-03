import time
import requests
import http.server
import threading

class MockHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
    def log_message(self, format, *args):
        pass

def run_server():
    server = http.server.HTTPServer(('localhost', 8080), MockHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Start server in thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1) # Wait for server

    # Test without session
    start = time.time()
    for _ in range(50):
        requests.post('http://localhost:8080', json={})
    without_session = time.time() - start
    print(f"Without session (50 requests): {without_session:.4f}s")

    # Test with session
    session = requests.Session()
    start = time.time()
    for _ in range(50):
        session.post('http://localhost:8080', json={})
    with_session = time.time() - start
    print(f"With session (50 requests): {with_session:.4f}s")

    improvement = (without_session - with_session) / without_session * 100
    print(f"Improvement: {improvement:.2f}%")
