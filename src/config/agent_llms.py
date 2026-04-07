from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# openai
GPT_54=init_chat_model(model="openai:gpt-5.4")
GPT_4=init_chat_model(model="openai:gpt-4o")

GEMINI_3P = init_chat_model("google_genai:gemini-3.1-pro-preview")
GEMINI_3F = init_chat_model("google_genai:gemini-3-flash-preview")

if __name__ == "__main__":
    print("ENV_PATH =", ENV_PATH)
    # answer = GEMINI_3F.invoke("hi")
    # print(answer.content[0]["text"]) # Hello! How can I help you today?

    answer = GPT_54.invoke("hi")
    print(answer.content)
