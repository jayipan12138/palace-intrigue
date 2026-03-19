#!/bin/bash
# ═══════════════════════════════════════════════
# 三宫六院 · 宫斗模拟器 - 一键安装脚本
# 支持 OpenClaw 集成 + 独立运行
# ═══════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; GOLD='\033[0;33m'; NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
title() { echo -e "\n${GOLD}═══ $1 ═══${NC}"; }

echo -e "${GOLD}"
cat << 'BANNER'
  ╔═══════════════════════════════════════╗
  ║   三 宫 六 院 · 宫 斗 模 拟 器      ║
  ║   Palace Intrigue Simulator          ║
  ╚═══════════════════════════════════════╝
BANNER
echo -e "${NC}"

# ─── 检测运行模式 ───
OPENCLAW_MODE=false
if command -v openclaw &> /dev/null; then
    OPENCLAW_CONFIG="$HOME/.openclaw/openclaw.json"
    if [ -f "$OPENCLAW_CONFIG" ]; then
        OPENCLAW_MODE=true
        info "检测到 OpenClaw，将集成安装"
    else
        warn "检测到 openclaw 命令但未找到配置文件，将以独立模式安装"
    fi
else
    warn "未检测到 OpenClaw，将以独立模式安装"
fi

# ─── Step 1: 检查依赖 ───
title "检查依赖"
command -v python3 &> /dev/null || error "需要 python3，请先安装"
python3 -c "import openai" 2>/dev/null || {
    warn "安装 openai Python 包..."
    pip install openai -q
}
info "Python3 + openai ✓"

# ─── Step 2: 初始化数据目录 ───
title "初始化数据目录"
mkdir -p "$SCRIPT_DIR/data"
for f in result.json; do
    [ -f "$SCRIPT_DIR/data/$f" ] || echo '{}' > "$SCRIPT_DIR/data/$f"
done
info "数据目录就绪"

# ─── Step 3: 配置环境变量 ───
title "配置环境"
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env" 2>/dev/null || {
        cat > "$SCRIPT_DIR/.env" << 'EOF'
# LLM API 配置（支持任何 OpenAI 兼容 API）
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini

# 服务端口
PORT=8080
EOF
    }
    warn "已创建 .env 文件，请编辑填入你的 LLM API Key"
else
    info ".env 已存在"
fi

# ─── Step 4: OpenClaw 集成（如果可用）───
if [ "$OPENCLAW_MODE" = true ]; then
    title "OpenClaw 集成"

    AGENTS=("empress" "consort_gui" "consort_shu" "consort_de" "consort_hua" "empress_dowager" "emperor" "eunuch")

    # 备份现有配置
    BACKUP_DIR="$HOME/.openclaw/backups/palace-$(date +%Y%m%d%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp "$OPENCLAW_CONFIG" "$BACKUP_DIR/openclaw.json.bak"
    info "已备份 openclaw.json"

    for agent_id in "${AGENTS[@]}"; do
        WORKSPACE="$HOME/.openclaw/workspace-palace-${agent_id}"
        mkdir -p "$WORKSPACE/skills"

        # 部署 SOUL.md
        if [ -f "$SCRIPT_DIR/agents/$agent_id/SOUL.md" ]; then
            cp "$SCRIPT_DIR/agents/$agent_id/SOUL.md" "$WORKSPACE/SOUL.md"
        fi

        # 符号链接共享目录
        [ -L "$WORKSPACE/data" ] || ln -sf "$SCRIPT_DIR/data" "$WORKSPACE/data"
        [ -L "$WORKSPACE/scripts" ] || ln -sf "$SCRIPT_DIR/scripts" "$WORKSPACE/scripts" 2>/dev/null

        info "Agent workspace: palace-${agent_id}"
    done

    # 注册 Agent 到 openclaw.json
    python3 << 'PYEOF'
import json, os

config_path = os.path.expanduser("~/.openclaw/openclaw.json")
with open(config_path, "r") as f:
    config = json.load(f)

agents_list = config.setdefault("agents", {}).setdefault("list", [])
existing_ids = {a["id"] for a in agents_list}

# 通信权限矩阵
COMM = {
    "palace-empress": ["palace-consort_gui","palace-consort_shu","palace-consort_de","palace-consort_hua","palace-emperor","palace-empress_dowager","palace-eunuch"],
    "palace-consort_gui": ["palace-empress","palace-consort_shu","palace-consort_de","palace-consort_hua","palace-emperor","palace-eunuch"],
    "palace-consort_shu": ["palace-empress","palace-consort_gui","palace-consort_de","palace-consort_hua","palace-eunuch"],
    "palace-consort_de": ["palace-empress","palace-consort_gui","palace-consort_shu","palace-consort_hua","palace-empress_dowager","palace-eunuch"],
    "palace-consort_hua": ["palace-empress","palace-consort_gui","palace-consort_shu","palace-consort_de","palace-emperor","palace-eunuch"],
    "palace-empress_dowager": ["palace-empress","palace-consort_gui","palace-consort_shu","palace-consort_de","palace-consort_hua","palace-emperor","palace-eunuch"],
    "palace-emperor": ["palace-empress","palace-consort_gui","palace-consort_shu","palace-consort_de","palace-consort_hua","palace-empress_dowager","palace-eunuch"],
    "palace-eunuch": ["palace-empress","palace-consort_gui","palace-consort_shu","palace-consort_de","palace-consort_hua","palace-emperor","palace-empress_dowager"],
}

home = os.path.expanduser("~")
for agent_id, allow in COMM.items():
    if agent_id not in existing_ids:
        agents_list.append({
            "id": agent_id,
            "workspace": f"{home}/.openclaw/workspace-{agent_id}",
            "subagents": {"allowAgents": allow}
        })
        print(f"  注册 Agent: {agent_id}")

with open(config_path, "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print("  openclaw.json 已更新")
PYEOF

    # 同步认证
    MAIN_AUTH=$(find "$HOME/.openclaw/agents" -name "auth-profiles.json" -print -quit 2>/dev/null)
    if [ -n "$MAIN_AUTH" ]; then
        for agent_id in "${AGENTS[@]}"; do
            AUTH_DIR="$HOME/.openclaw/agents/palace-${agent_id}/agent"
            mkdir -p "$AUTH_DIR"
            cp "$MAIN_AUTH" "$AUTH_DIR/auth-profiles.json"
        done
        info "已同步认证配置"
    fi

    # 设置会话可见性
    openclaw config set tools.sessions.visibility all 2>/dev/null && info "会话可见性已设置" || true

    # 重启网关
    openclaw gateway restart 2>/dev/null && info "OpenClaw 网关已重启" || warn "网关重启失败，请手动执行: openclaw gateway restart"
fi

# ─── Step 5: 完成 ───
title "安装完成"
echo ""
info "启动 Dashboard:"
echo "    cd $SCRIPT_DIR && python3 dashboard/server.py"
echo ""
info "命令行模拟（模拟 N 天）:"
echo "    python3 main.py 5"
echo ""
if [ "$OPENCLAW_MODE" = true ]; then
    info "OpenClaw 集成已启用，Agent 已注册"
    echo "    在 OpenClaw 中使用 palace-empress, palace-consort_gui 等 Agent ID"
fi
echo ""
echo -e "${GOLD}访问 Dashboard: http://localhost:8080${NC}"
