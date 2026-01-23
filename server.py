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
from datetime import datetime
import base64
import os

OLLAMA_API_URL = "http://localhost:11434/api"
PORT = 8080
IMAGE_GEN_MODEL_LIST = ["x/z-image-turbo:bf16", "x/flux2-klein:latest"]
HISTORY_DIR = Path(__file__).parent / "history"


def ensure_history_dir():
    """Ensure the history directory exists"""
    HISTORY_DIR.mkdir(exist_ok=True)


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

        elif self.path == "/history/index":
            # Return JSON array of all history items
            try:
                ensure_history_dir()
                history_items = []
                
                # Find all .json files in history directory
                for json_file in sorted(HISTORY_DIR.glob("*.json"), reverse=True):
                    try:
                        with open(json_file, 'r') as f:
                            item_data = json.load(f)
                            history_items.append(item_data)
                    except Exception as e:
                        print(f"Error reading {json_file}: {e}")
                        continue
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(history_items).encode("utf-8"))
            except Exception as e:
                error_msg = json.dumps({
                    "error": f"Failed to load history: {str(e)}"
                })
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(error_msg.encode())

        elif self.path.startswith("/history/"):
            # Extract image name from path (e.g., /history/20260123123453)
            image_name = self.path.split("/history/")[1]
            
            # Remove .png extension if provided
            if image_name.endswith(".png"):
                image_name = image_name[:-4]
            
            try:
                ensure_history_dir()
                image_path = HISTORY_DIR / f"{image_name}.png"
                json_path = HISTORY_DIR / f"{image_name}.json"
                
                if not image_path.exists():
                    self.send_error(404, f"Image not found: {image_name}")
                    return
                
                # Read the image and encode to base64
                with open(image_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                # Read the JSON metadata if it exists
                metadata = {}
                if json_path.exists():
                    with open(json_path, 'r') as f:
                        metadata = json.load(f)
                
                # Return in the same format as local storage
                response_data = {
                    "image": image_data,
                    "settings": metadata.get("settings", {}),
                    "timestamp": metadata.get("timestamp", ""),
                    "id": metadata.get("id", image_name)
                }
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            except Exception as e:
                error_msg = json.dumps({
                    "error": f"Failed to load image: {str(e)}"
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
                
                # Parse the request body to get settings
                request_data = json.loads(body)
                
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
                    # Also capture the final response to save to history
                    final_image_data = None
                    while True:
                        line = response.readline()
                        if not line:
                            break
                        
                        # Try to parse the line to check if it contains the final image
                        try:
                            line_data = json.loads(line)
                            if line_data.get('done') and line_data.get('image'):
                                final_image_data = line_data.get('image')
                        except:
                            pass
                        
                        self.wfile.write(line)
                        self.wfile.flush()
                    
                    # Save to history if we got an image
                    if final_image_data:
                        try:
                            ensure_history_dir()
                            
                            # Generate filename with timestamp
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            image_filename = f"{timestamp}.png"
                            json_filename = f"{timestamp}.json"
                            
                            # Save the image
                            image_path = HISTORY_DIR / image_filename
                            with open(image_path, 'wb') as f:
                                f.write(base64.b64decode(final_image_data))
                            
                            # Prepare metadata matching the local storage format
                            metadata = {
                                "id": timestamp,
                                "timestamp": datetime.now().isoformat(),
                                "image": final_image_data,  # Store base64 for compatibility
                                "settings": {
                                    "model": request_data.get("model", ""),
                                    "prompt": request_data.get("prompt", ""),
                                    "seed": request_data.get("seed", 0),
                                    "width": request_data.get("width", 512),
                                    "height": request_data.get("height", 512),
                                    "steps": request_data.get("steps", 12)
                                }
                            }
                            
                            # Save the metadata
                            json_path = HISTORY_DIR / json_filename
                            with open(json_path, 'w') as f:
                                json.dump(metadata, f, indent=2)
                            
                            print(f"✓ Saved image to history: {image_filename}", flush=True)
                        except Exception as e:
                            print(f"Error saving to history: {e}", flush=True)

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
