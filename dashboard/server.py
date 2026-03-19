#!/usr/bin/env python3
"""
三宫六院 · 宫斗模拟器 - 服务端
提供 REST API + 静态前端服务
"""
import json
import os
import sys
import threading
import time
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.game_state import GameState
from core.orchestrator import Orchestrator
from core.agent import PalaceAgent
from core.llm_client import chat_completion, chat_completion_json
from core.config import CHARACTERS, RANDOM_EVENTS

# ─── 全局状态 ───
game = GameState()
game.init_agents()
orchestrator = Orchestrator(game)
simulation_running = False
simulation_log: list[str] = []

# ─── 宫斗议政 会话管理 ───
discuss_sessions: dict[str, dict] = {}


def create_discuss_session(topic: str, participant_ids: list[str]) -> dict:
    sid = str(uuid.uuid4())[:8]
    session = {
        "id": sid,
        "topic": topic,
        "participants": participant_ids,
        "messages": [],
        "round": 0,
        "status": "active",
        "created_at": time.time(),
    }
    # 开场白
    session["messages"].append({
        "type": "system",
        "content": f"宫斗议政开始。议题：{topic}",
        "timestamp": time.time(),
    })
    discuss_sessions[sid] = session
    return session


def advance_discuss(sid: str, emperor_msg: str = "", decree: str = "") -> dict:
    session = discuss_sessions.get(sid)
    if not session or session["status"] != "active":
        return {"error": "会话不存在或已结束"}

    session["round"] += 1
    new_messages = []

    # 如果皇帝有话说
    if emperor_msg:
        new_messages.append({
            "type": "emperor",
            "speaker": "皇帝",
            "content": emperor_msg,
            "timestamp": time.time(),
        })

    # 如果有天命/圣旨
    if decree:
        new_messages.append({
            "type": "decree",
            "content": decree,
            "timestamp": time.time(),
        })

    # 构建上下文
    history = "\n".join(
        f"[{m.get('speaker', '系统')}]: {m['content']}"
        for m in session["messages"][-10:]
    )
    context_extra = ""
    if emperor_msg:
        context_extra += f"\n皇帝刚才说：{emperor_msg}"
    if decree:
        context_extra += f"\n天降圣旨：{decree}"

    # 每个参与者依次发言
    for pid in session["participants"]:
        agent = game.agents.get(pid)
        if not agent or not agent.alive or agent.in_cold_palace:
            continue

        prompt = (
            f"这是一场宫斗议政，议题是：{session['topic']}\n\n"
            f"之前的对话：\n{history}\n{context_extra}\n\n"
            f"现在轮到你发言。请以你的身份和性格，对议题发表看法或回应他人。"
            f"注意：你可能会支持、反对、暗中使坏、拉拢盟友，一切取决于你的目标。"
            f"控制在80字以内，要有戏剧张力。"
        )

        response = agent.respond(prompt)

        # 用 AI 判断情绪
        emotion = _detect_emotion(response)

        msg = {
            "type": "official",
            "speaker": agent.name,
            "speaker_id": pid,
            "content": response,
            "emotion": emotion,
            "round": session["round"],
            "timestamp": time.time(),
        }
        new_messages.append(msg)
        history += f"\n[{agent.name}]: {response}"

    session["messages"].extend(new_messages)
    return {"messages": new_messages, "round": session["round"]}


def conclude_discuss(sid: str) -> dict:
    session = discuss_sessions.get(sid)
    if not session:
        return {"error": "会话不存在"}

    session["status"] = "concluded"

    history = "\n".join(
        f"[{m.get('speaker', '系统')}]: {m['content']}"
        for m in session["messages"]
        if m["type"] in ("official", "emperor", "decree")
    )

    summary = chat_completion(
        "你是宫廷史官，擅长用精炼的文言文总结宫斗议政的结果。",
        [{"role": "user", "content":
            f"请总结这场宫斗议政的结果，议题是：{session['topic']}\n\n"
            f"对话记录：\n{history}\n\n"
            f"用100字以内总结胜负、各方表现、以及对后宫格局的影响。"
        }],
        max_tokens=300,
    )

    session["messages"].append({
        "type": "system",
        "content": f"【散朝总结】{summary}",
        "timestamp": time.time(),
    })
    return {"summary": summary}


def _detect_emotion(text: str) -> str:
    emotions = {
        "怒": "angry", "恨": "angry", "岂有此理": "angry", "放肆": "angry",
        "哭": "sad", "泪": "sad", "伤心": "sad",
        "笑": "amused", "哈": "amused", "有趣": "amused",
        "忧": "worried", "担心": "worried", "不妙": "worried",
        "哼": "confident", "本宫": "confident", "本妃": "confident",
    }
    for keyword, emotion in emotions.items():
        if keyword in text:
            return emotion
    return "thinking"


