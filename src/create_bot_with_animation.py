#!/usr/bin/env python3
"""Self-contained script to create a RecallAI bot with animated GIF support.

This script:
1. Starts a local HTTP server serving an HTML page with your GIF
2. Uses ngrok to expose it publicly (requires ngrok installed and authenticated)
3. Creates a RecallAI bot that displays the animated GIF in the meeting

Usage:
    pip install httpx pyngrok
    python create_bot_with_animation.py

Requirements:
    - ngrok installed and authenticated (ngrok config add-authtoken YOUR_TOKEN)
    - A GIF file (default: bot_avatar.gif in the same directory)
"""

import asyncio
import base64
import http.server
import os
import socketserver
import sys
import threading
from pathlib import Path
from typing import Any

import httpx

# Configuration
RECALLAI_API_KEY = "60167bf56c5d272df513f57b2fc097f530bfd52c"
RECALLAI_API_URL = "https://us-west-2.recall.ai/api/v1"
DEFAULT_BOT_NAME = "Clarity's Security Agent"
LOCAL_SERVER_PORT = 8765

# Default GIF file path (can be overridden)
DEFAULT_GIF_PATH = Path(__file__).parent.parent / "assets" / "gifs" / "robinhood.gif"


def create_html_page(gif_base64: str) -> str:
    """Create an HTML page that displays the animated GIF fullscreen."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Avatar</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html, body {{
            width: 100%;
            height: 100%;
            overflow: hidden;
        }}
        .avatar {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
    </style>
</head>
<body>
    <img class="avatar" src="data:image/gif;base64,{gif_base64}" alt="Bot Avatar">
</body>
</html>"""


class AnimationHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that serves the animated GIF HTML page."""
    
    html_content: str = ""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(self.html_content.encode())
    
    def log_message(self, format, *args):
        # Suppress HTTP request logging
        pass


def start_local_server(html_content: str, port: int) -> socketserver.TCPServer:
    """Start a local HTTP server serving the animated GIF page."""
    AnimationHandler.html_content = html_content
    
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("", port), AnimationHandler)
    
    # Run server in a background thread
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    return server


def load_gif_as_base64(gif_path: Path) -> str | None:
    """Load a GIF file and return its base64-encoded content."""
    if not gif_path.exists():
        print(f"❌ GIF file not found: {gif_path}")
        return None
    
    with open(gif_path, "rb") as f:
        data = f.read()
    
    print(f"Loaded GIF: {gif_path.name} ({len(data)} bytes)")
    return base64.b64encode(data).decode("ascii")


def start_ngrok_tunnel(port: int) -> str | None:
    """Start an ngrok tunnel and return the public URL."""
    try:
        from pyngrok import ngrok
        
        # Start ngrok tunnel
        print(f"Starting ngrok tunnel on port {port}...")
        tunnel = ngrok.connect(port, "http")
        public_url = tunnel.public_url
        
        # Ensure HTTPS
        if public_url.startswith("http://"):
            public_url = public_url.replace("http://", "https://")
        
        print(f"✅ ngrok tunnel active: {public_url}")
        return public_url
        
    except ImportError:
        print("❌ pyngrok not installed. Run: pip install pyngrok")
        return None
    except Exception as e:
        print(f"❌ Failed to start ngrok tunnel: {e}")
        print("   Make sure ngrok is installed and authenticated:")
        print("   1. Install ngrok: brew install ngrok  (or download from ngrok.com)")
        print("   2. Authenticate: ngrok config add-authtoken YOUR_TOKEN")
        return None


def build_request_payload_with_animation(
    meeting_url: str,
    bot_name: str,
    animation_url: str,
) -> dict[str, Any]:
    """Build the request payload for creating a bot with animated output."""
    return {
        "meeting_url": meeting_url,
        "bot_name": bot_name,
        "output_media": {
            "camera": {
                "kind": "webpage",
                "config": {
                    "url": animation_url
                }
            }
        },
        "recording_config": {
            "video_mixed_layout": "speaker_view",
        },
        # Use web_4_core variant for output media support
        "variant": {
            "zoom": "web_4_core",
            "google_meet": "web_4_core",
            "microsoft_teams": "web_4_core",
            "webex": "web_4_core"
        }
    }


async def create_bot_with_animation(
    meeting_url: str,
    animation_url: str,
    bot_name: str | None = None
) -> dict[str, Any] | None:
    """Create a RecallAI bot with animated GIF output.

    Args:
        meeting_url: Zoom, Teams, or Google Meet meeting URL
        animation_url: Public URL serving the animation HTML page
        bot_name: Optional custom bot name

    Returns:
        Bot data dict on success, None on failure
    """
    bot_name = bot_name or DEFAULT_BOT_NAME
    
    payload = build_request_payload_with_animation(meeting_url, bot_name, animation_url)
    
    print(f"Creating animated bot '{bot_name}' for meeting: {meeting_url}")
    
    async with httpx.AsyncClient(
        base_url=RECALLAI_API_URL,
        headers={
            "Authorization": f"Token {RECALLAI_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=30.0,
    ) as client:
        response = await client.post("/bot", json=payload)
        
        if response.status_code >= 400:
            print(f"\n❌ Failed to create bot!")
            print(f"   Error: API returned status {response.status_code}")
            print(f"   Details: {response.text}")
            return None
        
        data = response.json()
        
        print(f"\n✅ Success! Animated bot created and will join your meeting.")
        print(f"   Bot ID: {data.get('id')}")
        print(f"   Bot Name: {data.get('bot_name')}")
        
        return data


def main():
    print("=" * 50)
    print("RecallAI Animated Bot Creator")
    print("=" * 50)
    print()
    
    # Check for GIF file
    gif_path = DEFAULT_GIF_PATH
    
    # Allow custom GIF path via command line
    if len(sys.argv) > 1:
        gif_path = Path(sys.argv[1])
    
    if not gif_path.exists():
        print(f"⚠️  No GIF file found at: {gif_path}")
        print()
        print("Please provide a GIF file in one of these ways:")
        print(f"  1. Place a file named 'bot_avatar.gif' in: {gif_path.parent}")
        print(f"  2. Run with path: python {sys.argv[0]} /path/to/your/animation.gif")
        print()
        
        # Ask user for path
        user_path = input("Or enter the path to your GIF file now: ").strip()
        if user_path:
            gif_path = Path(user_path)
            if not gif_path.exists():
                print(f"\n❌ File not found: {gif_path}")
                return
        else:
            return
    
    # Load GIF
    gif_base64 = load_gif_as_base64(gif_path)
    if not gif_base64:
        return
    
    # Create HTML page with embedded GIF
    html_content = create_html_page(gif_base64)
    
    # Start local server
    print(f"Starting local server on port {LOCAL_SERVER_PORT}...")
    server = start_local_server(html_content, LOCAL_SERVER_PORT)
    print(f"✅ Local server running at http://localhost:{LOCAL_SERVER_PORT}")
    
    # Start ngrok tunnel
    public_url = start_ngrok_tunnel(LOCAL_SERVER_PORT)
    if not public_url:
        server.shutdown()
        return
    
    print()
    meeting_url = input("Please paste your Zoom, Teams, or Google Meet link: ").strip()
    
    if not meeting_url:
        print("\n❌ Error: No meeting link provided.")
        server.shutdown()
        return
    
    print()
    
    # Create the bot
    result = asyncio.run(create_bot_with_animation(meeting_url, public_url))
    
    if result:
        print()
        print("=" * 50)
        print("🎉 Your animated bot is joining the meeting!")
        print("=" * 50)
        print()
        print("⚠️  IMPORTANT: Keep this script running while the bot is in the meeting!")
        print("   The animation is served from your computer via ngrok.")
        print()
        print("Press Ctrl+C to stop the server and exit.")
        
        try:
            # Keep the server running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
    
    server.shutdown()


if __name__ == "__main__":
    main()
