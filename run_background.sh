#!/bin/bash
# FashionXG 后台运行脚本
# 启动后会在后台持续处理图片，关机自动停止

cd /Users/sunzemuzi/Downloads/fashionxg-local
source venv/bin/activate

echo "🍏 FashionXG Bridge 启动中..."
echo "处理间隔: 每批100张，休息60分钟"
echo "日志文件: /tmp/fashionxg.log"
echo ""

# 先启动ComfyUI（如果没运行）
if ! curl -s http://127.0.0.1:8188 > /dev/null 2>&1; then
    echo "启动 ComfyUI..."
    cd ~/ComfyUI && source venv/bin/activate
    nohup python main.py --listen 127.0.0.1 --port 8188 > /tmp/comfyui.log 2>&1 &
    sleep 10
    cd /Users/sunzemuzi/Downloads/fashionxg-local
fi

# 后台运行bridge
nohup python comfy_bridge.py --batch-size 100 --sleep 60 --server https://design.chermz112.xyz > /tmp/fashionxg.log 2>&1 &

echo "✅ 已在后台启动！"
echo ""
echo "查看日志: tail -f /tmp/fashionxg.log"
echo "停止运行: pkill -f comfy_bridge.py"
