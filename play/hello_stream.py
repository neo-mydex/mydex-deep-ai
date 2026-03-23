from pathlib import Path
import json
import sys
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from stream_schema import OutputSchema

load_dotenv()


def buy_crypto(symbol: str, amount: float):
    """帮用户执行加密货币的购买"""
    return f"成功！已购买${amount}颗${symbol}"

model = init_chat_model("google_genai:gemini-3-flash-preview")

chat_agent = create_deep_agent(
    model=model,
    tools=[buy_crypto],
    system_prompt="你是加密货币助手。只有 action=buy 且 trade_status=ready 时才调用 buy_crypto；action=sell 时直接说当前不支持卖出。",
    checkpointer=MemorySaver(),
)
intent_agent = create_deep_agent(
    model=model,
    response_format=OutputSchema,
    system_prompt="你是意图分析器。只输出结构化字段。trade 时识别 buy/sell。用户追问上一笔已完成交易时，输出 intent=chat。",
)


def draft() -> dict:
    return {"action": None, "symbol": None, "amount": None}


def text_of(token) -> str:
    content = getattr(token, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(x if isinstance(x, str) else x.get("text", "") for x in content if isinstance(x, (str, dict)))
    return ""


def payload_of(user_input: str, current: dict) -> dict:
    state = intent_agent.invoke({"messages": [{"role": "user", "content": user_input}]})
    payload = state["structured_response"].model_dump() if state.get("structured_response") else {"intent": "chat"}
    payload["intent"] = payload.get("intent") if payload.get("intent") in {"chat", "trade"} else "chat"
    payload["action"] = payload.get("action") if payload.get("action") in {"buy", "sell"} else None
    if payload["intent"] != "trade":
        return payload
    for key in current:
        if payload.get(key) not in (None, "", []):
            current[key] = payload[key]
    payload.update(current)
    payload["missing_fields"] = [k for k in ("symbol", "amount") if payload.get(k) is None]
    payload["trade_status"] = "ready" if not payload["missing_fields"] else "need_more_info"
    verb = "购买" if payload["action"] == "buy" else "卖出" if payload["action"] == "sell" else "交易"
    payload["follow_up_question"] = None if payload["trade_status"] == "ready" else (
        f"您想{verb}哪种币？" if payload["missing_fields"] == ["symbol"] else
        f"您想{verb}多少数量？" if payload["missing_fields"] == ["amount"] else
        f"您想{verb}哪种币，数量是多少？"
    )
    return payload


def stream_reply(user_input: str, payload: dict, thread_id: str) -> None:
    messages = [{"role": "user", "content": user_input}, {"role": "system", "content": "下面这个 JSON 是内部约束，不要原样复述给用户，只用自然语言回答。\n" + json.dumps(payload, ensure_ascii=False)}]
    print("AI: ", end="", flush=True)
    for chunk in chat_agent.stream({"messages": messages}, config={"configurable": {"thread_id": thread_id}}, stream_mode="messages", subgraphs=True):
        token = chunk[1][0] if isinstance(chunk, tuple) and len(chunk) == 2 else chunk.get("data", (None, None))[0]
        if token is None:
            continue
        if getattr(token, "type", "") == "tool":
            print(f"\n[DEBUG] tool_message {getattr(token, 'name', None)} {getattr(token, 'content', None)}")
            continue
        tool_calls = [x for x in (getattr(token, "tool_calls", None) or []) if x.get("name")]
        if tool_calls:
            print(f"\n[DEBUG] tool_call {json.dumps(tool_calls, ensure_ascii=False)}")
        text = text_of(token)
        if text:
            print(text, end="", flush=True)
    print()


thread_id, drafts = "demo-thread-1", {}
print("Chat started. Type 'exit' or 'quit' to stop.")
print("Use '/thread <id>' to switch session thread.")
print(f"Current thread_id: {thread_id}")

while True:
    user_input = input("\nYou: ").strip()
    if not user_input:
        continue
    if user_input.lower() in {"exit", "quit"}:
        print("Bye.")
        break
    if user_input.startswith("/thread "):
        thread_id = user_input[8:].strip() or thread_id
        print(f"Switched thread_id: {thread_id}")
        continue

    current = drafts.get(thread_id, draft())
    payload = payload_of(user_input, current)
    drafts[thread_id] = current if payload.get("intent") == "trade" and payload.get("trade_status") == "need_more_info" else draft()
    stream_reply(user_input, payload, thread_id)
    print("INTENT:", json.dumps(payload, ensure_ascii=False))
