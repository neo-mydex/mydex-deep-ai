from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.tools import tool 
load_dotenv()

PROJECT_ROOT='./src/play'

@tool
def get_1():
    """tool1"""
    return "shen"

@tool
def get_2():
    """tool2"""
    return "zhen"

# model = init_chat_model("google_genai:gemini-3.1-pro-preview")
# model = init_chat_model("google_genai:gemini-3-flash-preview")
model = init_chat_model("openai:gpt-5.4") # 最快的

agent = create_deep_agent(
    model=model,
    system_prompt="You ara a helpfuly assistant.",
    tools=[get_1, get_2],
    backend=FilesystemBackend(root_dir=PROJECT_ROOT, virtual_mode=True),
    skills=["/skills"],
)

if __name__ == "__main__":
    state = agent.invoke({"messages":"hello, 秘密是什么？"})
    for m in state["messages"]:
        m.pretty_print()