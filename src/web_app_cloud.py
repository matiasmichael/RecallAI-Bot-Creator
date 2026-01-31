#!/usr/bin/env python3
"""
RecallAI Bot Creator - Cloud Web Interface
A production-ready web UI for deploying animated bots to meetings.
No ngrok required - serves GIF pages directly from the cloud server.
"""

import os
import base64
import time
import uuid
from pathlib import Path

import httpx
from flask import Flask, render_template, request, jsonify, Response

# Configuration
RECALL_API_KEY = os.environ.get("RECALL_API_KEY", "60167bf56c5d272df513f57b2fc097f530bfd52c")
RECALL_API_BASE = "https://us-west-2.recall.ai/api/v1"
DEFAULT_BOT_NAME = "Clarity's Security Agent"

# Paths
BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets" / "gifs"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))

# Store active bots and their GIF data
active_bots = {}
# Cache for GIF HTML pages (bot_id -> html_content)
bot_pages = {}


def get_available_gifs():
    """Scan the assets/gifs directory for available GIFs."""
    gifs = []
    if ASSETS_DIR.exists():
        for gif_file in sorted(ASSETS_DIR.glob("*.gif")):
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
        }}
    </style>
</head>
<body>
    <img src="data:image/gif;base64,{gif_data}" alt="Bot Animation">
</body>
</html>"""


def get_base_url():
    """Get the base URL for this server."""
    # Check for common cloud platform environment variables
    if os.environ.get("RAILWAY_PUBLIC_DOMAIN"):
        return f"https://{os.environ['RAILWAY_PUBLIC_DOMAIN']}"
    elif os.environ.get("RENDER_EXTERNAL_URL"):
        return os.environ["RENDER_EXTERNAL_URL"]
    elif os.environ.get("FLY_APP_NAME"):
        return f"https://{os.environ['FLY_APP_NAME']}.fly.dev"
    elif os.environ.get("BASE_URL"):
        return os.environ["BASE_URL"]
    else:
        # Local development fallback
        return "http://localhost:5001"


def create_bot(meeting_url: str, gif_path: str, bot_name: str = DEFAULT_BOT_NAME) -> dict:
    """Create a RecallAI bot with animated GIF."""
    
    # Generate unique ID for this bot's camera page
    page_id = str(uuid.uuid4())[:8]
    
    # Create and cache the HTML page for this bot
    html_content = create_gif_html(gif_path)
    bot_pages[page_id] = html_content
    
    # Build the camera URL that RecallAI will use
    base_url = get_base_url()
    camera_url = f"{base_url}/camera/{page_id}"
    
    print(f"Creating bot with camera URL: {camera_url}")
    
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
                    "url": camera_url
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
        
        if response.status_code >= 400:
            error_detail = response.text
            print(f"API Error {response.status_code}: {error_detail}")
            # Clean up the page we created
            del bot_pages[page_id]
            raise Exception(f"RecallAI API Error: {error_detail}")
        
        bot_data = response.json()
    
    bot_id = bot_data.get("id")
    
    # Store bot info
    active_bots[bot_id] = {
        "page_id": page_id,
        "camera_url": camera_url,
        "meeting_url": meeting_url,
        "gif_path": gif_path,
        "bot_name": bot_name,
        "created_at": time.time()
    }
    
    return {
        "bot_id": bot_id,
        "bot_name": bot_name,
        "camera_url": camera_url,
        "status": "joining"
    }


def stop_bot(bot_id: str) -> bool:
    """Stop a bot and clean up its resources."""
    if bot_id in active_bots:
        bot_info = active_bots[bot_id]
        
        # Remove the cached page
        page_id = bot_info.get("page_id")
        if page_id and page_id in bot_pages:
            del bot_pages[page_id]
        
        del active_bots[bot_id]
        return True
    return False


# =============================================================================
# Routes
# =============================================================================

@app.route("/")
def index():
    """Render the main UI."""
    gifs = get_available_gifs()
    return render_template("index.html", gifs=gifs, active_bots=active_bots)


@app.route("/camera/<page_id>")
def camera_page(page_id):
    """Serve the camera page for a bot."""
    if page_id in bot_pages:
        return Response(bot_pages[page_id], mimetype='text/html')
    else:
        return "Bot not found", 404


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


@app.route("/health")
def health():
    """Health check endpoint for cloud platforms."""
    return jsonify({"status": "healthy", "active_bots": len(active_bots)})


if __name__ == "__main__":
    print("=" * 50)
    print("RecallAI Bot Creator - Cloud Web Interface")
    print("=" * 50)
    print()
    
    gifs = get_available_gifs()
    print(f"Found {len(gifs)} GIFs in {ASSETS_DIR}:")
    for gif in gifs:
        print(f"  • {gif['display_name']} ({gif['filename']})")
    print()
    
    base_url = get_base_url()
    print(f"Base URL: {base_url}")
    print()
    
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting web server on port {port}")
    print()
    
    app.run(host="0.0.0.0", port=port, debug=False)
