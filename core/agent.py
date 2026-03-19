"""
Agent 基类 - 每个宫斗角色都是一个 Agent
"""
import os
from .config import AGENTS_DIR, CHARACTERS
from .llm_client import chat_completion, chat_completion_json


class PalaceAgent:
    """宫斗角色 Agent"""

    def __init__(self, agent_id: str, game_state: "GameState"):
        self.agent_id = agent_id
        self.game_state = game_state
        self.config = CHARACTERS[agent_id]
        self.name = self.config["name"]
        self.title = self.config["title"]
        self.residence = self.config["residence"]

        # 动态属性
        self.favor = self.config["initial_favor"]
        self.influence = self.config["initial_influence"]
        self.health = self.config["initial_health"]
        self.faction = self.config["faction"]
        self.alive = True
        self.in_cold_palace = False

        # 对话记忆 (最近的记忆)
        self.memory: list[dict] = []
        self.max_memory = 20

        # 加载 SOUL.md
        self.soul = self._load_soul()

    def _load_soul(self) -> str:
        soul_path = os.path.join(AGENTS_DIR, self.agent_id, "SOUL.md")
        if os.path.exists(soul_path):
            with open(soul_path, "r", encoding="utf-8") as f:
                return f.read()
        return f"你是{self.name}，{self.title}。"

    def _build_system_prompt(self, context: str = "") -> str:
        """构建系统提示词，包含角色设定和当前状态"""
        status = (
            f"\n\n## 当前状态\n"
            f"- 恩宠值: {self.favor}/100\n"
            f"- 影响力: {self.influence}/100\n"
            f"- 健康值: {self.health}/100\n"
            f"- 所属阵营: {self.faction}\n"
            f"- 居所: {self.residence}\n"
        )
        relationships = self._build_relationship_context()
        memory_ctx = self._build_memory_context()

        prompt = self.soul + status + relationships + memory_ctx

        if context:
            prompt += f"\n\n## 当前情境\n{context}"

        prompt += (
            "\n\n## 回复要求\n"
            "- 完全沉浸在角色中，用符合身份的语气说话\n"
            "- 回复控制在100-200字以内\n"
            "- 每次回复中要体现你的性格和目的\n"
            "- 可以有内心独白（用括号标注），但主要是对话\n"
            "- 你的行动和话语应该符合你的目标和当前局势\n"
        )
        return prompt

    def _build_relationship_context(self) -> str:
        """构建当前关系网络的上下文"""
        lines = ["\n\n## 后宫众人现状"]
        for cid, char in CHARACTERS.items():
            if cid == self.agent_id:
                continue
            agent = self.game_state.agents.get(cid)
            if agent and agent.alive:
                status = "在冷宫中" if agent.in_cold_palace else f"恩宠{agent.favor}"
                lines.append(f"- {char['name']}({char['title']}): {status}, 影响力{agent.influence}")
        return "\n".join(lines)

    def _build_memory_context(self) -> str:
        """构建记忆上下文"""
        if not self.memory:
            return ""
        lines = ["\n\n## 近期记忆"]
        for mem in self.memory[-10:]:
            lines.append(f"- [{mem['day']}] {mem['summary']}")
        return "\n".join(lines)

    def add_memory(self, day: int, summary: str):
        """添加记忆"""
        self.memory.append({"day": day, "summary": summary})
        if len(self.memory) > self.max_memory:
            self.memory = self.memory[-self.max_memory:]

    def respond(self, situation: str, messages: list[dict] = None) -> str:
        """作为 Agent 对情境做出回应"""
        if not self.alive or self.in_cold_palace:
            return f"（{self.name}无法回应）"
        system_prompt = self._build_system_prompt(situation)
        if messages is None:
            messages = [{"role": "user", "content": situation}]
        return chat_completion(system_prompt, messages)

    def decide_action(self, situation: str, available_actions: list[str]) -> dict:
        """Agent 自主决策下一步行动"""
        if not self.alive or self.in_cold_palace:
            return {"action": "none", "reason": "无法行动"}

        action_list = "\n".join(f"{i+1}. {a}" for i, a in enumerate(available_actions))
        system_prompt = self._build_system_prompt(situation)
        prompt = (
            f"当前局势：{situation}\n\n"
            f"你可以选择的行动：\n{action_list}\n\n"
            f"请以JSON格式回复你的决策：\n"
            f'{{"action": "选择的行动", "target": "目标人物(如有)", '
            f'"reason": "你的理由(角色内心独白)", "dialogue": "你说的话"}}'
        )
        return chat_completion_json(
            system_prompt,
            [{"role": "user", "content": prompt}],
        )

    def converse(self, other_agent: "PalaceAgent", topic: str, initiator: bool = True) -> str:
        """与另一个 Agent 进行对话"""
        if initiator:
            context = f"你主动找{other_agent.name}谈话。话题是：{topic}"
        else:
            context = f"{other_agent.name}来找你谈话。话题是：{topic}"
        return self.respond(context)

    def to_dict(self) -> dict:
        return {
            "id": self.agent_id,
            "name": self.name,
            "title": self.title,
            "favor": self.favor,
            "influence": self.influence,
            "health": self.health,
            "faction": self.faction,
            "alive": self.alive,
            "in_cold_palace": self.in_cold_palace,
            "residence": self.residence,
        }
