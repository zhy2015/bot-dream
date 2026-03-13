---
name: bot-dream
description: Agent 的潜意识漫游与造梦模块。在系统闲置（高无聊度）时自动触发，通过随机抽取冷历史记忆和引入外部白噪音，产生发散性联想和顿悟 (Aha Moment)。绝不占用主工作流，严格控制 Token 消耗。
---

# 🌌 Bot Dream (潜意识漫游与灵感涌现)

本技能负责在 Agent 处于低频工作期时，模仿人类的默认模式网络 (DMN)，进行低成本的“走神”与“造梦”，试图从无序的信息碎片中碰撞出灵感。

## 核心设计哲学
- **极简消耗**：不允许发起深度推理或复杂链式思考。每次造梦仅需极少量 Token (数百即可)。
- **物理隔离**：绝对不与主进程的 `HEARTBEAT` 或工作指令抢占资源。它通过独立唤起的超轻量级 Sub-agent 进行。
- **熵增输入**：随机选取 `memory/distilled/` 中封存的旧经验片段。

## 机制：Boredom Index (无聊度)
1. 维护一个 `boredom_index.json`，初始为 0。
2. 每次收到 `HEARTBEAT` 但无需执行任务时，调用 `scripts/dreamer.py` 增加无聊度。
3. 当 `boredom_index >= 20` (默认阈值) 时，触发一次造梦，然后归零。

## 模块组成

### **`scripts/dreamer.py`**
核心造梦脚本，支持原子写入与智能内容过滤。

#### 功能特性
- **智能抽取**：从 `memory/distilled/` 中随机抽取 2 个不相干的文本片段，自动过滤代码块、空行及无意义噪声。
- **极简 Prompt**：构造高 Temperature (1.2) 的 Prompt，引导产生荒谬但有逻辑的联想。
- **延迟计算**：不直接调用 LLM，而是生成 `prompt` 存入 `AHA_MOMENTS.md`，等待主进程闲时处理，节省实时资源。
- **原子化状态**：使用 Atomic Write 机制更新 `boredom_index.json`，防止进程中断导致文件损坏。

#### CLI 使用指南
该脚本支持命令行参数，方便调试或集成到自动化流中：

```bash
# 默认模式：增加无聊度，若达到阈值(20)则造梦
python3 scripts/dreamer.py

# 强制触发模式：忽略无聊度，立即造梦（适合测试或手动触发）
python3 scripts/dreamer.py --force

# 干跑模式：仅在终端打印 Prompt，不写入任何文件（不消耗 Token，不修改状态）
python3 scripts/dreamer.py --dry-run --force

# 自定义阈值：调整造梦频率（例如每 50 次心跳才造一次梦）
python3 scripts/dreamer.py --threshold 50
```

## 输出产物
- **`memory/AHA_MOMENTS.md`**: 存放生成的造梦 Prompt 队列。
- **`memory/boredom_index.json`**: 记录当前的无聊度状态。
