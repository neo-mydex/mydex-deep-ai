"""示例：如何在 Agent 中共享 context（用户信息）和 state（意图历史）"""
from datetime import datetime
from typing import Annotated, Literal

from deepagents import create_deep_agent
from langchain.agents import AgentState
from langchain.agents.middleware import before_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


# ========================
# 1. Context: 用户静态信息
# ========================
class UserContext(BaseModel):
    user_id: str
    jwt: str


# ========================
# 2. Intent 结果模型
# ========================
class IntentResult(BaseModel):
    """LLM 意图分类结果"""
    category: Literal["chitchat", "analyze", "perps-trade", "unknown"]
    action: str | None = None
    target: list[str] | None = None
    reasoning: str | None = None


# ========================
# 3. 自定义 Reducer: 追加意图
# ========================
def append_intent(left: list, right) -> list:
    """追加意图列表"""
    if not left:
        left = []
    if not right:
        return left
    if isinstance(right, list):
        return left + right
    return left + [right]


# ========================
# 4. State 扩展: 意图历史
# ========================
class AgentStateWithIntent(AgentState):
    """扩展 AgentState，添加 intent_history"""
    intent_history: Annotated[list[dict], append_intent] = []


# ========================
# 5. LLM 分类函数
# ========================
def classify_with_llm(message: str) -> dict:
    """使用 LLM 对消息进行意图分类"""
    from langchain.chat_models import init_chat_model

    classifier = init_chat_model("openai:gpt-4o-mini").with_structured_output(IntentResult)

    prompt = f"""分析以下用户消息，返回意图分类：

消息：{message}

分类要求：
- category: chitchat(闲聊) | analyze(分析/咨询) | perps-trade(永续合约交易) | unknown(未知)
- action: 具体动作，如 open_long, close_position, set_stop_loss, analysis_request, casual_chat
- target: 交易标的，如 BTC, ETH 等
- reasoning: 分类理由"""

    result = classifier.invoke(prompt)

    return {
        "timestamp": datetime.now().isoformat(),
        "raw_message": message,
        "category": result.category,
        "action": result.action,
        "target": result.target,
        "reasoning": result.reasoning,
    }


# ========================
# 6. Middleware: 自动用 LLM 记录用户意图（装饰器方式）
# ========================
@before_agent(state_schema=AgentStateWithIntent)
def record_user_intent(state: AgentStateWithIntent, runtime) -> dict | None:
    """在 agent 执行前，用 LLM 提取并记录用户意图"""
    # 获取最新的用户消息
    human_messages = [
        m for m in state["messages"]
        if isinstance(m, HumanMessage)
    ]

    if not human_messages:
        return None

    latest_user_msg = human_messages[-1]
    content = latest_user_msg.content

    # 如果最后一条消息已经记录过（避免重复），则跳过
    existing_history = state.get("intent_history", [])
    if existing_history and existing_history[-1].get("raw_message") == content:
        return None

    # 用 LLM 分类意图
    intent = classify_with_llm(content)
    return {"intent_history": [intent]}


# ========================
# 7. Tools
# ========================
@tool
def get_user_info(runtime: ToolRuntime) -> str:
    """获取当前用户的信息

    Returns:
        用户 ID 和 JWT 信息
    """
    context = runtime.context
    user_id = context.get("user_id", "未登录") if context else "未登录"
    jwt = context.get("jwt", "未设置") if context else "未设置"
    return f"用户ID: {user_id}\nJWT: {jwt[:20]}..." if len(jwt) > 20 else f"用户ID: {user_id}\nJWT: {jwt}"


@tool
def get_intent_history(runtime: ToolRuntime) -> str:
    """获取用户的意图历史记录

    Returns:
        格式化的意图历史列表
    """
    state = runtime.state
    history = state.get("intent_history", [])
    if not history:
        return "暂无意图历史记录"

    lines = []
    for item in history:
        category = item.get("category", "unknown")
        action = item.get("action", "-")
        targets = ", ".join(item.get("target", [])) if item.get("target") else "-"
        ts = item.get("timestamp", "")[11:19]
        lines.append(f"[{ts}] {category:12} | {action:20} | 标的: {targets}")
    return "\n".join(lines)


# ========================
# 8. 创建 Agent
# ========================
agent = create_deep_agent(
    model="openai:gpt-5.4",
    tools=[get_user_info, get_intent_history],
    middleware=[record_user_intent],
    system_prompt="你是一个说话简短的AI交易助手，人狠话不多"
)


# ========================
# 9. 测试
# ========================
if __name__ == "__main__":
    from utils import format_messages

    print("=== 第一轮对话 ===")
    result1 = agent.invoke(
        {
            "messages": [{"role": "user", "content": "我想开一个用1U 开25x的 BTC 多单"}],
            "intent_history": [],
        },
        config={"context": UserContext(user_id="user_123", jwt="eyJhbGciOiJIUzI1NiJ9...")},
    )
    format_messages(result1["messages"])
    print(f"\n意图历史:")
    for h in result1.get("intent_history", []):
        ts = h.get("timestamp", "")[:19]
        print(f"  - [{ts}] 分类: {h.get('category'):12} | 动作: {h.get('action'):20} | 标的: {', '.join(h.get('target', []) or ['-'])}")

    print("\n=== 第二轮对话 ===")
    result2 = agent.invoke(
        {
            "messages": [{"role": "user", "content": "平掉我的仓"}],
            "intent_history": result1.get("intent_history", []),
        },
        config={"context": UserContext(user_id="user_123", jwt="eyJhbGciOiJIUzI1NiJ9...")},
    )
    format_messages(result2["messages"])
    print(f"\n意图历史:")
    for h in result2.get("intent_history", []):
        ts = h.get("timestamp", "")[:19]
        print(f"  - [{ts}] 分类: {h.get('category'):12} | 动作: {h.get('action'):20} | 标的: {', '.join(h.get('target', []) or ['-'])}")

    print("\n=== 第三轮对话（闲聊）===")
    result3 = agent.invoke(
        {
            "messages": [{"role": "user", "content": "你好啊"}],
            "intent_history": result2.get("intent_history", []),
        },
        config={"context": UserContext(user_id="user_123", jwt="eyJhbGciOiJIUzI1NiJ9...")},
    )
    format_messages(result3["messages"])
    print(f"\n意图历史:")
    for h in result3.get("intent_history", []):
        ts = h.get("timestamp", "")[:19]
        print(f"  - [{ts}] 分类: {h.get('category'):12} | 动作: {h.get('action'):20} | 标的: {', '.join(h.get('target', []) or ['-'])}")
