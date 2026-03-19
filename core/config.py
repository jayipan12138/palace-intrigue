"""
三宫六院 - 宫斗模拟器
Palace Intrigue Simulator - AI Agent-based Imperial Harem Drama

核心配置文件
"""
import os

# LLM API 配置
LLM_API_BASE = os.environ.get("LLM_API_BASE", "https://api.mulerun.com/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", os.environ.get("MULEROUTER_API_KEY", ""))
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4.1-mini")

# Agent 配置
AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")

# 角色定义
CHARACTERS = {
    "empress": {
        "name": "皇后·王氏",
        "title": "皇后",
        "residence": "坤宁宫",
        "initial_favor": 70,
        "initial_influence": 85,
        "initial_health": 90,
        "faction": "中宫派",
    },
    "consort_gui": {
        "name": "贵妃·苏氏",
        "title": "贵妃",
        "residence": "翊坤宫",
        "initial_favor": 90,
        "initial_influence": 70,
        "initial_health": 95,
        "faction": "苏派",
    },
    "consort_shu": {
        "name": "淑妃·陈氏",
        "title": "淑妃",
        "residence": "钟粹宫",
        "initial_favor": 55,
        "initial_influence": 65,
        "initial_health": 85,
        "faction": "中立",
    },
    "consort_de": {
        "name": "德妃·林氏",
        "title": "德妃",
        "residence": "永和宫",
        "initial_favor": 60,
        "initial_influence": 60,
        "initial_health": 88,
        "faction": "太后派",
    },
    "consort_hua": {
        "name": "华妃·赵氏",
        "title": "华妃",
        "residence": "咸福宫",
        "initial_favor": 65,
        "initial_influence": 75,
        "initial_health": 92,
        "faction": "将门派",
    },
    "empress_dowager": {
        "name": "太后·李氏",
        "title": "太后",
        "residence": "慈宁宫",
        "initial_favor": 0,  # 太后不参与争宠
        "initial_influence": 95,
        "initial_health": 70,
        "faction": "太后派",
    },
    "emperor": {
        "name": "皇帝·萧景琰",
        "title": "皇帝",
        "residence": "乾清宫",
        "initial_favor": 0,
        "initial_influence": 100,
        "initial_health": 85,
        "faction": "皇权",
    },
    "eunuch": {
        "name": "太监总管·李德福",
        "title": "太监总管",
        "residence": "内廷",
        "initial_favor": 0,
        "initial_influence": 50,
        "initial_health": 80,
        "faction": "中立",
    },
}

# 随机事件库
RANDOM_EVENTS = [
    {
        "id": "imperial_banquet",
        "name": "宫廷夜宴",
        "description": "皇帝在御花园设宴，所有妃嫔必须出席。席间众人即兴赋诗，暗流涌动。",
        "participants": ["empress", "consort_gui", "consort_shu", "consort_de", "consort_hua", "emperor"],
        "type": "social",
    },
    {
        "id": "tribute_gift",
        "name": "番邦进贡",
        "description": "西域番邦进贡了一匣子稀世珠宝，皇帝要赏赐后宫。分配珠宝引发了一场暗战。",
        "participants": ["empress", "consort_gui", "consort_hua", "emperor"],
        "type": "resource",
    },
    {
        "id": "palace_rumor",
        "name": "宫闱流言",
        "description": "后宫突然流传一则流言：有人在贵妃的汤药中做了手脚。各方反应不一。",
        "participants": ["consort_gui", "empress", "consort_shu", "eunuch"],
        "type": "crisis",
    },
    {
        "id": "dowager_birthday",
        "name": "太后寿辰",
        "description": "太后寿辰将至，各宫妃嫔争相准备寿礼讨好太后，一场孝心大战拉开帷幕。",
        "participants": ["empress_dowager", "empress", "consort_gui", "consort_de", "consort_hua"],
        "type": "social",
    },
    {
        "id": "prince_study",
        "name": "皇子课业",
        "description": "太傅上奏皇子们的课业表现，各母妃为自己的孩子暗中角力。",
        "participants": ["empress", "consort_gui", "consort_de", "emperor"],
        "type": "political",
    },
    {
        "id": "maid_caught",
        "name": "宫女密报",
        "description": "一名宫女被发现在深夜潜入翊坤宫附近，供出是受人指使来窥探。幕后主使成谜。",
        "participants": ["consort_gui", "empress", "consort_shu", "eunuch"],
        "type": "crisis",
    },
    {
        "id": "flower_viewing",
        "name": "春日赏花",
        "description": "御花园牡丹盛开，皇帝邀妃嫔赏花。看似风雅的聚会暗藏争宠心机。",
        "participants": ["emperor", "consort_gui", "consort_hua", "consort_de", "empress"],
        "type": "social",
    },
    {
        "id": "medicine_incident",
        "name": "安胎药疑云",
        "description": "某位妃嫔传出有孕的消息，但安胎药方却被人调换。后宫人人自危。",
        "participants": ["consort_shu", "empress", "consort_gui", "eunuch", "empress_dowager"],
        "type": "crisis",
    },
    {
        "id": "general_victory",
        "name": "边关大捷",
        "description": "华妃之父赵大将军边关大捷的消息传入宫中，华妃气焰大涨，众妃嫔态度各异。",
        "participants": ["consort_hua", "empress", "consort_gui", "emperor", "empress_dowager"],
        "type": "political",
    },
    {
        "id": "cold_palace_threat",
        "name": "冷宫之影",
        "description": "皇帝震怒，暗示要将某位妃嫔打入冷宫。后宫众人或落井下石，或暗中营救。",
        "participants": ["emperor", "empress", "consort_gui", "consort_de", "eunuch"],
        "type": "crisis",
    },
]

# 通信权限矩阵 - 定义谁可以主动与谁对话
COMM_MATRIX = {
    "empress": ["consort_gui", "consort_shu", "consort_de", "consort_hua", "emperor", "empress_dowager", "eunuch"],
    "consort_gui": ["empress", "consort_shu", "consort_de", "consort_hua", "emperor", "eunuch"],
    "consort_shu": ["empress", "consort_gui", "consort_de", "consort_hua", "eunuch"],
    "consort_de": ["empress", "consort_gui", "consort_shu", "consort_hua", "empress_dowager", "eunuch"],
    "consort_hua": ["empress", "consort_gui", "consort_shu", "consort_de", "emperor", "eunuch"],
    "empress_dowager": ["empress", "consort_gui", "consort_shu", "consort_de", "consort_hua", "emperor", "eunuch"],
    "emperor": ["empress", "consort_gui", "consort_shu", "consort_de", "consort_hua", "empress_dowager", "eunuch"],
    "eunuch": ["empress", "consort_gui", "consort_shu", "consort_de", "consort_hua", "emperor", "empress_dowager"],
}
