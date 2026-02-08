---

# 🍏 FashionXG Mac 本地处理端：ComfyUI 自动化实施方案

## 第一阶段：ComfyUI 环境准备 (Mac 本地)

**目标**：在 Mac 上跑通 ComfyUI 并安装必要的服装标注插件。

1.  **安装 ComfyUI**：
    *   指令 Claude Code 检查本地是否已有 ComfyUI 目录，若无则克隆并安装依赖。
2.  **安装核心自定义节点 (Custom Nodes)**：
    *   `ComfyUI-WD14-Tagger`: 用于提取工业级标签。
    *   `ComfyUI-JoyCaption` 或 `ComfyUI-Florence2`: 用于生成高质量服装描述。
    *   `ComfyUI-Logic`: 用于在工作流中加入基础逻辑判断。
3.  **启动 API 模式**：
    *   确认 ComfyUI 运行在 `http://127.0.0.1:8188`。

## 第二阶段：导出 API 工作流 (Workflow Design)

**目标**：在 ComfyUI 界面上搭建好标注流水线，并导出为 API 可用的 JSON。

1.  **手动搭建工作流**：
    *   `Load Image` -> `WD14 Tagger` -> `Florence2` -> `Aesthetic Score`。
2.  **导出 JSON**：
    *   在 ComfyUI 设置中开启 "Enable Dev mode"。
    *   点击 "Save (API Format)"，保存为 `fashion_tagger_api.json`。
    *   **指令 Claude Code**：读取这个 JSON 文件，将其作为请求模板。

## 第三阶段：编写“桥接脚本” (The Comfy-Bridge)

**目标**：让 Python 脚本充当“指挥官”，协调云端服务器和本地 ComfyUI。

1.  **指令 Claude Code 编写 `comfy_bridge.py`**：
    *   **逻辑流程**：
        1.  从云端 API 获取待处理图片 URL。
        2.  将图片发送至 ComfyUI 的 `/prompt` 接口。
        3.  通过 WebSocket 监听 ComfyUI 任务状态。
        4.  任务完成后，解析 ComfyUI 返回的 JSON（提取 Tags、Caption、Score）。
2.  **加入“逻辑过滤” (Logic Filtering)**：
    *   在回传给云端之前，在 Python 脚本中执行我们之前讨论的逻辑：
        *   *检查黑名单标签*：如果 WD14 返回了 `text` 或 `meme`，直接标记为废弃。
        *   *向量比对*：计算当前图与“喜欢”图的相似度。

## 第四阶段：实施“点赞/点踩”逻辑对齐

**目标**：利用你那几十个反馈数据，在 ComfyUI 处理前后进行干预。

1.  **预处理过滤**：
    *   指令 Claude Code 编写逻辑：在把图片塞给 ComfyUI 之前，先算简单的 CLIP 相似度。
    *   如果与“点踩”图高度相似，直接跳过，**不浪费 Mac 的 GPU 算力跑 ComfyUI**。
2.  **后处理加权**：
    *   ComfyUI 返回分数后，结合设计师的偏好进行加分或减分。

---

### 💡 给 Claude Code 的具体执行指令（你可以直接复制）：

> "Claude，我现在要实施 FashionXG 的本地处理端。请按以下步骤操作：
>
> 1.  **环境检查**：检查本地 `~/ComfyUI` 目录。如果不存在，请指导我安装。
> 2.  **编写桥接脚本**：创建一个 `comfy_bridge.py`。
>     *   它需要从 `http://your-server:8000/api/images/pending` 拉取任务。
>     *   使用 WebSocket 连接本地 ComfyUI (`127.0.0.1:8188`)。
>     *   将图片传入我提供的 `fashion_tagger_api.json` 工作流。
> 3.  **加入逻辑过滤**：
>     *   读取本地 `data/feedback/likes.pt`（如果有）。
>     *   如果 ComfyUI 返回的标签包含 'text' 或 'watermark'，将 `process_status` 设为 -1。
>     *   如果审美分 > 7 且与‘喜欢’的向量相似度 > 0.8，优先回传并标记为 `high_quality`。
> 4.  **自动化**：脚本处理完一批后，自动删除本地临时图片并休眠 5 分钟。"

---

### 为什么在 Mac 上用 ComfyUI + Claude Code 是绝配？

1.  **可视化调试**：如果 AI 标注得不对，你直接打开 ComfyUI 网页就能改节点，不需要改代码。
2.  **利用 MPS 加速**：ComfyUI 对 Mac M 芯片的优化非常好，跑 Florence-2 非常快。
3.  **解耦**：你的 Python 脚本只负责“传话”和“逻辑判断”，繁重的 AI 推理全部交给专业的 ComfyUI。

**你需要先做的一件事**：
去 ComfyUI 里把那套标注工作流（WD14 + Florence2 + 评分）搭好，导出那个 **API 格式的 JSON** 给 Claude Code，它就能立刻帮你把剩下的自动化逻辑写完。

