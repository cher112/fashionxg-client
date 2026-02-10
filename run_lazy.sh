#!/bin/bash
# FashionXG Auto Runner
# 开机自启，caffeinate 防休眠中断

cd /Users/sunzemuzi/Downloads/fashionxg-local
source venv/bin/activate

# 确保ComfyUI运行
start_comfyui() {
    if ! curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
        echo "$(date): 启动ComfyUI..."
        cd ~/ComfyUI && source venv/bin/activate
        nohup python main.py --listen 127.0.0.1 --port 8188 > /tmp/comfyui.log 2>&1 &
        echo "$(date): 等待ComfyUI就绪..."
        for i in $(seq 1 30); do
            sleep 2
            if curl -s http://127.0.0.1:8188/system_stats > /dev/null 2>&1; then
                echo "$(date): ComfyUI 已就绪"
                break
            fi
        done
        cd /Users/sunzemuzi/Downloads/fashionxg-local
        source venv/bin/activate
    else
        echo "$(date): ComfyUI 已在运行"
    fi
}

echo "$(date): FashionXG Bridge 启动"

start_comfyui

# caffeinate -i 防止休眠杀进程，持续模式运行
exec caffeinate -i python comfy_bridge.py --batch-size 200 --sleep 10 --server https://design.chermz112.xyz
