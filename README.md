# FashionXG Client

Mac local processing client for FashionXG — an AI-powered fashion image tagging and curation system.

## What It Does

This client runs on your Mac and connects to the FashionXG cloud server (`https://design.chermz112.xyz`). It:

1. Pulls pending images from the server API
2. Sends each image through a local ComfyUI pipeline (WD14 Tagger + Aesthetic Predictor v2.5)
3. Applies composite filtering logic (blacklist tags, preference matching, aesthetic scoring)
4. Uploads results (tags, scores, descriptions) back to the server

Designers then review the tagged images on the web interface, providing like/dislike feedback that refines future filtering.

## Architecture

```
Cloud Server (design.chermz112.xyz)
├── FastAPI backend + SQLite database
├── Pinterest crawler (daily)
└── Web gallery for designer review
        ↕  API calls
Mac Client (this repo)
├── comfy_bridge.py → orchestrates the pipeline
├── ComfyUI (local) → WD14 tagging + aesthetic scoring
└── preference_profile.json → learned designer preferences
```

## Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) installed at `~/ComfyUI`
- ComfyUI custom nodes:
  - [ComfyUI-WD14-Tagger](https://github.com/pythongosssss/ComfyUI-WD14-Tagger)
  - [ComfyUI-Aesthetic-Predictor-V2.5](https://github.com/discus0434/comfyui-aesthetic-predictor-v2-5)
- Python 3.10+

## Setup

```bash
cd /path/to/fashionxg-client

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements_bridge.txt
```

Make sure `.env` contains:
```
FASHIONXG_SERVER=https://design.chermz112.xyz
```

## Usage

### 1. Start ComfyUI

```bash
cd ~/ComfyUI && source venv/bin/activate
python main.py --listen 127.0.0.1 --port 8188
```

### 2. Run the bridge

**Single batch:**
```bash
source venv/bin/activate
python comfy_bridge.py --once --batch-size 100
```

**Continuous mode (foreground):**
```bash
python comfy_bridge.py --batch-size 200 --sleep 10
```

**Background mode:**
```bash
./run_background.sh
```

**Auto-start on login (LaunchAgent):**
```bash
cp com.fashionxg.bridge.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.fashionxg.bridge.plist
```

### 3. Update preferences (optional)

After accumulating likes/dislikes on the web interface:
```bash
python update_preference_lib.py
```

## File Structure

```
├── comfy_bridge.py            # Main bridge script
├── fashion_tagger_api.json    # ComfyUI workflow (API format)
├── update_preference_lib.py   # Build preference profile from feedback
├── preference_profile.json    # Designer preference data
├── check_setup.py             # Verify prerequisites
├── run_lazy.sh                # Background runner with auto ComfyUI start
├── run_background.sh          # Simple background runner
├── com.fashionxg.bridge.plist # macOS LaunchAgent config
├── requirements_bridge.txt    # Python dependencies
└── .env                       # Server URL config
```

## CLI Options

```
python comfy_bridge.py [OPTIONS]

--batch-size N    Images per batch (default: 10)
--sleep N         Minutes between batches (default: 5)
--once            Process one batch and exit
--server URL      Override server URL
```

## Filtering Logic

Each image gets a composite score:

```
final_score = aesthetic_score * 0.4 + similarity * 0.4 + tag_match * 0.2
```

- **Hard filter**: Images with blacklist tags (text, watermark, meme, blurry) are rejected
- **Aesthetic score**: From Aesthetic Predictor v2.5 (0-10 scale)
- **Tag match**: Overlap between image tags and designer-preferred tags
- **Similarity**: CLIP vector distance to liked images (when available)

## Monitoring

```bash
# View bridge logs
tail -f comfy_bridge.log

# View ComfyUI logs
tail -f /tmp/comfyui.log

# Check server stats
curl -s https://design.chermz112.xyz/api/stats | python3 -m json.tool
```

## License

Private project.
