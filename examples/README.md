# Example Configuration Files

This folder contains example configurations and use cases for the RecallAI Bot Creator.

## Quick Examples

### Basic Usage

```bash
# Run with default settings
python ../src/create_bot_with_animation.py

# Run with a specific GIF
python ../src/create_bot_with_animation.py ../assets/gifs/deel.gif
```

### Custom Bot Name

Edit `src/create_bot_with_animation.py` and change:

```python
DEFAULT_BOT_NAME = "Your Company's AI Assistant"
```

### Using Different RecallAI Regions

Available regions:
- `us-west-2` (default)
- `us-east-1`
- `eu-central-1`
- `ap-northeast-1`

```python
RECALLAI_API_URL = "https://eu-central-1.recall.ai/api/v1"
```

## Meeting Platform Notes

### Zoom
- Works out of the box
- Bot appears as a regular participant

### Google Meet
- Works out of the box
- May require host to admit the bot

### Microsoft Teams
- Works with most configurations
- Enterprise accounts may have restrictions

### Webex
- Requires additional Webex bot setup
- See RecallAI documentation for details
