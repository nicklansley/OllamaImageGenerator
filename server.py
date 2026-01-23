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

OLLAMA_API_URL = "http://localhost:11434/api"
PORT = 8080
IMAGE_GEN_MODEL_LIST = ["x/z-image-turbo:bf16", "x/flux2-klein:latest"]


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
        elif self.path == "/test.html":
            try:
                html_file = Path(__file__).parent / "test.html"
                with open(html_file, "rb") as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "test.html not found")
        elif self.path == "/models":
            req = urllib.request.Request(
                OLLAMA_API_URL + "/tags",
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    # Filter models that have 'image' in their name
                    image_gen_model_list = []
                    for model in data["models"]:
                        if model["name"] in IMAGE_GEN_MODEL_LIST:
                            image_gen_model_list.append(model['name'])
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(image_gen_model_list).encode("utf-8"))
            except urllib.error.HTTPError as e:
                error_body = e.read() if e.fp else b""
                self.send_response(e.code)
                self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                if error_body:
                    self.wfile.write(error_body)
                else:
                    error_msg = json.dumps({
                        "error": f"Ollama error: {e.reason}"
                    })
                    self.wfile.write(error_msg.encode())
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
            self.send_error(404, "File not found")

    def do_POST(self):
        """Proxy POST requests to Ollama API"""
        if self.path == "/generate":
            try:
                # Read the request body
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                try:
                    print(json.dumps(json.loads(body), indent=4), flush=True)
                except json.JSONDecodeError:
                    print(body.decode("utf-8", errors="replace"), flush=True)
                
                # Forward the request to Ollama
                req = urllib.request.Request(
                    OLLAMA_API_URL + "/generate",
                    data=body,
                    headers={"Content-Type": "application/json"}
                )
                
                # Open connection to Ollama
                with urllib.request.urlopen(req) as response:
                    # Send response headers
                    self.send_response(response.status)
                    content_type = response.headers.get("Content-Type", "application/x-ndjson")
                    self.send_header("Content-Type", content_type)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("X-Accel-Buffering", "no")
                    self.end_headers()

                    # Stream line-delimited JSON to preserve progress updates
                    while True:
                        line = response.readline()
                        if not line:
                            break
                        self.wfile.write(line)
                        self.wfile.flush()

            except urllib.error.HTTPError as e:
                error_body = e.read() if e.fp else b""
                self.send_response(e.code)
                self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                if error_body:
                    self.wfile.write(error_body)
                else:
                    error_msg = json.dumps({
                        "error": f"Ollama error: {e.reason}"
                    })
                    self.wfile.write(error_msg.encode())

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
