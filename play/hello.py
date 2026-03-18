from dotenv import load_dotenv
from deepagents import create_deep_agent
from pprint import pprint


load_dotenv()

agent = create_deep_agent(
    model="openai:gpt-5.4",
    system_prompt="You ara a helpfuly assistant."
)

if __name__ == "__main__":
    state = agent.invoke({"messages":"hello"})
    pprint(state["messages"][-1].content)
    """
[{'annotations': [],
  'id': 'msg_010be81c6579fd610069b7fd92304c819f811e039d92aaecb0',
  'text': 'Hello.',
  'type': 'text'}]
    """
