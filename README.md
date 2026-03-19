# 三宫六院 · 宫斗模拟器

> AI Agent 驱动的后宫宫斗模拟 —— 每个角色都是独立的 AI Agent，所有剧情由 AI 与 AI 之间的真实对话驱动。

灵感来源：[edict（三省六部）](https://github.com/cft0808/edict)

## 特性

- **8 个独立 AI Agent** — 皇后、贵妃、淑妃、德妃、华妃、太后、皇帝、太监总管，各有独立人格（SOUL.md）
- **AI-to-AI 对话** — 角色之间的所有对话均由 LLM 实时生成，非硬编码
- **宫斗议政** — 交互式多 Agent 辩论，支持皇帝介入、颁旨、命运骰子
- **裁判系统** — 独立 AI 裁判根据角色表现判定恩宠/影响力变化
- **可视化看板** — Web Dashboard 展示角色状态、事件时间线、模拟控制
- **OpenClaw 集成** — 一键注册所有 Agent 到 OpenClaw，支持 subagent 调用
- **Docker 一键部署** — `docker compose up` 即可运行

## 快速开始

### 方式一：直接运行

```bash
# 1. 克隆项目
git clone https://github.com/jayipan12138/palace-intrigue.git
cd palace-intrigue

# 2. 安装依赖
pip install openai

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key（支持 OpenAI / DeepSeek / Qwen 等兼容 API）

# 4. 启动 Dashboard
python3 dashboard/server.py
# 访问 http://localhost:8080
```

### 方式二：Docker 部署

```bash
cp .env.example .env
# 编辑 .env 填入 API Key
docker compose up -d
# 访问 http://localhost:8080
```

### 方式三：OpenClaw 集成

```bash
# 需要先安装 OpenClaw
bash install.sh
# Agent 会自动注册到 OpenClaw，可通过 subagent 机制互相调用
```

### 命令行模式

```bash
# 模拟 5 天的宫斗
python3 main.py 5
```

## 架构

```
palace-intrigue/
├── agents/                     # 角色 SOUL 定义
│   ├── empress/SOUL.md         # 皇后·王氏
│   ├── consort_gui/SOUL.md     # 贵妃·苏氏
│   ├── consort_shu/SOUL.md     # 淑妃·陈氏
│   ├── consort_de/SOUL.md      # 德妃·林氏
│   ├── consort_hua/SOUL.md     # 华妃·赵氏
│   ├── empress_dowager/SOUL.md # 太后·李氏
│   ├── emperor/SOUL.md         # 皇帝·萧景琰
│   └── eunuch/SOUL.md          # 太监总管·李德福
├── core/                       # 核心引擎
│   ├── agent.py                # Agent 基类（记忆、对话、决策）
│   ├── config.py               # 角色配置、事件库、通信矩阵
│   ├── game_state.py           # 游戏状态管理
│   ├── llm_client.py           # LLM API 封装
│   └── orchestrator.py         # 编排器（驱动 AI-to-AI 交互）
├── dashboard/                  # Web Dashboard
│   ├── server.py               # HTTP API 服务
│   └── dashboard.html          # 前端界面
├── main.py                     # CLI 入口
├── install.sh                  # OpenClaw 一键安装脚本
├── Dockerfile                  # Docker 镜像
├── docker-compose.yml          # Docker Compose
└── .env.example                # 环境变量模板
```

## Dashboard 功能

| 面板 | 功能 |
|------|------|
| 人物看板 | 角色卡片 + 恩宠/影响力/健康进度条 + 阵营标签 |
| 宫斗议政 | 选择参与者开启辩论，支持皇帝发言/颁旨/命运骰子/散朝总结 |
| 事件簿 | 完整的宫斗大事记时间线 |
| 模拟推演 | 推进模拟 + 实时日志 |

## 每日模拟流程

1. **随机事件** — 从 10 种宫廷事件中触发（宫宴、流言、进贡、寿辰等）
2. **众人反应** — 每个参与者 Agent 独立生成反应
3. **交锋对话** — Agent 之间多轮真实对话
4. **裁判判定** — 独立 AI 裁判评估表现，判定属性变化
5. **暗中行动** — 妃嫔 Agent 自主决策夜间行动

## 角色一览

| 角色 | 性格特点 | 核心策略 |
|------|---------|---------|
| 皇后·王氏 | 城府极深，端庄大气 | 借刀杀人，以退为进 |
| 贵妃·苏氏 | 才貌双全，外柔内刚 | 以柔克刚，暗度陈仓 |
| 淑妃·陈氏 | 八面玲珑，长袖善舞 | 情报战，两头押注 |
| 德妃·林氏 | 外贤内狠，最善伪装 | 扮猪吃虎，坐山观虎斗 |
| 华妃·赵氏 | 将门虎女，直率火爆 | 正面冲突，以势压人 |
| 太后·李氏 | 老辣精明，看透人心 | 一锤定音，扶弱抑强 |
| 皇帝·萧景琰 | 英明多疑，优柔寡断 | 维持平衡，帝王心术 |
| 太监总管·李德福 | 圆滑世故，察言观色 | 信息贩卖，见风使舵 |

## LLM 兼容性

支持任何 OpenAI 兼容 API：

| 服务商 | LLM_API_BASE | LLM_MODEL |
|--------|-------------|-----------|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` |
| Ollama | `http://localhost:11434/v1` | `llama3` |

## License

MIT
