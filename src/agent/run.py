import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from deepagents import create_deep_agent
import src.config as conf


agent = create_deep_agent(
    model=conf.GPT_54,
    system_prompt=conf.SYSTEM_PROMPT,
    backend=conf.BACKEND,
    skills=[conf.SKILL_DIR],
    tools=conf.AGENT_TOOLS,
)

if __name__ == "__main__":
    state = agent.invoke({"messages":"查一下我的仓位0x802f71cBf691D4623374E8ec37e32e26d5f74d87，我能开多一笔ETH的空单吗"})
    for m in state["messages"]:
        m.pretty_print()
