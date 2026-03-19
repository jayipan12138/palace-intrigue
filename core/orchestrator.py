"""
编排器 - 驱动宫斗模拟的核心引擎
负责 Agent 之间的对话调度、事件处理、结果判定
"""
import json
import random
from .game_state import GameState
from .agent import PalaceAgent
from .llm_client import chat_completion_json, chat_completion
from .config import CHARACTERS


class Orchestrator:
    """宫斗编排器 - 每一轮驱动多个 Agent 进行交互"""

    def __init__(self, game_state: GameState):
        self.game = game_state
        self.round_log: list[str] = []

    def log(self, msg: str):
        self.round_log.append(msg)
        print(msg)

    def run_day(self) -> list[str]:
        """运行一天的宫斗模拟"""
        self.round_log = []
        self.game.advance_day()

        self.log(f"\n{'='*60}")
        self.log(f"  承平{self.game.day}年 · {self.game.season}季 · 第{self.game.day}天")
        self.log(f"{'='*60}")

        # 阶段1: 触发随机事件
        event = self.game.get_random_event()
        self.game.current_event = event
        self.log(f"\n📜 【{event['name']}】")
        self.log(f"   {event['description']}")
        self.log(f"   涉及: {', '.join(CHARACTERS[p]['name'] for p in event['participants'])}")

        # 阶段2: 参与者依次回应事件 (Agent-to-Agent 对话)
        self.log(f"\n{'─'*50}")
        self.log("  🎭 众人反应")
        self.log(f"{'─'*50}")
        responses = self._run_event_responses(event)

        # 阶段3: 多轮 Agent 对话交锋
        self.log(f"\n{'─'*50}")
        self.log("  ⚔️ 交锋对话")
        self.log(f"{'─'*50}")
        dialogues = self._run_confrontations(event, responses)

        # 阶段4: 裁判 Agent 判定结果
        self.log(f"\n{'─'*50}")
        self.log("  ⚖️ 局势判定")
        self.log(f"{'─'*50}")
        self._judge_outcomes(event, responses, dialogues)

        # 阶段5: 暗中行动 (Agent 自主决策)
        self.log(f"\n{'─'*50}")
        self.log("  🌙 暗中行动")
        self.log(f"{'─'*50}")
        self._run_secret_actions()

        # 显示状态
        self.log(f"\n{self.game.get_status_summary()}")

        # 记忆更新
        self._update_memories(event, responses)

        return self.round_log

    def _run_event_responses(self, event: dict) -> dict[str, str]:
        """每个参与者对事件做出反应 - 这是 Agent 独立思考"""
        responses = {}
        for pid in event["participants"]:
            agent = self.game.agents[pid]
            if not agent.alive or agent.in_cold_palace:
                continue

            situation = (
                f"事件：{event['name']}\n"
                f"详情：{event['description']}\n"
                f"在场的人有：{', '.join(CHARACTERS[p]['name'] for p in event['participants'] if p != pid)}\n"
                f"请以{agent.title}{agent.name.split('·')[1]}的身份做出反应，"
                f"包括你的言行和内心活动。"
            )
            response = agent.respond(situation)
            responses[pid] = response
            self.log(f"\n  【{agent.name}】")
            self.log(f"  {response}")

        return responses

    def _run_confrontations(self, event: dict, initial_responses: dict) -> list[dict]:
        """核心: Agent 之间的多轮对话交锋"""
        dialogues = []
        participants = [
            p for p in event["participants"]
            if p in self.game.agents
            and self.game.agents[p].alive
            and not self.game.agents[p].in_cold_palace
        ]

        if len(participants) < 2:
            return dialogues

        # 选择 1-2 组对话交锋
        num_confrontations = min(2, len(participants) // 2)
        shuffled = list(participants)
        random.shuffle(shuffled)

        for i in range(num_confrontations):
            if i * 2 + 1 >= len(shuffled):
                break

            agent_a = self.game.agents[shuffled[i * 2]]
            agent_b = self.game.agents[shuffled[i * 2 + 1]]

            self.log(f"\n  💬 {agent_a.name} ⇔ {agent_b.name}")
            dialogue = self._run_dialogue(agent_a, agent_b, event, initial_responses, max_rounds=2)
            dialogues.append({
                "agent_a": agent_a.agent_id,
                "agent_b": agent_b.agent_id,
                "exchanges": dialogue,
            })

        return dialogues

    def _run_dialogue(
        self,
        agent_a: PalaceAgent,
        agent_b: PalaceAgent,
        event: dict,
        context_responses: dict,
        max_rounds: int = 2,
    ) -> list[dict]:
        """两个 Agent 之间的多轮对话"""
        exchanges = []
        # 构建对话上下文
        context = (
            f"场景：{event['name']} - {event['description']}\n"
        )
        if agent_a.agent_id in context_responses:
            context += f"你之前的反应：{context_responses[agent_a.agent_id][:200]}\n"
        if agent_b.agent_id in context_responses:
            context += f"对方之前的反应：{context_responses[agent_b.agent_id][:200]}\n"

        conversation_history_a = []
        conversation_history_b = []

        for round_num in range(max_rounds):
            # Agent A 说话
            if round_num == 0:
                prompt_a = f"{context}\n你现在面对{agent_b.name}，请开口说话。注意体现你的性格和目的。"
            else:
                prompt_a = f"{agent_b.name}对你说: {last_b_response}\n请回应。"

            conversation_history_a.append({"role": "user", "content": prompt_a})
            response_a = agent_a.respond(
                context,
                messages=conversation_history_a,
            )
            conversation_history_a.append({"role": "assistant", "content": response_a})

            exchanges.append({"speaker": agent_a.agent_id, "content": response_a})
            self.log(f"    {agent_a.name}：{response_a}")

            # Agent B 回应
            prompt_b = f"{agent_a.name}对你说: {response_a}\n请回应。注意体现你的性格和目的。"
            if round_num == 0:
                prompt_b = f"{context}\n{prompt_b}"

            conversation_history_b.append({"role": "user", "content": prompt_b})
            response_b = agent_b.respond(
                context,
                messages=conversation_history_b,
            )
            conversation_history_b.append({"role": "assistant", "content": response_b})

            exchanges.append({"speaker": agent_b.agent_id, "content": response_b})
            self.log(f"    {agent_b.name}：{response_b}")

            last_b_response = response_b

        return exchanges

    def _judge_outcomes(self, event: dict, responses: dict, dialogues: list):
        """用一个裁判 AI 来判定本轮的结果"""
        summary = f"事件：{event['name']} - {event['description']}\n\n"
        summary += "各人反应：\n"
        for pid, resp in responses.items():
            name = CHARACTERS[pid]["name"]
            summary += f"- {name}: {resp[:150]}\n"

        summary += "\n对话交锋：\n"
        for d in dialogues:
            a_name = CHARACTERS[d["agent_a"]]["name"]
            b_name = CHARACTERS[d["agent_b"]]["name"]
            summary += f"\n{a_name} vs {b_name}:\n"
            for ex in d["exchanges"]:
                speaker = CHARACTERS[ex["speaker"]]["name"]
                summary += f"  {speaker}: {ex['content'][:100]}\n"

        judge_prompt = (
            "你是宫斗模拟的裁判系统。根据以下事件和各角色的表现，判定本轮结果。\n"
            "请客观评估每个参与者的表现，考虑他们的策略是否合理、话术是否高明。\n\n"
            f"{summary}\n\n"
            "请以JSON格式输出结果，格式如下：\n"
            '{\n'
            '  "winner": "本轮表现最好的角色ID",\n'
            '  "loser": "本轮表现最差的角色ID",\n'
            '  "changes": [\n'
            '    {"agent_id": "角色ID", "favor_delta": 数值, "influence_delta": 数值, "reason": "原因"}\n'
            '  ],\n'
            '  "narrative": "本轮叙事总结(50字以内)"\n'
            '}\n\n'
            f"可用的角色ID: {list(responses.keys())}\n"
            "favor_delta 和 influence_delta 范围: -15 到 +15\n"
        )

        result = chat_completion_json(
            "你是一个公正的宫斗裁判，负责根据角色表现判定胜负和属性变化。",
            [{"role": "user", "content": judge_prompt}],
            temperature=0.5,
        )

        if "error" not in result:
            self.log(f"\n  📋 裁判判定: {result.get('narrative', '无')}")
            changes = result.get("changes", [])
            for change in changes:
                aid = change.get("agent_id", "")
                if aid not in self.game.agents:
                    continue
                fd = change.get("favor_delta", 0)
                ind = change.get("influence_delta", 0)
                reason = change.get("reason", "")
                if fd != 0:
                    self.game.apply_favor_change(aid, fd, reason)
                if ind != 0:
                    self.game.apply_influence_change(aid, ind, reason)
        else:
            self.log(f"  ⚠️ 裁判判定失败: {result}")
            # 降级处理：随机小幅变化
            for pid in responses:
                if pid in ("emperor", "empress_dowager", "eunuch"):
                    continue
                delta = random.randint(-5, 5)
                self.game.apply_favor_change(pid, delta, "局势变化")

    def _run_secret_actions(self):
        """夜间暗中行动 - 每个妃嫔 Agent 自主决策一个秘密行动"""
        concubines = ["empress", "consort_gui", "consort_shu", "consort_de", "consort_hua"]
        actions = [
            "拉拢太监总管，打探消息",
            "向太后请安，争取支持",
            "暗中派人监视某位妃嫔",
            "给皇帝准备特别的礼物或饭菜",
            "与某位妃嫔密谈结盟",
            "休养生息，保存实力",
            "在皇帝面前说某位妃嫔的坏话",
            "安排宫人散布对自己有利的流言",
        ]

        # 随机选 1-2 个妃嫔执行暗中行动
        active = [c for c in concubines if self.game.agents[c].alive and not self.game.agents[c].in_cold_palace]
        if not active:
            return
        actors = random.sample(active, min(2, len(active)))

        for aid in actors:
            agent = self.game.agents[aid]
            situation = (
                f"夜深了，你回到{agent.residence}，回想今天发生的事。"
                f"你决定暗中采取一些行动来巩固自己的地位。"
            )
            decision = agent.decide_action(situation, actions)

            if "error" not in decision:
                action = decision.get("action", "休养生息")
                dialogue = decision.get("dialogue", "")
                reason = decision.get("reason", "")
                self.log(f"\n  🌙 {agent.name}暗中行动: {action}")
                if dialogue:
                    self.log(f'     "{dialogue}"')
                if reason:
                    self.log(f"     (内心: {reason})")

                # 简单的行动效果
                self._apply_secret_action_effect(aid, action, decision)
            else:
                self.log(f"\n  🌙 {agent.name}: 安静度过了夜晚。")

    def _apply_secret_action_effect(self, agent_id: str, action: str, decision: dict):
        """应用暗中行动的效果"""
        if "太监" in action or "打探" in action:
            self.game.apply_influence_change(agent_id, random.randint(1, 3), "打探消息")
        elif "太后" in action:
            self.game.apply_influence_change(agent_id, random.randint(1, 4), "讨好太后")
        elif "监视" in action:
            self.game.apply_influence_change(agent_id, random.randint(0, 2), "暗中监视")
        elif "皇帝" in action or "礼物" in action:
            self.game.apply_favor_change(agent_id, random.randint(1, 5), "讨好皇帝")
        elif "结盟" in action:
            self.game.apply_influence_change(agent_id, random.randint(2, 4), "暗中结盟")
        elif "休养" in action:
            self.game.apply_health_change(agent_id, random.randint(1, 3), "休养生息")
        elif "坏话" in action:
            self.game.apply_favor_change(agent_id, random.randint(-2, 3), "说坏话风险")
        elif "流言" in action:
            self.game.apply_influence_change(agent_id, random.randint(-1, 3), "散布流言")

    def _update_memories(self, event: dict, responses: dict):
        """更新所有参与者的记忆"""
        event_summary = f"{event['name']}: {event['description'][:50]}"
        for pid in event["participants"]:
            if pid in self.game.agents:
                agent = self.game.agents[pid]
                agent.add_memory(self.game.day, event_summary)
                if pid in responses:
                    agent.add_memory(self.game.day, f"我的反应: {responses[pid][:80]}")
