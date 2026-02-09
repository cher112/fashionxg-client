# FashionXG Client

Mac 本地处理客户端 — AI 驱动的时尚图片标注与筛选系统。

Mac local processing client for FashionXG — an AI-powered fashion image tagging and curation system.

---

## 功能简介 / What It Does

本客户端运行在 Mac 上，连接 FashionXG 云端服务器 (`https://design.chermz112.xyz`)，完成以下工作：

1. 从服务器 API 拉取待处理图片
2. 通过本地 ComfyUI 流水线处理（WD14 Tagger 提取标签 + Aesthetic Predictor v2.5 审美评分）
3. 应用复合过滤逻辑（黑名单标签、偏好匹配、审美评分）
4. 将结果（标签、分数、描述）上传回服务器

设计师在 Web 端浏览已标注的图片，通过点赞/点踩反馈来优化后续筛选。

---

## 系统架构 / Architecture

```
云端服务器 Cloud Server (design.chermz112.xyz)
├── FastAPI 后端 + SQLite 数据库
├── Pinterest 爬虫（每日）
└── Web 瀑布流画廊，供设计师浏览评审
        ↕  API 调用
Mac 本地客户端 (本仓库)
├── comfy_bridge.py → 调度整个流水线
├── ComfyUI (本地) → WD14 标签提取 + 审美评分
└── preference_profile.json → 设计师偏好数据
```

---

## 环境要求 / Prerequisites

- macOS，Apple Silicon（M1/M2/M3）
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) 安装在 `~/ComfyUI`
- ComfyUI 自定义节点：
  - [ComfyUI-WD14-Tagger](https://github.com/pythongosssss/ComfyUI-WD14-Tagger)
  - [ComfyUI-Aesthetic-Predictor-V2.5](https://github.com/discus0434/comfyui-aesthetic-predictor-v2-5)
- Python 3.10+

---

## 安装 / Setup

```bash
cd /path/to/fashionxg-client

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements_bridge.txt
```

确保 `.env` 文件包含：
```
FASHIONXG_SERVER=https://design.chermz112.xyz
```

---

## 使用方式 / Usage

### 1. 启动 ComfyUI

```bash
cd ~/ComfyUI && source venv/bin/activate
python main.py --listen 127.0.0.1 --port 8188
```

### 2. 运行桥接脚本

**单次处理一批：**
```bash
source venv/bin/activate
python comfy_bridge.py --once --batch-size 100
```

**持续模式（前台运行）：**
```bash
python comfy_bridge.py --batch-size 200 --sleep 10
```

**后台运行：**
```bash
./run_background.sh
```

**开机自动启动（LaunchAgent）：**
```bash
# 安装
cp com.fashionxg.bridge.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.fashionxg.bridge.plist

# 卸载
launchctl unload ~/Library/LaunchAgents/com.fashionxg.bridge.plist
rm ~/Library/LaunchAgents/com.fashionxg.bridge.plist
```

### 3. 更新偏好配置（可选）

在 Web 端积累了足够的点赞/点踩后，运行以下命令更新本地偏好：
```bash
python update_preference_lib.py
```

---

## 文件结构 / File Structure

```
├── comfy_bridge.py            # 主桥接脚本 / Main bridge script
├── fashion_tagger_api.json    # ComfyUI 工作流 (API 格式)
├── update_preference_lib.py   # 从反馈数据构建偏好配置
├── preference_profile.json    # 设计师偏好数据
├── check_setup.py             # 环境检查脚本
├── run_lazy.sh                # 后台运行（自动启动 ComfyUI）
├── run_background.sh          # 简单后台运行
├── com.fashionxg.bridge.plist # macOS LaunchAgent 配置
├── requirements_bridge.txt    # Python 依赖
└── .env                       # 服务器地址配置
```

---

## 命令行参数 / CLI Options

```
python comfy_bridge.py [OPTIONS]

--batch-size N    每批处理图片数 (默认: 10)
--sleep N         批次间休息分钟数 (默认: 5)
--once            只处理一批后退出
--server URL      覆盖服务器地址
```

---

## 筛选逻辑 / Filtering Logic

每张图片获得一个复合评分：

```
最终得分 = 审美评分 * 0.4 + 相似度 * 0.4 + 标签匹配度 * 0.2
```

- **硬过滤 / Hard filter**：命中黑名单标签（text, watermark, meme, blurry）的图片直接剔除
- **审美评分 / Aesthetic score**：Aesthetic Predictor v2.5 输出，0-10 分
- **标签匹配 / Tag match**：图片标签与设计师偏好标签的重合度
- **视觉相似度 / Similarity**：与已点赞图片的 CLIP 向量距离（有数据时启用）

---

## 监控 / Monitoring

```bash
# 查看桥接日志
tail -f comfy_bridge.log

# 查看 ComfyUI 日志
tail -f /tmp/comfyui.log

# 查看服务器统计
curl -s https://design.chermz112.xyz/api/stats | python3 -m json.tool
```

---

## 常见问题 / FAQ

**Q: ComfyUI 启动失败？**
```bash
# 检查端口是否被占用
lsof -i :8188
# 杀掉占用进程
pkill -f "python main.py"
```

**Q: 处理速度？**
首次运行需下载模型，之后每张图约 3 秒。

**Q: 如何查看已处理数量？**
```bash
curl -s https://design.chermz112.xyz/api/stats
```

**Q: 修改处理间隔？**
编辑 `run_lazy.sh` 中的 `sleep 3600`（单位：秒），或使用 `--sleep` 参数。

---

## License

Private project.
