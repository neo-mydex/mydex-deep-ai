import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from deepagents import create_deep_agent
import src.config as conf


agent = create_deep_agent(
    model=conf.GPT_54,                   # 使用的LLM
    system_prompt=conf.SYSTEM_PROMPT,    # 系统提示词
    backend=conf.BACKEND,                # 后端，skill要用
    skills=[conf.SKILL_DIR],             # skill在后端的位置
    tools=conf.AGENT_TOOLS,              # 可用工具
    context_schema=conf.ChatContext,     # 运行时上下文（用户身份等）
)

if __name__ == "__main__":
    state = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "查一下BTC价格",
                }
            ]
        },
        context=conf.ChatContext(
            context="用户钱包地址: 0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
            # jwt="<privy_jwt_here>",  # 登录场景可传
        ),
    )
    for m in state["messages"]:
        m.pretty_print()
