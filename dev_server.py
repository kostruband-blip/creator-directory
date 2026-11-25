#!/usr/bin/env python3
"""Local preview that mimics vercel.json rewrites (/ru, /uk -> index.html).

    python dev_server.py          # http://localhost:8000
"""
import http.server
import os
import socketserver

PORT = int(os.environ.get("PORT", "8000"))
REWRITES = {"/ru": "/index.html", "/uk": "/index.html", "/ru/": "/index.html", "/uk/": "/index.html"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path == "/ua":
            self.send_response(308)
            self.send_header("Location", "/uk" + ("?" + query if query else ""))
            self.end_headers()
            return
        if path in REWRITES:
            self.path = REWRITES[path] + ("?" + query if query else "")
        return super().do_GET()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Serving on http://0.0.0.0:{PORT}")
        httpd.serve_forever()
