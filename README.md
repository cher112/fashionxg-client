# 👗 FashionXG Client

> ✨ 给设计师老婆的 AI 时尚灵感助手 ✨
>
> *An AI-powered fashion inspiration assistant — made with love 💕*

每天自动从 Pinterest 收集时尚灵感图，用 AI 打分筛选，只把最好看的呈现给你～

---

## 🌸 它能做什么？

这个小工具安静地跑在 Mac 后台，默默帮你：

1. 🖼️ 从云端拉取 Pinterest 上的时尚图片
2. 🤖 用本地 AI 给每张图打标签 + 审美评分
3. 🎯 过滤掉水印、模糊、低质量的图
4. ☁️ 把打好分的图传回云端，按美感排序展示

然后你只需要打开网页 👉 [design.chermz112.xyz](https://design.chermz112.xyz)，刷好看的图，喜欢的点 ❤️，不喜欢的点 👎，AI 会越来越懂你的审美～

---

## 🏗️ 系统架构

```
☁️  云端服务器 (design.chermz112.xyz)
├── 📦 FastAPI 后端 + 数据库
├── 🕷️ Pinterest 爬虫（每天自动跑）
└── 🖥️ Web 画廊（瀑布流浏览 + 点赞反馈）
          ↕  自动同步
🍎 Mac 本地客户端（就是这个仓库啦）
├── 🔗 comfy_bridge.py → 桥接脚本，调度一切
├── 🎨 ComfyUI → 本地 AI 引擎（标签 + 评分）
└── 💝 preference_profile.json → 记住你喜欢什么风格
```

---

## 📋 需要什么环境

- 🍎 macOS + Apple Silicon（M1/M2/M3/M4）
- 🎨 [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 安装在 `~/ComfyUI`
- 🧩 ComfyUI 插件：
  - [WD14-Tagger](https://github.com/pythongosssss/ComfyUI-WD14-Tagger) — 时尚标签提取
  - [Aesthetic-Predictor-V2.5](https://github.com/discus0434/comfyui-aesthetic-predictor-v2-5) — 审美评分
- 🐍 Python 3.10+

---

## 🚀 安装

```bash
cd /path/to/fashionxg-client

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements_bridge.txt
```

`.env` 文件里写上服务器地址：
```
FASHIONXG_SERVER=https://design.chermz112.xyz
```

---

## 💫 使用方式

### 方式一：开机自动跑（推荐！设置一次就不用管了）

```bash
# 安装开机自启
cp com.fashionxg.bridge.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.fashionxg.bridge.plist
```

装好之后每次开机就会自动在后台运行，合盖休眠也不会中断 🎉

```bash
# 如果想卸载
launchctl unload ~/Library/LaunchAgents/com.fashionxg.bridge.plist
rm ~/Library/LaunchAgents/com.fashionxg.bridge.plist
```

### 方式二：手动运行

先启动 ComfyUI：
```bash
cd ~/ComfyUI && source venv/bin/activate
python main.py --listen 127.0.0.1 --port 8188
```

再启动桥接脚本：
```bash
# 持续跑（每批 200 张，休息 10 分钟）
python comfy_bridge.py --batch-size 200 --sleep 10

# 或者只跑一批就停
python comfy_bridge.py --once --batch-size 100
```

### 🎀 更新审美偏好

在网页上积累了一些 ❤️ 和 👎 之后，跑一下这个让 AI 更懂你：
```bash
python update_preference_lib.py
```

---

## 📁 文件一览

```
├── comfy_bridge.py            # 🔗 主程序，负责拉图→AI处理→上传
├── fashion_tagger_api.json    # 🎨 ComfyUI 工作流配置
├── update_preference_lib.py   # 💝 从你的点赞数据学习偏好
├── preference_profile.json    # 📝 你的审美偏好档案
├── check_setup.py             # 🔍 环境自检脚本
├── run_lazy.sh                # 🚀 后台启动脚本
├── com.fashionxg.bridge.plist # ⚙️ macOS 开机自启配置
├── requirements_bridge.txt    # 📦 Python 依赖
└── .env                       # 🔑 服务器地址
```

---

## 🎯 AI 是怎么打分的？

```
综合得分 = 审美评分 × 0.4 + 风格相似度 × 0.4 + 标签匹配 × 0.2
```

- 🚫 **硬过滤**：有水印、模糊、截图的直接扔掉
- 💎 **审美评分**：AI 判断图片好不好看（0-10 分）
- 🏷️ **标签匹配**：和你喜欢的风格标签有多少重合
- 🔍 **风格相似度**：和你点赞过的图有多像

分越高的图排越前面，但也会混入一些随机的新图，帮你发现新风格～

---

## 🔧 日常查看

```bash
# 看处理日志
tail -f comfy_bridge.log

# 看 ComfyUI 日志
tail -f /tmp/comfyui.log

# 看服务器统计（总共多少图、处理了多少）
curl -s https://design.chermz112.xyz/api/stats | python3 -m json.tool
```

---

## 💌

Made with love for my wife's fashion design journey.

Private project.
