#!/usr/bin/env python3
"""
RecallAI Bot Creator - Web Interface
A simple web UI for team members to deploy animated bots to meetings.
"""

import os
import sys
import base64
import threading
import time
import http.server
import socketserver
from pathlib import Path

import httpx
from flask import Flask, render_template, request, jsonify
from pyngrok import ngrok

# Configuration
RECALL_API_KEY = "60167bf56c5d272df513f57b2fc097f530bfd52c"
RECALL_API_BASE = "https://us-west-2.recall.ai/api/v1"
DEFAULT_BOT_NAME = "Clarity's Security Agent"
BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets" / "gifs"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))

# Store active bots and their servers
active_bots = {}
next_port = 8800  # Start port for GIF servers


def get_available_gifs():
    """Scan the assets/gifs directory for available GIFs."""
    gifs = []
    if ASSETS_DIR.exists():
        for gif_file in sorted(ASSETS_DIR.glob("*.gif")):
            # Create display name from filename (e.g., "robinhood.gif" -> "Robinhood")
            display_name = gif_file.stem.replace("_", " ").replace("-", " ").title()
            gifs.append({
                "filename": gif_file.name,
                "display_name": display_name,
                "path": str(gif_file)
            })
    return gifs


def create_gif_html(gif_path: str) -> str:
    """Create HTML page with embedded GIF for bot camera."""
    with open(gif_path, "rb") as f:
        gif_data = base64.b64encode(f.read()).decode("utf-8")
    
    # Optimized HTML with instant black background and preloaded GIF
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ 
            width: 100%; 
            height: 100%; 
            overflow: hidden;
            background: #000;
        }}
        img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            opacity: 0;
            transition: opacity 0.2s ease-in;
        }}
        img.loaded {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <img id="gif" alt="Bot Animation" onload="this.classList.add('loaded')">
    <script>
        // Start loading immediately
        const img = document.getElementById('gif');
        img.src = 'data:image/gif;base64,{gif_data}';
    </script>
</body>
</html>"""


class GifHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve the GIF HTML page."""
    
    html_content = ""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(self.html_content.encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def start_gif_server(gif_path: str, port: int) -> tuple:
    """Start a local server serving the GIF and return ngrok URL."""
    html_content = create_gif_html(gif_path)
    
    # Store HTML content as class variable for handler
    GifHandler.html_content = html_content
    
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", port), GifHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Create ngrok tunnel
    public_url = ngrok.connect(port, "http").public_url
    
    return server, public_url


def create_bot(meeting_url: str, gif_path: str, bot_name: str = DEFAULT_BOT_NAME) -> dict:
    """Create a RecallAI bot with animated GIF."""
    global next_port
    
    # Start server for this bot
    port = next_port
    next_port += 1
    
    server, public_url = start_gif_server(gif_path, port)
    
    # Create bot via RecallAI API
    headers = {
        "Authorization": f"Token {RECALL_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "meeting_url": meeting_url,
        "bot_name": bot_name,
        "variant": {
            "zoom": "web_4_core",
            "google_meet": "web_4_core",
            "microsoft_teams": "web_4_core",
            "webex": "web_4_core"
        },
        "output_media": {
            "camera": {
                "kind": "webpage",
                "config": {
                    "url": public_url
                }
            }
        }
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{RECALL_API_BASE}/bot",
            headers=headers,
            json=payload
        )
        
        # Check for errors and capture details
        if response.status_code >= 400:
            error_detail = response.text
            print(f"API Error {response.status_code}: {error_detail}")
            raise Exception(f"RecallAI API Error: {error_detail}")
        
        bot_data = response.json()
    
    bot_id = bot_data.get("id")
    
    # Store bot info
    active_bots[bot_id] = {
        "server": server,
        "port": port,
        "public_url": public_url,
        "meeting_url": meeting_url,
        "gif_path": gif_path,
        "bot_name": bot_name,
        "created_at": time.time()
    }
    
    return {
        "bot_id": bot_id,
        "bot_name": bot_name,
        "public_url": public_url,
        "status": "joining"
    }


def stop_bot(bot_id: str) -> bool:
    """Stop a bot and clean up its resources."""
    if bot_id in active_bots:
        bot_info = active_bots[bot_id]
        
        # Stop the server
        try:
            bot_info["server"].shutdown()
        except:
            pass
        
        # Disconnect ngrok
        try:
            ngrok.disconnect(bot_info["public_url"])
        except:
            pass
        
        del active_bots[bot_id]
        return True
    return False


@app.route("/")
def index():
    """Render the main UI."""
    gifs = get_available_gifs()
    return render_template("index.html", gifs=gifs, active_bots=active_bots)


@app.route("/api/gifs")
def api_gifs():
    """Get list of available GIFs."""
    return jsonify(get_available_gifs())


@app.route("/api/create-bot", methods=["POST"])
def api_create_bot():
    """Create a new bot."""
    data = request.json
    meeting_url = data.get("meeting_url")
    gif_filename = data.get("gif_filename")
    bot_name = data.get("bot_name", DEFAULT_BOT_NAME)
    
    if not meeting_url:
        return jsonify({"error": "Meeting URL is required"}), 400
    
    if not gif_filename:
        return jsonify({"error": "GIF selection is required"}), 400
    
    gif_path = ASSETS_DIR / gif_filename
    if not gif_path.exists():
        return jsonify({"error": f"GIF not found: {gif_filename}"}), 404
    
    try:
        result = create_bot(meeting_url, str(gif_path), bot_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stop-bot/<bot_id>", methods=["POST"])
def api_stop_bot(bot_id):
    """Stop a running bot."""
    if stop_bot(bot_id):
        return jsonify({"success": True})
    return jsonify({"error": "Bot not found"}), 404


@app.route("/api/active-bots")
def api_active_bots():
    """Get list of active bots."""
    bots = []
    for bot_id, info in active_bots.items():
        bots.append({
            "bot_id": bot_id,
            "bot_name": info["bot_name"],
            "meeting_url": info["meeting_url"],
            "created_at": info["created_at"]
        })
    return jsonify(bots)


if __name__ == "__main__":
    print("=" * 50)
    print("RecallAI Bot Creator - Web Interface")
    print("=" * 50)
    print()
    
    # Check for GIFs
    gifs = get_available_gifs()
    print(f"Found {len(gifs)} GIFs in {ASSETS_DIR}:")
    for gif in gifs:
        print(f"  • {gif['display_name']} ({gif['filename']})")
    print()
    
    # Start Flask app
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting web server on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    print()
    
    app.run(host="0.0.0.0", port=port, debug=False)
