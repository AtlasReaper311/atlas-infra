import http.server
import socketserver
import json
import os
from datetime import datetime, timezone

PORT = int(os.environ.get("PORT", 8080))


class AtlasHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok", "service": "hello-atlas"})
        elif self.path == "/":
            self._respond(200, {
                "service": "hello-atlas",
                "version": "0.1.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Atlas Systems infrastructure smoke test"
            })
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, code: int, body: dict):
        payload = json.dumps(body, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        print(f"[{datetime.now(timezone.utc).isoformat()}] {format % args}")


with socketserver.TCPServer(("", PORT), AtlasHandler) as httpd:
    print(f"hello-atlas running on port {PORT}")
    httpd.serve_forever()