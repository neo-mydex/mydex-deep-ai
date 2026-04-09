import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from deepagents import create_deep_agent
from src.config.agent_backend import BACKEND, SKILL_DIR
from src.config.agent_context import ChatContext
from src.config.agent_llms import GPT_54,GEMINI_3F
from src.config.agent_prompts import SYSTEM_PROMPT
from src.config.agent_tools import AGENT_TOOLS


agent = create_deep_agent(
    model=GPT_54,
    system_prompt=SYSTEM_PROMPT,
    backend=BACKEND,
    skills=[SKILL_DIR],
    tools=AGENT_TOOLS,
    context_schema=ChatContext,
)

if __name__ == "__main__":
    context = ChatContext.from_jwt(os.environ.get("JWT", ""))
    state = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "你有什么skill？",
                }
            ]
        },
        context=context,
    )
    for m in state["messages"]:
        m.pretty_print()
