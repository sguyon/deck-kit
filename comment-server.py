#!/usr/bin/env python3
"""Tiny local server for deck comments: the live deck POSTs {slide,title,target,text,comment} here; appended to comments.md."""
import json, datetime, os
from http.server import BaseHTTPRequestHandler, HTTPServer
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comments.md')
class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or '{}')
        with open(OUT, 'a') as f:
            f.write(f"- [ ] **Slide {d.get('slide')} · {d.get('title','')}** ({datetime.datetime.now():%H:%M})\n"
                    f"  - On: `{d.get('target','')}` — \"{(d.get('text') or '')[:160]}\"\n"
                    f"  - Comment: {d.get('comment','')}\n")
        self.send_response(200); self._cors(); self.end_headers(); self.wfile.write(b'ok')
    def log_message(self, *a): pass
HTTPServer(('127.0.0.1', 8765), H).serve_forever()
