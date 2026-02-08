# FashionXG v2.0 · 服装设计AI训练数据集管理系统

> 从Pinterest爬取、AI评分、到设计师审阅的完整数据流水线

## 🎯 项目目标

为服装设计师积累高质量的训练数据集，支持：
- **精准标签**: 材质、剪裁、风格、细节
- **审美评分**: 自动化审美评分 + 设计师反馈
- **垂直度**: 聚焦高品质时尚设计

## 📁 项目结构（v2.0 重构）

```
fashionxg/
├── backend/                    # 后端代码（新架构）
│   ├── api/                    # Web API
│   │   ├── app.py             # Flask应用（原有）
│   │   ├── fastapi_app.py     # FastAPI应用（新增）
│   │   ├── run_web.py         # Web启动脚本
│   │   └── gunicorn_conf.py   # Gunicorn配置
│   ├── crawler/               # 爬虫模块
│   │   └── pinterest_crawler.py
│   ├── processors/            # 图片处理器
│   │   ├── process_images.py
│   │   ├── download_images.py
│   │   └── download_pending_images.py
│   ├── tasks/                 # 定时任务
│   │   ├── run_cron_tasks.py
│   │   └── run_crawler.py
│   └── core/                  # 核心模块
│       ├── database.py        # 数据库管理
│       ├── migrate_database.py # 数据库迁移
│       └── ...                # 其他核心工具
├── frontend/                   # 前端资源
│   ├── static/                # 静态文件
│   └── templates/             # 模板文件
├── deploy/                     # 部署配置
│   └── nginx.conf             # Nginx配置
├── scripts/                    # 工具脚本
│   └── maintenance/           # 维护脚本
├── data/                       # 数据目录
│   ├── images/                # 图片存储
│   ├── metadata/              # 元数据
│   ├── logs/                  # 日志
│   └── fashion.db             # SQLite数据库
├── config/                     # 配置文件
├── docs/                       # 文档
├── Dockerfile                  # Docker镜像
├── docker-compose.yml          # Docker编排
├── start_web.py               # 启动脚本（兼容）
├── start_crawler.py           # 爬虫脚本（兼容）
└── requirements.txt           # Python依赖
```

## 🚀 快速开始

### 方式1: 传统启动（向后兼容）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 数据库迁移（首次运行）
python backend/core/migrate_database.py

# 3. 启动Web服务
python start_web.py           # Flask: http://localhost:5000

# 或启动FastAPI
python -m uvicorn backend.api.fastapi_app:app --port 8000
                               # FastAPI: http://localhost:8000

# 4. 运行爬虫
python start_crawler.py
```

### 方式2: Docker启动（推荐）

```bash
# 1. 复制环境变量模板
cp .env.example .env
# 编辑 .env 填写必要配置（OpenAI API Key等）

# 2. 启动服务
docker-compose up -d api web

# 3. 访问
# Flask Web: http://localhost:5000
# FastAPI:   http://localhost:8000
# API文档:   http://localhost:8000/docs

# 4. 运行爬虫（一次性任务）
docker-compose --profile crawler run --rm crawler

