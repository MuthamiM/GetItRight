"""
GetItRight — Local Development Server
Serves static files from /web and proxies /api + /ws to the backend on port 5000.
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import os
import sys
import threading

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
BACKEND = "http://127.0.0.1:5000"
PORT = 8090


class DevHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/") or self.path.startswith("/api?") or self.path == "/api" or self.path.startswith("/health"):
            self._proxy()
        else:
            super().do_GET()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def _proxy(self):
        url = BACKEND + self.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        headers = {}
        for key in self.headers:
            if key.lower() not in ("host", "connection"):
                headers[key] = self.headers[key]

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=self.command)
            with urllib.request.urlopen(req, timeout=30) as resp:
                status = resp.status
                resp_headers = resp.getheaders()
                resp_body = resp.read()

            self.send_response(status)
            for h_name, h_val in resp_headers:
                if h_name.lower() not in ("transfer-encoding", "connection", "content-encoding"):
                    self.send_header(h_name, h_val)
            self.end_headers()
            self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"error": "Backend unreachable: {e}"}}'.encode())

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        sys.stderr.write(f"[DEV] {self.address_string()} - {format % args}\n")

    def translate_path(self, path):
        """Serve .html files for paths without extension (SPA-style routing)."""
        result = super().translate_path(path)
        if not os.path.exists(result) and not os.path.splitext(result)[1]:
            # Try appending .html
            html_path = result + ".html"
            if os.path.exists(html_path):
                return html_path
            # Fall back to index.html for SPA
            return os.path.join(WEB_DIR, "index.html")
        return result


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print(f"GetItRight Dev Server starting on http://localhost:{PORT}")
    print(f"Serving static files from: {WEB_DIR}")
    print(f"Proxying /api/* to: {BACKEND}")
    with ThreadedServer(("0.0.0.0", PORT), DevHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dev server.")
