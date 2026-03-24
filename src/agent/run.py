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
)

if __name__ == "__main__":
    state = agent.invoke({"messages":"hello,秘密是什么？"})
    for m in state["messages"]:
        m.pretty_print()
