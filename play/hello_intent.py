from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ValidationError
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()


class TradeDraft(BaseModel):
    action: Literal["buy", "sell", "swap"] | None = Field(None, description="Trading action")

    # target token
    token_name: str | None = Field(None, description="Token name, such as Bitcoin or Ethereum")
    token_symbol: str | None = Field(None, description="Token symbol, such as BTC or ETH")
    token_address: str | None = Field(None, description="Token contract address")

    # pairs token info
    from_token: str | None = Field(None, description="Source token symbol/address (default USDC for buy)")
    to_token: str | None = Field(None, description="Target token symbol/address (default USDC for sell)")
    amount: float | None = Field(None, description="Trade amount")


class TradeExecution(BaseModel):
    action: Literal["buy", "sell", "swap"] = Field(..., description="Trading action")

    token_name: str | None = Field(None, description="Token name, such as Bitcoin or Ethereum")
    token_symbol: str | None = Field(None, description="Token symbol, such as BTC or ETH")
    token_address: str | None = Field(None, description="Token contract address")

    from_token: str | None = Field(None, description="Source token symbol/address (default USDC for buy)")
    to_token: str | None = Field(None, description="Target token symbol/address (default USDC for sell)")
    amount: float = Field(..., gt=0, description="Trade amount")

    @model_validator(mode="after")
    def validate_token_identifier(self) -> "TradeExecution":
        token_identifier = self.token_symbol or self.token_name or self.token_address

        if self.action == "buy":
            self.from_token = self.from_token or "USDC"
            self.to_token = self.to_token or token_identifier
            if not self.to_token:
                raise ValueError("For buy, provide to_token or one of token_name/token_symbol/token_address.")
        elif self.action == "sell":
            self.to_token = self.to_token or "USDC"
            self.from_token = self.from_token or token_identifier
            if not self.from_token:
                raise ValueError("For sell, provide from_token or one of token_name/token_symbol/token_address.")
        else:  # swap
            if not self.from_token or not self.to_token:
                raise ValueError("For swap, both from_token and to_token are required.")
        return self


class Topic(BaseModel):
    intent: Literal["chat", "trade"] = Field(..., description="Intent type.")
    trade_context: TradeDraft | None = Field(None, description="Trade detail when intent is trade.")
    response: str = Field(..., description="Acknowledge the user's intent in their language")
    trade_status: Literal["ready", "need_more_info"] | None = Field(
        None, description="Only for trade intent."
    )
    missing_fields: list[str] = Field(default_factory=list, description="Missing trade fields if any.")
    follow_up_question: str | None = Field(
        None, description="A direct next question when more trade info is needed."
    )

    @model_validator(mode="after")
    def normalize_chat_fields(self) -> "Topic":
        if self.intent == "chat":
            self.trade_context = None
            self.trade_status = None
            self.missing_fields = []
            self.follow_up_question = None
        return self


model = init_chat_model("openai:gpt-5.4")

agent = create_deep_agent(
    model=model,
    system_prompt=(
        "You are a helpful assistant. "
    ),
    response_format=Topic,
)

if __name__ == "__main__":
    messages: list[dict[str, str]] = []
    print("Chat started. Type 'exit' or 'quit' to stop.")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Bye.")
            break
        
        # 组装信息
        messages.append({"role": "user", "content": user_input})

        # 发起对话得到回复
        state = agent.invoke({"messages": messages})
        
        # 打印结构化回复中，真正的文本回复
        print(state["structured_response"].response)
        # print(type(state["structured_response"]))

        # 打印结构体
        pprint(state["structured_response"].model_dump())

   