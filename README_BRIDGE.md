# FashionXG Mac Local Processing Setup

This directory contains the Mac local processing scripts that bridge your cloud server with ComfyUI for AI-powered fashion image tagging.

## 📋 Prerequisites

1. **ComfyUI Installation** (see installation instructions below)
2. **Python 3.8+**
3. **Required Python packages**

## 🚀 Quick Start

### Step 1: Install ComfyUI

```bash
# Clone ComfyUI
cd ~ && git clone https://github.com/comfyanonymous/ComfyUI.git

# Install dependencies
cd ~/ComfyUI && pip install -r requirements.txt

# Install required custom nodes
cd ~/ComfyUI/custom_nodes

# WD14 Tagger for industrial-grade tags
git clone https://github.com/pythongosssss/ComfyUI-WD14-Tagger.git

# Florence-2 for high-quality descriptions
git clone https://github.com/kijai/ComfyUI-Florence2.git

# Logic nodes (optional)
git clone https://github.com/WASasquatch/was-node-suite-comfyui.git
```

### Step 2: Create ComfyUI Workflow

1. Start ComfyUI:
   ```bash
   cd ~/ComfyUI && python main.py --listen 127.0.0.1 --port 8188
   ```

2. Open browser: `http://127.0.0.1:8188`

3. Build your workflow with these nodes:
   - **Load Image** → Input node
   - **WD14 Tagger** → Extract fashion tags
   - **Florence-2** → Generate descriptions
   - **Aesthetic Predictor** → Score images (optional but recommended)

4. Enable Dev Mode:
   - Settings → Enable Dev mode Options

5. Export workflow:
   - Click "Save (API Format)"
   - Save as `fashion_tagger_api.json` in this directory

### Step 3: Install Bridge Dependencies

```bash
pip install -r requirements_bridge.txt
```

### Step 4: Configure Server URL

```bash
# Set your server URL (default: http://localhost:8000)
export FASHIONXG_SERVER="http://your-server-ip:8000"
```

### Step 5: Build Preference Profile

Run this once to build your initial preference profile from designer feedback:

```bash
python update_preference_lib.py
```

This will:
- Fetch all liked/disliked images from your server
- Extract tag frequencies
- Build `preference_profile.json` for filtering

### Step 6: Run the Bridge

**Single batch mode** (process once and exit):
```bash
python comfy_bridge.py --once
```

**Continuous mode** (recommended for production):
```bash
python comfy_bridge.py --batch-size 10 --sleep 5
```

Options:
- `--batch-size N`: Process N images per batch (default: 10)
- `--sleep N`: Sleep N minutes between batches (default: 5)
- `--once`: Process one batch and exit
- `--server URL`: Override server URL

## 📊 How It Works

### Data Flow

```
Cloud Server → Mac Bridge → ComfyUI → Mac Bridge → Cloud Server
     ↓              ↓           ↓           ↓            ↓
  Pending      Download    AI Process   Filter &    Update DB
  Images        Image      (Tags/Score)  Score      with Results
```

### Processing Pipeline

1. **Fetch**: Pull pending images from server API (`/api/images/pending`)
2. **Download**: Download image to temp directory
3. **Process**: Send to ComfyUI for AI tagging
4. **Filter**: Apply logic filtering:
   - ❌ Blacklist tags (text, watermark, meme)
   - ✅ Tag matching with designer preferences
   - ✅ Composite scoring (aesthetic + similarity + tags)
5. **Upload**: Send results back to server (`/api/tags/update`)
6. **Cleanup**: Delete temporary files
7. **Notify**: macOS notification for high-priority finds

### Priority Scoring

**Formula**: `final_score = aesthetic * 0.4 + similarity * 0.4 + tag_match * 0.2`

**Status Assignment**:
- Score ≥ 0.8 → `process_status = 2` (Archive - high quality)
- Score ≥ 0.5 → `process_status = 1` (Review - medium quality)
- Score < 0.5 → `process_status = -1` (Reject - low quality)
- Blacklist tags → `process_status = -1` (Reject immediately)

## 🔧 Configuration Files

### `fashion_tagger_api.json`
Your ComfyUI workflow exported in API format. **Required**.

### `preference_profile.json`
Designer preference data built from feedback. Contains:
- `liked_tags`: Top tags from liked images
- `disliked_tags`: Top tags from disliked images
- `liked_vectors`: CLIP vectors for similarity matching
- Tag frequencies for scoring

Update regularly with:
```bash
python update_preference_lib.py
```

## 📝 Logs

All operations are logged to `comfy_bridge.log`:
```bash
tail -f comfy_bridge.log
```

## 🔔 Notifications

When a high-priority image is found (score ≥ 0.8), you'll receive a macOS notification:
- Title: "FashionXG: High Priority Image Found"
- Subtitle: Pin ID
- Body: Priority score

## 🛠️ Troubleshooting

### ComfyUI Connection Failed
```bash
# Check if ComfyUI is running
curl http://127.0.0.1:8188

# Start ComfyUI if not running
cd ~/ComfyUI && python main.py --listen 127.0.0.1 --port 8188
```

### Workflow File Not Found
Make sure `fashion_tagger_api.json` exists in this directory. Export it from ComfyUI using "Save (API Format)".

### Server Connection Failed
```bash
# Check server URL
echo $FASHIONXG_SERVER

# Test server connection
curl $FASHIONXG_SERVER/api/stats
```

### No Pending Images
Check your server database:
```bash
# On server
curl http://localhost:8000/api/images/pending
```

## 🔄 Updating Preferences

Run this regularly (e.g., after every 10-20 feedback actions):
```bash
python update_preference_lib.py
```

This ensures the filtering logic stays aligned with your evolving taste.

## 📈 Performance Tips

1. **Batch Size**: Start with 10, increase if your Mac can handle it
2. **Sleep Interval**: 5 minutes is good for continuous operation
3. **ComfyUI Models**: Use quantized models for faster processing
4. **Temp Cleanup**: Automatic - no manual intervention needed

## 🎯 Next Steps

1. ✅ Install ComfyUI and custom nodes
2. ✅ Create and export workflow
3. ✅ Run preference updater
4. ✅ Start bridge in continuous mode
5. 📊 Monitor logs and notifications
6. 🔄 Update preferences regularly

## 📚 Related Files

- `comfy_bridge.py`: Main bridge script
- `update_preference_lib.py`: Preference profile builder
- `requirements_bridge.txt`: Python dependencies
- `task.md`: Original implementation plan
- `readme-web.md`: Server documentation

## 🐛 Issues?

Check logs first:
```bash
tail -n 100 comfy_bridge.log
```

Common issues are usually:
- ComfyUI not running
- Workflow file missing/incorrect
- Server URL misconfigured
- Network connectivity

---

**Tech Stack**: Python • ComfyUI • WebSocket • macOS Notifications
