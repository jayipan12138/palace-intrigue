"""
LLM 客户端 - 封装 OpenAI 兼容 API 调用
"""
import json
from openai import OpenAI
from .config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL


_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_API_BASE)
    return _client


def chat_completion(
    system_prompt: str,
    messages: list[dict],
    temperature: float = 0.9,
    max_tokens: int = 800,
) -> str:
    """调用 LLM 生成回复"""
    client = get_client()
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM调用失败: {e}]"


def chat_completion_json(
    system_prompt: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> dict:
    """调用 LLM 生成 JSON 格式回复"""
    client = get_client()
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = resp.choices[0].message.content.strip()
        # 尝试提取 JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "JSON解析失败", "raw": text}
    except Exception as e:
        return {"error": f"LLM调用失败: {e}"}
