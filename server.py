#!/usr/bin/env python3
"""
Simple proxy server for Ollama Image Generator
Serves the HTML interface and forwards API requests to Ollama
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
from pathlib import Path

OLLAMA_API_URL = "http://localhost:11434/api/generate"
PORT = 8080


class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the index.html file"""
        if self.path == "/" or self.path == "/index.html":
            try:
                html_file = Path(__file__).parent / "index.html"
                with open(html_file, "rb") as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "index.html not found")
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        """Proxy POST requests to Ollama API"""
        if self.path == "/generate":
            try:
                # Read the request body
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                print(json.dumps(json.loads(body), indent=4), flush=True)
                
                # Forward the request to Ollama
                req = urllib.request.Request(
                    OLLAMA_API_URL,
                    data=body,
                    headers={"Content-Type": "application/json"}
                )
                
                # Open connection to Ollama
                with urllib.request.urlopen(req) as response:
                    # Send response headers
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Transfer-Encoding", "chunked")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("X-Accel-Buffering", "no")
                    self.end_headers()
                    
                    # Stream the response back to the client with minimal buffering
                    # Use very small buffer (1 byte) for immediate streaming
                    while True:
                        chunk = response.read(1)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                        
            except urllib.error.URLError as e:
                error_msg = json.dumps({
                    "error": f"Failed to connect to Ollama: {str(e)}"
                })
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(error_msg.encode())
                
            except Exception as e:
                error_msg = json.dumps({
                    "error": f"Server error: {str(e)}"
                })
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(error_msg.encode())
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, ProxyHandler)
    
    print(f"🚀 Ollama Image Generator Server")
    print(f"📡 Server running on http://localhost:{PORT}")
    print(f"🔗 Proxying to Ollama at {OLLAMA_API_URL}")
    print(f"Press Ctrl+C to stop\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        httpd.shutdown()


if __name__ == "__main__":
    main()
