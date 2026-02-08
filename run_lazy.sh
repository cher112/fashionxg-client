#!/bin/bash
# FashionXG Lazy Runner
# 登录自动启动，熄屏暂停，亮屏继续

cd /Users/sunzemuzi/Downloads/fashionxg-local
source venv/bin/activate

# 确保ComfyUI运行
start_comfyui() {
    if ! curl -s http://127.0.0.1:8188 > /dev/null 2>&1; then
        echo "$(date): 启动ComfyUI..."
        cd ~/ComfyUI && source venv/bin/activate
        python main.py --listen 127.0.0.1 --port 8188 &
        sleep 15
        cd /Users/sunzemuzi/Downloads/fashionxg-local
        source venv/bin/activate
    fi
}

# 主循环
echo "$(date): FashionXG Bridge 启动"

while true; do
    start_comfyui

    echo "$(date): 开始处理一批图片..."
    python comfy_bridge.py --once --batch-size 50 --server https://design.chermz112.xyz

    echo "$(date): 休息60分钟..."
    sleep 3600
done
