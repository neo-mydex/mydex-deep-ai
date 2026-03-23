from typing import Literal
from pydantic import BaseModel, Field, model_validator


class OutputSchema(BaseModel):
    """代理最终输出的结构"""

    intent: Literal["chat", "trade"] = Field(..., description="Intent type.")
    action: Literal["buy", "sell"] | None = Field(None, description="交易动作，仅 trade 场景使用")
    trade_status: Literal["ready", "need_more_info"] | None = Field(None, description="仅 trade 场景使用")
    symbol: str | None = Field(None, description="交易币种，例如 BTC")
    amount: float | None = Field(None, description="交易数量")
    missing_fields: list[Literal["symbol", "amount"]] = Field(default_factory=list, description="缺失字段列表")
    follow_up_question: str | None = Field(None, description="需要追问时的问题")

    @model_validator(mode="after")
    def _normalize(self) -> "OutputSchema":
        if self.intent == "chat":
            self.action = None
            self.trade_status = None
            self.symbol = None
            self.amount = None
            self.missing_fields = []
            self.follow_up_question = None
        return self
