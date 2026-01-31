# 🤖 RecallAI Bot Creator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Zoom%20%7C%20Teams%20%7C%20Google%20Meet-orange.svg)

**Create AI meeting bots with animated avatars for Zoom, Microsoft Teams, and Google Meet**

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#%EF%B8%8F-configuration)

</div>

---

## ✨ Features

- 🎬 **Animated GIF Avatars** - Display dynamic, eye-catching animations as your bot's video feed
- 🔄 **Multi-Platform Support** - Works with Zoom, Microsoft Teams, Google Meet, and Webex
- 🖼️ **Fullscreen Display** - GIFs render edge-to-edge for maximum visual impact
- 🚀 **Simple Setup** - Get running in under 5 minutes
- 🎨 **Customizable** - Use any GIF animation you want

## 📁 Project Structure

```
RecallAI-Bot-Creator/
├── src/
│   ├── create_bot.py              # Basic bot (static image)
│   └── create_bot_with_animation.py   # Animated GIF bot
├── assets/
│   └── gifs/
│       ├── robinhood.gif          # Sample: Robinhood-style orb
│       └── deel.gif               # Sample: Deel-style animation
├── examples/                      # Example configurations
├── requirements.txt               # Python dependencies
└── README.md                      # You are here!
```

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/matiasmichael/RecallAI-Bot-Creator.git
cd RecallAI-Bot-Creator

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure ngrok (one-time setup)
ngrok config add-authtoken YOUR_NGROK_TOKEN

# 5. Run the bot!
python src/create_bot_with_animation.py assets/gifs/robinhood.gif
```

## 📦 Installation

### Prerequisites

- **Python 3.10+** - [Download here](https://www.python.org/downloads/)
- **ngrok account** (free) - [Sign up here](https://dashboard.ngrok.com/signup)
- **RecallAI API key** - [Get one here](https://recall.ai)

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/matiasmichael/RecallAI-Bot-Creator.git
cd RecallAI-Bot-Creator
```

#### 2. Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure ngrok

ngrok creates a secure tunnel so the bot can display your animation.

1. Sign up at [ngrok.com](https://dashboard.ngrok.com/signup) (free)
2. Get your authtoken from [dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Configure ngrok:

```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

## 📖 Usage

### Running with Animated GIF

```bash
# Use the default GIF (robinhood.gif)
python src/create_bot_with_animation.py

# Use a specific GIF
python src/create_bot_with_animation.py assets/gifs/deel.gif

# Use your own GIF
python src/create_bot_with_animation.py /path/to/your/animation.gif
```

### Running with Static Image (Basic Mode)

```bash
python src/create_bot.py
```

### What Happens

1. 🖥️ A local server starts to serve your animation
2. 🌐 ngrok creates a public URL for the server
3. 📝 You paste your meeting link
4. 🤖 The bot joins with your animated avatar!

> ⚠️ **Important:** Keep the script running while the bot is in the meeting. The animation is served from your computer.

## ⚙️ Configuration

### Customizing the Bot

Edit `src/create_bot_with_animation.py` to change:

```python
# Bot name displayed in meetings
DEFAULT_BOT_NAME = "Clarity's Security Agent"

# RecallAI API settings
RECALLAI_API_KEY = "your-api-key-here"
RECALLAI_API_URL = "https://us-west-2.recall.ai/api/v1"

# Local server port (change if 8765 is in use)
LOCAL_SERVER_PORT = 8765
```

### Using Your Own GIFs

For best results, your GIF should:

- ✅ Be **16:9 aspect ratio** (1280x720 recommended)
- ✅ Be under **10 MB** in size
- ✅ Have a **seamless loop** for continuous playback
- ✅ Use **solid backgrounds** that match your brand

## 🎨 Included Sample GIFs

| GIF | Description | Best For |
|-----|-------------|----------|
| `robinhood.gif` | Animated blue/green orb with Robinhood branding | Fintech, Modern SaaS |
| `deel.gif` | Professional animated avatar | HR Tech, Enterprise |

## 🔧 Troubleshooting

### "Address already in use" Error

```bash
# Kill any existing processes on port 8765
lsof -ti:8765 | xargs kill -9
```

### ngrok Authentication Failed

```bash
# Re-configure your ngrok token
ngrok config add-authtoken YOUR_TOKEN
```

### Bot Not Showing Animation

- Ensure the script is still running
- Check that your GIF file path is correct
- Verify ngrok tunnel is active (you should see a URL printed)

### "python: command not found"

Use `python3` instead of `python`, or ensure Python is in your PATH.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Recall.ai](https://recall.ai) - Meeting bot infrastructure
- [ngrok](https://ngrok.com) - Secure tunneling

---

<div align="center">

**Built with ❤️ by the Clarity team**

[Report Bug](https://github.com/matiasmichael/RecallAI-Bot-Creator/issues) • [Request Feature](https://github.com/matiasmichael/RecallAI-Bot-Creator/issues)

</div>
