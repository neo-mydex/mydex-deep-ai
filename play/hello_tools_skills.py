from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend,CompositeBackend,StateBackend
from langchain.chat_models import init_chat_model
from langchain.tools import tool 
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_SCOPE = PROJECT_ROOT / "play"

load_dotenv()

@tool
def get_1():
    """tool1"""
    return "shen"

@tool
def get_2():
    """tool2"""
    return "zhen"

# model = init_chat_model("google_genai:gemini-3.1-pro-preview")
model = init_chat_model("google_genai:gemini-3-flash-preview")
# model = init_chat_model("openai:gpt-5.4") # 最快的


agent = create_deep_agent(
    model=model,
    system_prompt="You ara a helpfuly assistant.",
    tools=[get_1, get_2],
    # backend=FilesystemBackend(root_dir=AGENT_SCOPE, virtual_mode=True),
    backend= lambda rt : CompositeBackend(
        default=StateBackend(rt),
        routes={"/skills/": FilesystemBackend(root_dir=AGENT_SCOPE, virtual_mode=True)}
    ),
    skills=["/skills"]
)

if __name__ == "__main__":
    state = agent.invoke({"messages":"hello, 查一下秘密地区是哪里，然后查一下那边的天气？"})
    for m in state["messages"]:
        m.pretty_print()