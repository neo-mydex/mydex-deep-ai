from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver  


agent = create_deep_agent(
    model="google_genai:gemini-3-flash-preview"
)