# ─── 命运骰子 ───
FATE_EVENTS = [
    "八百里加急！边关战报传来，华妃之兄战死沙场！",
    "御医密报：某位妃嫔的安胎药中被人掺了麝香！",
    "太后突然召见所有妃嫔，宣布要亲自考核德行！",
    "皇帝微服出宫被发现，竟在民间有一知己！",
    "宫中失火，翊坤宫珍宝尽毁，贵妃痛哭！",
    "西域进贡了一面照妖镜，据说能照出人心中的秘密！",
    "一名老宫女临终前留下血书，揭露十年前的宫中惨案！",
    "钦天监奏报：天象异变，主后宫有大变！",
    "皇帝突然宣布要立太子，后宫炸开了锅！",
    "一位已故妃嫔的贴身丫鬟突然现身，手握惊天秘密！",
]


def run_simulation_day():
    """在后台运行一天的模拟"""
    global simulation_running, simulation_log
    simulation_running = True
    simulation_log = []
    try:
        logs = orchestrator.run_day()
        simulation_log = logs
    finally:
        simulation_running = False


# ─── HTTP 服务 ───
class PalaceHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 安静模式

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self._json_response(game.to_dict())
        elif path == "/api/characters":
            chars = {}
            for aid, agent in game.agents.items():
                chars[aid] = agent.to_dict()
            self._json_response(chars)
        elif path == "/api/events":
            self._json_response({"events": game.event_log[-50:]})
        elif path == "/api/simulation-status":
            self._json_response({
                "running": simulation_running,
                "day": game.day,
                "log_lines": len(simulation_log),
            })
        elif path == "/api/simulation-log":
            self._json_response({"log": simulation_log})
        elif path == "/api/discuss/list":
            sessions = [
                {"id": s["id"], "topic": s["topic"], "status": s["status"], "round": s["round"]}
                for s in discuss_sessions.values()
            ]
            self._json_response({"sessions": sessions})
        elif path.startswith("/api/discuss/get/"):
            sid = path.split("/")[-1]
            session = discuss_sessions.get(sid)
            if session:
                self._json_response(session)
            else:
                self._json_response({"error": "not found"}, 404)
        elif path == "/api/fate-dice":
            import random
            event = random.choice(FATE_EVENTS)
            self._json_response({"event": event})
        elif path == "/api/random-events":
            self._json_response({"events": RANDOM_EVENTS})
        elif path == "/" or path == "/index.html":
            self._serve_dashboard()
        else:
            self._json_response({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/api/simulate-day":
            if simulation_running:
                self._json_response({"error": "模拟正在进行中"}, 400)
                return
            thread = threading.Thread(target=run_simulation_day, daemon=True)
            thread.start()
            self._json_response({"ok": True, "message": "开始模拟新的一天"})

        elif path == "/api/discuss/start":
            topic = body.get("topic", "后宫权力分配")
            participants = body.get("participants", ["empress", "consort_gui", "consort_de", "consort_hua"])
            session = create_discuss_session(topic, participants)
            self._json_response(session)

        elif path == "/api/discuss/advance":
            sid = body.get("session_id", "")
            emperor_msg = body.get("emperor_message", "")
            decree = body.get("decree", "")
            result = advance_discuss(sid, emperor_msg, decree)
            self._json_response(result)

        elif path == "/api/discuss/conclude":
            sid = body.get("session_id", "")
            result = conclude_discuss(sid)
            self._json_response(result)

        elif path == "/api/discuss/fate":
            sid = body.get("session_id", "")
            import random
            fate = random.choice(FATE_EVENTS)
            result = advance_discuss(sid, decree=fate)
            self._json_response({"fate": fate, **result})

        else:
            self._json_response({"error": "not found"}, 404)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except Exception:
            return {}

    def _json_response(self, data: dict, code: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _serve_dashboard(self):
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
        if os.path.exists(dashboard_path):
            with open(dashboard_path, "r", encoding="utf-8") as f:
                content = f.read().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self._json_response({"error": "dashboard.html not found"}, 404)


def main():
    port = int(os.environ.get("PORT", 6891))
    server = HTTPServer(("0.0.0.0", port), PalaceHandler)
    print(f"三宫六院 · 总控台 已启动: http://localhost:{port}")
    print(f"按 Ctrl+C 退出")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
