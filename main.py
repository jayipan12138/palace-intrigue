#!/usr/bin/env python3
"""
三宫六院 · 宫斗模拟器
Palace Intrigue Simulator

每个角色都是一个独立的 AI Agent，通过 AI 之间的对话驱动剧情发展。
"""
import sys
import json
import os

sys.path.insert(0, os.path.dirname(__file__))

from core.game_state import GameState
from core.orchestrator import Orchestrator


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║          三 宫 六 院 · 宫 斗 模 拟 器                   ║
║          Palace Intrigue Simulator v1.0                  ║
║                                                          ║
║   每个角色都是独立的 AI Agent                            ║
║   AI 与 AI 之间的对话驱动剧情                           ║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║   👑 皇帝·萧景琰    🏛️ 太后·李氏    🔑 太监总管·李德福  ║
║   👸 皇后·王氏      💃 贵妃·苏氏    🎭 淑妃·陈氏        ║
║   🌸 德妃·林氏      ⚔️ 华妃·赵氏                        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


def run_simulation(num_days: int = 3) -> dict:
    """运行宫斗模拟"""
    print_banner()

    # 初始化游戏
    game = GameState()
    game.init_agents()
    orchestrator = Orchestrator(game)

    print(game.get_status_summary())
    print()

    all_logs = []

    for day in range(num_days):
        print(f"\n{'▓'*60}")
        print(f"  正在模拟第 {day + 1}/{num_days} 天...")
        print(f"{'▓'*60}")

        day_log = orchestrator.run_day()
        all_logs.extend(day_log)

        # 检查是否有人出局
        active = [
            a for a in game.agents.values()
            if a.alive and not a.in_cold_palace
            and a.agent_id not in ("emperor", "empress_dowager", "eunuch")
        ]
        if len(active) <= 1:
            print("\n🏆 宫斗结束！只剩一位妃嫔屹立不倒！")
            if active:
                print(f"   最终赢家: {active[0].name}")
            break

    # 最终报告
    print(f"\n{'═'*60}")
    print("  📊 最终局势报告")
    print(f"{'═'*60}")
    print(game.get_status_summary())

    # 生成结局叙事
    print(f"\n{'─'*50}")
    print("  📖 结局")
    print(f"{'─'*50}")
    _generate_ending(game)

    return game.to_dict()


def _generate_ending(game: GameState):
    """用 AI 生成结局叙事"""
    from core.llm_client import chat_completion

    status = []
    concubines = ["empress", "consort_gui", "consort_shu", "consort_de", "consort_hua"]
    for cid in concubines:
        a = game.agents[cid]
        s = "在冷宫中" if a.in_cold_palace else ("已薨" if not a.alive else f"恩宠{a.favor}/影响力{a.influence}")
        status.append(f"- {a.name}: {s}")

    recent_events = "\n".join(e["message"] for e in game.event_log[-10:])

    prompt = (
        f"这是一个宫斗模拟的结局场景。经过{game.day}天的明争暗斗：\n\n"
        f"{''.join(status)}\n\n"
        f"近期大事：\n{recent_events}\n\n"
        f"请用200字以内写一段精彩的结局叙事，描述后宫最终的格局。"
        f"语气要有古风韵味。"
    )
    ending = chat_completion(
        "你是一位宫廷小说作家，擅长用优美的古风文笔描述后宫故事。",
        [{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    print(f"\n{ending}")


if __name__ == "__main__":
    num_days = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    result = run_simulation(num_days)

    # 保存结果
    output_path = os.path.join(os.path.dirname(__file__), "data", "result.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存至 {output_path}")