没问题，我们把 **Aesthetic Score (审美评分)** 深度集成进 ComfyUI，并实现你要求的 **“相似度 + 标签特征”双重逻辑筛选**。

这种方案能解决单一维度的误判。例如：一张图视觉上很像你喜欢的（相似度高），但标签显示它是“街拍”而你想要“白底图”（标签不符），逻辑过滤就会自动调低它的优先级。

---

# 🍏 FashionXG Mac 本地端：ComfyUI + 复合逻辑筛选方案

## 第一阶段：ComfyUI 工作流配置 (Workflow)

你需要确保你的 ComfyUI 包含以下三个核心节点，并导出为 **API JSON**：

1.  **WD14 Tagger**: 负责提取 `silk`, `pleated`, `minimalist` 等标签。
2.  **Florence-2**: 负责生成自然语言描述。
3.  **Aesthetic Predictor**: 负责打分（通常使用 `ComfyUI-Aesthetic-Score` 节点，加载 `sac+logos+ava1-l14-linear.pth` 权重）。

**Claude Code 指令**：
> "Claude，请检查我的 `workflow_api.json`。确保它能接收一个图片路径作为输入，并输出：1. WD14 的标签列表；2. Florence-2 的描述；3. Aesthetic Score 的分值。"

---

## 第二阶段：核心逻辑——“相似度 + 标签”双重筛选器

这是你最关心的部分。我们在 `comfy_bridge.py` 中实现一个 **评分加权引擎**。

### 筛选逻辑设计：
*   **基础分** = ComfyUI 返回的 `Aesthetic Score`。
*   **相似度加成** = 计算当前图与“喜欢仓库”的 CLIP 向量距离。
*   **标签加成/扣分** = 检查 WD14 标签是否命中你的“核心设计元素”。

### 逻辑示例：
> 如果（相似度 > 0.8 **且** 标签包含 "silk"） -> **极高优先级**
> 如果（相似度 > 0.8 **但** 标签包含 "street"） -> **中优先级（视觉对但场景错）**
> 如果（标签包含 "watermark" 或 "text"） -> **直接剔除**

---

## 第三阶段：Claude Code 实施步骤规划

你可以按顺序给 Claude Code 下达这些指令：

### 1. 建立特征数据库
> "Claude，请编写一个脚本 `update_preference_lib.py`。它需要从服务器拉取所有 `designer_rating = 1`（喜欢）和 `-1`（讨厌）的图片，提取它们的 **CLIP 向量** 和 **WD14 标签频率**，保存到本地 `preference_profile.json` 中。"

### 2. 编写复合筛选函数
> "在 `comfy_bridge.py` 中实现 `calculate_final_priority` 函数：
> - **输入**：ComfyUI 返回的 tags, score 和当前图片的 vector。
> - **逻辑**：
>   1. **硬过滤**：若 tags 命中黑名单（如 text, blurry），返回优先级 0。
>   2. **标签匹配**：计算 tags 与‘喜欢’标签集的重合度（例如：我喜欢的图里 80% 都有 'high_heels'）。
>   3. **视觉匹配**：计算与‘喜欢’向量的最高相似度。
>   4. **综合得分** = `score * 0.4 + similarity * 0.4 + tag_match * 0.2`。
> - **输出**：最终优先级分数。"

### 3. 自动化流水线
> "请完善 `comfy_bridge.py` 的主循环：
> 1. 从 API 获取待处理图片。
> 2. 传给 ComfyUI 运行工作流。
> 3. 运行上面的复合筛选函数。
> 4. 将所有数据（含 Tags, Caption, Score, Final_Priority）回传给服务器。
> 5. 如果 `Final_Priority` 极高，触发一个系统通知告诉我发现了‘黄金数据’。"

---

## 为什么这种“复合筛选”比单纯相似度好？

| 维度 | 优点 | 缺点 | 复合后的弥补 |
| :--- | :--- | :--- | :--- |
| **Aesthetic Score** | 过滤掉画质烂的图 | 无法分辨风格（它可能觉得一张烂俗婚纱照很高分） | 靠**相似度**拉回你的审美偏好 |
| **CLIP 相似度** | 把握整体视觉“氛围” | 无法识别细节（它分不清真丝和化纤） | 靠**WD14 标签**精准识别材质 |
| **WD14 标签** | 识别具体设计元素 | 没有美感概念 | 靠**Aesthetic Score**保证质量 |

## 下一步行动建议：

1.  **在 ComfyUI 里跑通一张图**：确认 WD14、Florence-2 和 Aesthetic 节点都能正常出结果。
2.  **导出 API JSON**：这是 Claude Code 工作的基础。
3.  **运行 `update_preference_lib.py`**：让你那几十个“点击/喜欢”数据变成可衡量的 JSON 档案。
4.  **让 Claude Code 写 Bridge 脚本**：把 ComfyUI 变成一个全自动的后台标注机器。

**注意：** 既然你只有几十个数据，建议在标签筛选逻辑中，给 **“讨厌的标签”** 更高的权重（即：只要出现我讨厌的元素，不管多美都降权），这样能最快速度净化你的数据集。