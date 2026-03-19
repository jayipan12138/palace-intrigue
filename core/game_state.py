"""
游戏状态管理
"""
from __future__ import annotations
import json
import random
from .config import CHARACTERS, RANDOM_EVENTS


class GameState:
    """管理整个宫斗游戏的状态"""

    def __init__(self):
        self.day = 0
        self.season = "春"
        self.agents: dict[str, "PalaceAgent"] = {}
        self.event_log: list[dict] = []
        self.current_event = None
        self.alliances: list[tuple[str, str]] = []  # 联盟关系
        self.enmities: list[tuple[str, str]] = []    # 敌对关系

    def init_agents(self):
        """初始化所有 Agent"""
        from .agent import PalaceAgent
        for agent_id in CHARACTERS:
            self.agents[agent_id] = PalaceAgent(agent_id, self)

    def advance_day(self):
        """推进一天"""
        self.day += 1
        seasons = ["春", "夏", "秋", "冬"]
        self.season = seasons[(self.day // 30) % 4]

    def get_random_event(self) -> dict:
        """获取一个随机事件"""
        event = random.choice(RANDOM_EVENTS)
        # 过滤掉不可用的参与者
        event = dict(event)
        event["participants"] = [
            p for p in event["participants"]
            if p in self.agents and self.agents[p].alive and not self.agents[p].in_cold_palace
        ]
        return event

    def apply_favor_change(self, agent_id: str, delta: int, reason: str):
        """改变恩宠值"""
        agent = self.agents.get(agent_id)
        if agent:
            old = agent.favor
            agent.favor = max(0, min(100, agent.favor + delta))
            self.log_event(f"{agent.name}恩宠{'增加' if delta > 0 else '减少'}{abs(delta)} ({old}->{agent.favor}): {reason}")

    def apply_influence_change(self, agent_id: str, delta: int, reason: str):
        """改变影响力"""
        agent = self.agents.get(agent_id)
        if agent:
            old = agent.influence
            agent.influence = max(0, min(100, agent.influence + delta))
            self.log_event(f"{agent.name}影响力{'增加' if delta > 0 else '减少'}{abs(delta)} ({old}->{agent.influence}): {reason}")

    def apply_health_change(self, agent_id: str, delta: int, reason: str):
        """改变健康值"""
        agent = self.agents.get(agent_id)
        if agent:
            old = agent.health
            agent.health = max(0, min(100, agent.health + delta))
            if agent.health <= 0:
                agent.alive = False
                self.log_event(f"💀 {agent.name}薨逝！原因：{reason}")
            else:
                self.log_event(f"{agent.name}健康{'恢复' if delta > 0 else '下降'}{abs(delta)} ({old}->{agent.health}): {reason}")

    def send_to_cold_palace(self, agent_id: str, reason: str):
        """打入冷宫"""
        agent = self.agents.get(agent_id)
        if agent:
            agent.in_cold_palace = True
            agent.favor = 0
            agent.influence = max(0, agent.influence - 30)
            self.log_event(f"⛓️ {agent.name}被打入冷宫！原因：{reason}")

    def log_event(self, message: str):
        """记录事件"""
        self.event_log.append({
            "day": self.day,
            "season": self.season,
            "message": message,
        })

    def get_status_summary(self) -> str:
        """获取当前状态摘要"""
        lines = [
            f"═══ 第{self.day}天 · {self.season}季 ═══",
            "",
            "【后宫众人状态】",
        ]
        concubines = ["empress", "consort_gui", "consort_shu", "consort_de", "consort_hua"]
        for aid in concubines:
            a = self.agents[aid]
            status = "❄️冷宫" if a.in_cold_palace else ("💀薨" if not a.alive else "正常")
            bar_favor = "█" * (a.favor // 10) + "░" * (10 - a.favor // 10)
            lines.append(f"  {a.name:12s}  恩宠[{bar_favor}]{a.favor:3d}  影响力{a.influence:3d}  健康{a.health:3d}  {status}")

        lines.append("")
        others = ["empress_dowager", "emperor", "eunuch"]
        for aid in others:
            a = self.agents[aid]
            lines.append(f"  {a.name:12s}  影响力{a.influence:3d}  健康{a.health:3d}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "day": self.day,
            "season": self.season,
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "event_log": self.event_log[-20:],
        }
