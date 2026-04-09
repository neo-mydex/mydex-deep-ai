"""
止盈止损 Confirm 模块 (SET_TPSL)

按 hyperliquid交易卡片需求文档.md 5.7 实现

Key constraints:
- tpPrice 和 tpRatio 互斥，二选一
- slPrice 和 slRatio 互斥，二选一
- existingTpOid = 0 表示第一次设置，非0表示更新已有订单
- existingSlOid = 0 表示第一次设置，非0表示更新已有订单
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Literal


# =============================================================================
# Pydantic 类
# =============================================================================

class SetTpslAction(BaseModel):
    """confirm_perp_set_tpsl 返回"""
    action: Literal["SET_TPSL"]
    execution_plan: list[dict]
    meta: dict


class ConfirmSetTpslInput(BaseModel):
    """confirm_perp_set_tpsl 输入参数与校验"""
    coin: str
    position_size: float = Field(gt=0)
    tp_price: float | None = Field(default=None, gt=0)
    tp_ratio: float | None = Field(default=None, gt=0, le=1)
    sl_price: float | None = Field(default=None, gt=0)
    sl_ratio: float | None = Field(default=None, gt=0, le=1)
    existing_tp_oid: int = Field(default=0, ge=0)
    existing_sl_oid: int = Field(default=0, ge=0)
    source_text: str = ""

    @model_validator(mode="after")
    def validate_semantics(self) -> "ConfirmSetTpslInput":
        if self.tp_price is not None and self.tp_ratio is not None:
            raise ValueError("tp_price 和 tp_ratio 二选一，不可同时指定")
        if self.sl_price is not None and self.sl_ratio is not None:
            raise ValueError("sl_price 和 sl_ratio 二选一，不可同时指定")

        has_tp = self.tp_price is not None or self.tp_ratio is not None or self.existing_tp_oid > 0
        has_sl = self.sl_price is not None or self.sl_ratio is not None or self.existing_sl_oid > 0
        if not has_tp and not has_sl:
            raise ValueError("至少需要提供止盈参数或止损参数之一")
        return self


# =============================================================================
# impl 纯函数
# =============================================================================

def _str(v: float | None) -> str | None:
    """转字符串，去除无意义的 .0"""
    if v is None:
        return None
    s = str(v)
    return s[:-2] if s.endswith(".0") else s


def confirm_perp_set_tpsl_impl(
    coin: str,
    position_size: float,
    tp_price: float | None = None,
    tp_ratio: float | None = None,
    sl_price: float | None = None,
    sl_ratio: float | None = None,
    existing_tp_oid: int = 0,
    existing_sl_oid: int = 0,
    source_text: str = "",
) -> dict:
    """设置止盈止损卡片（SET_TPSL）。用于"BTC 仓位止盈 72000，止损 66500"类意图。"""
    try:
        payload = ConfirmSetTpslInput(
            coin=coin,
            position_size=position_size,
            tp_price=tp_price,
            tp_ratio=tp_ratio,
            sl_price=sl_price,
            sl_ratio=sl_ratio,
            existing_tp_oid=existing_tp_oid,
            existing_sl_oid=existing_sl_oid,
            source_text=source_text,
        )
    except ValidationError as e:
        raise ValueError(str(e)) from e

    item_dict = {
        "intent": "SET_TPSL",
        "coin": payload.coin.upper(),
        "size": _str(round(payload.position_size, 6)),
        "tpPrice": _str(payload.tp_price),
        "tpRatio": payload.tp_ratio,
        "slPrice": _str(payload.sl_price),
        "slRatio": payload.sl_ratio,
        "existingTpOid": payload.existing_tp_oid,
        "existingSlOid": payload.existing_sl_oid,
    }
    return SetTpslAction.model_validate({
        "action": "SET_TPSL",
        "execution_plan": [item_dict],
        "meta": {"source_text": payload.source_text},
    }).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

@tool(args_schema=ConfirmSetTpslInput)
def confirm_perp_set_tpsl(
    coin: str,
    position_size: float,
    tp_price: float | None = None,
    tp_ratio: float | None = None,
    sl_price: float | None = None,
    sl_ratio: float | None = None,
    existing_tp_oid: int = 0,
    existing_sl_oid: int = 0,
    source_text: str = "",
) -> dict:
    """设置止盈止损卡片（SET_TPSL）

    用户想给仓位设置止盈或止损时使用。TP 和 SL 相互独立，可以只设其中一个。

    参数规则：
    - tp_price 和 tp_ratio 互斥，二选一
    - sl_price 和 sl_ratio 互斥，二选一
    - 止盈：tp_price / tp_ratio / existing_tp_oid > 0 三者至少有一个
    - 止损：sl_price / sl_ratio / existing_sl_oid > 0 三者至少有一个

    existing_tp_oid / existing_sl_oid：
    - 0 = 第一次设置该方向的 TPSL
    - 非0 = 更新已有 TPSL 订单，传入原订单号

    示例：
    - "BTC 仓位止盈 72000，止损 66500" → tp_price=72000, sl_price=66500
    - "BTC 仓位只设止盈 72000" → tp_price=72000
    - "ETH 仓位 30% 止盈，10% 止损" → tp_ratio=0.3, sl_ratio=0.1
    - "把 BTC 止盈改成 72500" → tp_price=72500, existing_tp_oid=18273645
    """
    return confirm_perp_set_tpsl_impl(
        coin=coin,
        position_size=position_size,
        tp_price=tp_price,
        tp_ratio=tp_ratio,
        sl_price=sl_price,
        sl_ratio=sl_ratio,
        existing_tp_oid=existing_tp_oid,
        existing_sl_oid=existing_sl_oid,
        source_text=source_text,
    )


# =============================================================================
# if __name__ == "__main__"
# =============================================================================

if __name__ == "__main__":
    from rich import print

    print("=== 止盈止损（价格）===")
    print(confirm_perp_set_tpsl_impl(
        coin="BTC",
        position_size=0.2921,
        tp_price=72000,
        sl_price=66500,
        source_text="BTC 仓位止盈 72000，止损 66500",
    ))
    print()
    print("=== 止盈止损（比例）===")
    print(confirm_perp_set_tpsl_impl(
        coin="ETH",
        position_size=1.0,
        tp_ratio=0.3,
        sl_ratio=0.1,
        source_text="ETH 仓位 30% 止盈，10% 止损",
    ))
    print()
    print("=== 更新已有 TPSL ===")
    print(confirm_perp_set_tpsl_impl(
        coin="BTC",
        position_size=0.2921,
        tp_price=72500,
        existing_tp_oid=18273645,
        existing_sl_oid=1,  # 已有止损单，不改它
        source_text="把 BTC 止盈改成 72500",
    ))