# 5. 启动完整服务（包括Nginx）
docker-compose --profile nginx up -d
# Nginx: http://localhost:80
```

## 🔌 API端点（FastAPI v2.0）

### 图片管理
- `GET /api/images/pending` - 获取待处理图片（Mac本地拉取）
- `GET /api/images/processed` - 获取已处理图片（设计师审阅）
- `POST /api/images/batch-update-status` - 批量更新状态

### 标签数据
- `POST /api/tags/update` - 更新图片标签（Mac回传）
  ```json
  {
    "pin_id": "123456789",
    "aesthetic_score": 8.5,
    "fashion_tags": {
      "material": ["silk", "cotton"],
      "style": ["minimalist", "modern"],
      "cut": ["A-line"],
      "details": ["pleated", "asymmetric"]
    },
    "description": "A minimalist silk dress with asymmetric draping",
    "tags_list": ["dress", "silk", "minimalist"],
    "is_nsfw": false
  }
  ```

### 设计师反馈
- `POST /api/feedback` - 提交反馈（点赞/点踩）
  ```json
  {
    "pin_id": "123456789",
    "rating": 1  // -1讨厌, 0未看, 1喜欢
  }
  ```

### 统计信息
- `GET /api/stats` - 获取系统统计

## 🗄️ 数据库Schema（v2.0）

### images表
| 字段 | 类型 | 说明 |
|------|------|------|
| pin_id | TEXT | Pinterest ID（主键）|
| local_path | TEXT | 本地图片路径 |
| image_url | TEXT | 图片URL |
| source_keyword | TEXT | 来源关键词 |
| aesthetic_score | REAL | 审美评分（0-10）|
| fashion_tags | TEXT | 服装标签JSON |
| ai_description | TEXT | AI生成描述 |
| designer_rating | INTEGER | 设计师评分（-1/0/1）|
| process_status | INTEGER | 处理状态（0/1/2）|
| image_hash | TEXT | 图片哈希值 |
| original_metadata | TEXT | 原始元数据 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**process_status说明**:
- 0: 已抓取（待处理）
- 1: 已打标（待审阅）
- 2: 已归档（可用于训练）

### interactions表
记录用户交互行为（like/dislike/click等）

## 📊 完整工作流（基于update.md规划）

### 阶段1: 服务器端（云端）
1. **爬虫抓取** - Pinterest滚动爬取，存储元数据到数据库
2. **去重检查** - image_hash防止重复图片
3. **API服务** - 提供图片查询和数据回传接口

### 阶段2: Mac本地（处理中心）
1. **拉取图片** - 从API获取 `process_status=0` 的图片
2. **AI标注**:
   - ComfyUI + WD14-Tagger → 工业级标签
   - JoyCaption / Florence-2 → 自然语言描述
   - Aesthetic Predictor → 审美评分
3. **回传数据** - 更新标签、评分到服务器

### 阶段3: 设计师审阅（人工对齐）
1. **Web界面** - 展示 `aesthetic_score > 7` 且 `status=1` 的图片
2. **快速反馈** - 点赞✅ / 点踩❌
3. **数据积累** - 每次点击都是训练集的质量保证

### 阶段4: 训练集导出
1. **标签清洗** - 归类和标准化
2. **打包输出** - 图片 + `.txt` 描述文件
3. **黄金数据** - 可用于LoRA/Fine-tuning

## 🛠️ 维护命令

```bash
# 数据库迁移
python backend/core/migrate_database.py

# 清理项目（慎用）
python scripts/maintenance/cleanup_project.py

# 查看日志
tail -f data/logs/app.log

# Docker日志
docker-compose logs -f api
docker-compose logs -f web
```

## 📈 当前数据状态

- **数据库记录**: 1479 张图片
- **已下载图片**: 47 张
- **待处理图片**: 1432 张

## 🔄 从v1.0升级

v2.0 完全向后兼容，旧代码保留在根目录：

```bash
# 旧启动方式仍然有效
python app.py              # 仍然可用
python run_web.py          # 仍然可用

# 新启动方式
python start_web.py        # 推荐
python -m uvicorn backend.api.fastapi_app:app  # FastAPI
```

数据库自动升级，无需手动操作。如需回退：
```bash
git checkout <pre-refactor-commit>
```

## 📝 配置文件

### 环境变量（.env）
```bash
# 复制模板
cp .env.example .env

# 必填项
OPENAI_API_KEY=sk-...
PINTEREST_COOKIE=...
```

### 爬虫配置（config/）
- 关键词列表
- 滚动深度
- 代理设置

## 🎨 前端功能

- 瀑布流布局 + 无限滚动
- 图片预加载和懒加载
- 悬停快捷操作（Like/Dislike）
- 点击跳转Pinterest源
- 三层Dislike过滤机制

## 🔐 安全注意事项

- 不要提交 `.env` 文件到Git
- Pinterest Cookie定期更新
- API接口生产环境需添加认证
- 数据库定期备份

## 🚧 开发路线图

- [ ] Mac本地处理脚本（Pull-Process-Push）
- [ ] Streamlit设计师审阅界面
- [ ] 标签清洗和归类工具
- [ ] 训练集导出工具
- [ ] 图片哈希去重优化
- [ ] 批量下载待处理图片

## 📚 相关文档

- [update.md](update.md) - 完整规划方案
- [CHANGELOG.md](CHANGELOG.md) - 版本变更日志
- [docs/](docs/) - 详细文档

## 📄 许可证

MIT License

---

**技术栈**: Python • Flask • FastAPI • SQLite • Docker • Playwright • OpenAI API • ComfyUI
