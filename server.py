#!/usr/bin/env python3
"""
Simple proxy server for Ollama Image Generator
Serves the HTML interface and forwards API requests to Ollama
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import base64
import os
import re

OLLAMA_API_URL = "http://localhost:11434/api"
OLLAMA_LOG_LOCATION = "~/.ollama/logs/app.log" # Location of Ollama Log on MacOS - change for Windows and Linux if different!
PORT = 8080
IMAGE_GEN_MODEL_LIST = [
    "x/z-image-turbo:bf16",
    "x/z-image-turbo:fp8",
    "x/z-image-turbo:latest",
    "x/flux2-klein:4b",
    "x/flux2-klein:9b",
    "x/flux2-klein:latest"
]
HISTORY_DIR = Path(__file__).parent / "history"
HISTORY_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]+")
LOG_MESSAGE_PATTERN = r'msg="([^"]*)"'


def get_latest_log_message(level):
    """Return the latest log message for a given level, or None if not found."""
    log_path = Path(OLLAMA_LOG_LOCATION).expanduser()
    if not log_path.exists():
        return None

    try:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    pattern = re.compile(rf"level={re.escape(level)}[^\n]*?{LOG_MESSAGE_PATTERN}")
    matches = list(pattern.finditer(log_text))
    if not matches:
        return None
    return matches[-1].group(1)


def ensure_history_dir():
    """Ensure the history directory exists"""
    HISTORY_DIR.mkdir(exist_ok=True)


def parse_history_id(path):
    """Extract and validate a history id from a request path."""
    if not path.startswith("/history/"):
        return None

    image_name = path.split("/history/", 1)[1]
    if image_name.endswith(".png"):
        image_name = image_name[:-4]

    if not image_name or not HISTORY_ID_PATTERN.fullmatch(image_name):
        return None

    return image_name


def resolve_history_path(image_name, suffix):
    """Resolve a history file path and ensure it stays under HISTORY_DIR."""
    base_dir = HISTORY_DIR.resolve()
    candidate = (base_dir / f"{image_name}{suffix}").resolve()
    if base_dir not in candidate.parents:
        return None
    return candidate


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

        elif self.path == "/ollamalog/warn":
            message = get_latest_log_message("WARN")
            if message is None:
                error_msg = json.dumps({
                    "error": "No WARN entry found"
                })
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(error_msg.encode())
            else:
                response_data = json.dumps({
                    "message": message
                })
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response_data.encode("utf-8"))

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
                            if "image" in item_data:
                                item_data.pop("image")
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
            image_name = parse_history_id(self.path)
            if not image_name:
                self.send_error(400, "Invalid history id")
                return

            try:
                ensure_history_dir()
                image_path = resolve_history_path(image_name, ".png")
                json_path = resolve_history_path(image_name, ".json")
                if not image_path or not json_path:
                    self.send_error(400, "Invalid history path")
                    return

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
                    request_data = json.loads(body)
                    print(json.dumps(request_data, indent=4), flush=True)
                except json.JSONDecodeError:
                    error_msg = json.dumps({
                        "error": "Invalid JSON body"
                    })
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(error_msg.encode())
                    return

                # Convert any newline or carriage returns in the prompt to spaces.
                request_data['prompt'] = request_data['prompt'].replace('\n', ' ').replace('\r', ' ')

                reformatted_body = json.dumps(request_data)

                print(f'Calling Ollama API with: {json.dumps(request_data, indent=4)}')

                # Forward the request to Ollama
                req = urllib.request.Request(
                    OLLAMA_API_URL + "/generate",
                    data=reformatted_body.encode("utf-8"),
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
                        except Exception as e:
                            print(f"Error parsing stream line: {e}", flush=True)

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

    def do_DELETE(self):
        """Handle DELETE requests for history items"""
        if self.path.startswith("/history/"):
            # Extract image name from path (e.g., /history/20260123123453)
            image_name = parse_history_id(self.path)
            if not image_name:
                response_data = {
                    "SUCCESS": False,
                    "error": "Invalid history id"
                }
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                return

            try:
                ensure_history_dir()
                image_path = resolve_history_path(image_name, ".png")
                json_path = resolve_history_path(image_name, ".json")
                if not image_path or not json_path:
                    response_data = {
                        "SUCCESS": False,
                        "error": "Invalid history path"
                    }
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode("utf-8"))
                    return

                # Check if files exist
                image_exists = image_path.exists()
                json_exists = json_path.exists()

                if not image_exists and not json_exists:
                    response_data = {
                        "SUCCESS": False,
                        "error": f"Image not found: {image_name}"
                    }
                    self.send_response(404)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode("utf-8"))
                    return

                # Delete both files if they exist
                if image_exists:
                    image_path.unlink()
                if json_exists:
                    json_path.unlink()

                response_data = {"SUCCESS": True}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))

                print(f"✓ Deleted history item: {image_name}", flush=True)

            except Exception as e:
                response_data = {
                    "SUCCESS": False,
                    "error": str(e)
                }
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                print(f"Error deleting history item {image_name}: {e}", flush=True)
        else:
            self.send_error(404, "Endpoint not found")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    server_address = ("", PORT)
    httpd = ThreadingHTTPServer(server_address, ProxyHandler)

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
