#!/bin/bash
# FashionXG Bridge Startup Script

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🍏 FashionXG Mac Local Processing Bridge"
echo "========================================"
echo ""

# Check if ComfyUI is running
echo "Checking ComfyUI status..."
if ! curl -s http://127.0.0.1:8188 > /dev/null 2>&1; then
    echo "❌ ComfyUI is not running!"
    echo ""
    echo "Please start ComfyUI first:"
    echo "  cd ~/ComfyUI && python main.py --listen 127.0.0.1 --port 8188"
    echo ""
    exit 1
fi
echo "✅ ComfyUI is running"
echo ""

# Check if workflow file exists
if [ ! -f "fashion_tagger_api.json" ]; then
    echo "❌ Workflow file not found: fashion_tagger_api.json"
    echo ""
    echo "Please export your ComfyUI workflow:"
    echo "  1. Open http://127.0.0.1:8188"
    echo "  2. Build workflow with WD14Tagger + Florence2 + AestheticScore"
    echo "  3. Enable Dev Mode in Settings"
    echo "  4. Click 'Save (API Format)'"
    echo "  5. Save as 'fashion_tagger_api.json' in this directory"
    echo ""
    exit 1
fi
echo "✅ Workflow file found"
echo ""

# Check if preference profile exists
if [ ! -f "preference_profile.json" ]; then
    echo "⚠️  Preference profile not found"
    echo "Building preference profile from server..."
    python update_preference_lib.py
    echo ""
fi

# Check server connection
SERVER_URL=${FASHIONXG_SERVER:-"http://localhost:8000"}
echo "Checking server connection: $SERVER_URL"
if ! curl -s "$SERVER_URL/api/stats" > /dev/null 2>&1; then
    echo "❌ Cannot connect to server: $SERVER_URL"
    echo ""
    echo "Please check:"
    echo "  1. Server is running"
    echo "  2. FASHIONXG_SERVER environment variable is set correctly"
    echo "     export FASHIONXG_SERVER='http://your-server:8000'"
    echo ""
    exit 1
fi
echo "✅ Server connection OK"
echo ""

# Parse command line arguments
MODE="continuous"
BATCH_SIZE=10
SLEEP_INTERVAL=5

while [[ $# -gt 0 ]]; do
    case $1 in
        --once)
            MODE="once"
            shift
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --sleep)
            SLEEP_INTERVAL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--once] [--batch-size N] [--sleep N]"
            exit 1
            ;;
    esac
done

# Start bridge
echo "Starting FashionXG Bridge..."
echo "  Mode: $MODE"
echo "  Batch Size: $BATCH_SIZE"
if [ "$MODE" = "continuous" ]; then
    echo "  Sleep Interval: $SLEEP_INTERVAL minutes"
fi
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

if [ "$MODE" = "once" ]; then
    python comfy_bridge.py --once --batch-size "$BATCH_SIZE" --server "$SERVER_URL"
else
    python comfy_bridge.py --batch-size "$BATCH_SIZE" --sleep "$SLEEP_INTERVAL" --server "$SERVER_URL"
fi
