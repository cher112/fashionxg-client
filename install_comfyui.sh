#!/bin/bash
# ComfyUI Quick Install Script for FashionXG

set -e

echo "🎨 ComfyUI Installation Script for FashionXG"
echo "=============================================="
echo ""

# Check if ComfyUI already exists
if [ -d "$HOME/ComfyUI" ]; then
    echo "⚠️  ComfyUI directory already exists at ~/ComfyUI"
    read -p "Do you want to reinstall? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping ComfyUI installation"
        exit 0
    fi
    echo "Removing existing ComfyUI..."
    rm -rf "$HOME/ComfyUI"
fi

echo "📦 Step 1: Cloning ComfyUI..."
cd ~
git clone https://github.com/comfyanonymous/ComfyUI.git
echo "✅ ComfyUI cloned"
echo ""

echo "📦 Step 2: Installing ComfyUI dependencies..."
cd ~/ComfyUI
pip install -r requirements.txt
echo "✅ ComfyUI dependencies installed"
echo ""

echo "📦 Step 3: Installing custom nodes..."
cd ~/ComfyUI/custom_nodes

# WD14 Tagger
echo "  Installing WD14 Tagger..."
git clone https://github.com/pythongosssss/ComfyUI-WD14-Tagger.git
cd ComfyUI-WD14-Tagger
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
cd ..
echo "  ✅ WD14 Tagger installed"

# Florence-2
echo "  Installing Florence-2..."
git clone https://github.com/kijai/ComfyUI-Florence2.git
cd ComfyUI-Florence2
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
cd ..
echo "  ✅ Florence-2 installed"

# WAS Node Suite (for logic nodes)
echo "  Installing WAS Node Suite..."
git clone https://github.com/WASasquatch/was-node-suite-comfyui.git
cd was-node-suite-comfyui
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
cd ..
echo "  ✅ WAS Node Suite installed"

echo ""
echo "✅ All custom nodes installed"
echo ""

echo "=============================================="
echo "🎉 ComfyUI Installation Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start ComfyUI:"
echo "   cd ~/ComfyUI"
echo "   python main.py --listen 127.0.0.1 --port 8188"
echo ""
echo "2. Open browser: http://127.0.0.1:8188"
echo ""
echo "3. Build your workflow:"
echo "   - Add LoadImage node"
echo "   - Add WD14 Tagger node"
echo "   - Add Florence2 node"
echo "   - Add Aesthetic Score node (if available)"
echo "   - Connect them in sequence"
echo ""
echo "4. Export workflow:"
echo "   - Settings → Enable Dev mode Options"
echo "   - Click 'Save (API Format)'"
echo "   - Save as 'fashion_tagger_api.json' in:"
echo "     $(pwd)"
echo ""
echo "5. Test the bridge:"
echo "   cd $(pwd)"
echo "   ./start_bridge.sh --once"
echo ""
