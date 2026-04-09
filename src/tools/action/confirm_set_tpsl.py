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
from pydantic import BaseModel
from typing import Literal


# =============================================================================
# Pydantic 类
# =============================================================================

class SetTpslAction(BaseModel):
    """confirm_set_tpsl 返回"""
    action: Literal["SET_TPSL"]
    execution_plan: list[dict]
    meta: dict


# =============================================================================
# impl 纯函数
# =============================================================================

def _str(v: float | None) -> str | None:
    """转字符串，去除无意义的 .0"""
    if v is None:
        return None
    s = str(v)
    return s[:-2] if s.endswith(".0") else s


def confirm_set_tpsl_impl(
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
    if tp_price is not None and tp_ratio is not None:
        raise ValueError("tp_price 和 tp_ratio 二选一，不可同时指定")
    if tp_price is None and tp_ratio is None and existing_tp_oid == 0:
        raise ValueError("止盈需要提供 tp_price 或 tp_ratio 之一（或者已有止盈单号则传 existing_tp_oid）")
    if sl_price is not None and sl_ratio is not None:
        raise ValueError("sl_price 和 sl_ratio 二选一，不可同时指定")
    if sl_price is None and sl_ratio is None and existing_sl_oid == 0:
        # 既是新建 sl 又没提供任何 sl 参数，报错
        raise ValueError("止损需要提供 sl_price 或 sl_ratio 之一（或者已有止损单号则传 existing_sl_oid）")

    item_dict = {
        "intent": "SET_TPSL",
        "coin": coin.upper(),
        "size": _str(round(position_size, 6)),
        "tpPrice": _str(tp_price),
        "tpRatio": tp_ratio,
        "slPrice": _str(sl_price),
        "slRatio": sl_ratio,
        "existingTpOid": existing_tp_oid,
        "existingSlOid": existing_sl_oid,
    }
    return SetTpslAction.model_validate({
        "action": "SET_TPSL",
        "execution_plan": [item_dict],
        "meta": {"source_text": source_text},
    }).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

@tool
def confirm_set_tpsl(
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

    用户想给仓位设置止盈或止损时使用。

    互斥规则：
    - tp_price 和 tp_ratio 二选一（指定价格或指定比例）
    - sl_price 和 sl_ratio 二选一

    existing_tp_oid / existing_sl_oid：
    - 0 = 第一次设置该方向的 TPSL
    - 非0 = 更新已有 TPSL 订单，传入原订单号

    示例：
    - "BTC 仓位止盈 72000，止损 66500" → tp_price=72000, sl_price=66500
    - "ETH 仓位 30% 止盈，10% 止损" → tp_ratio=0.3, sl_ratio=0.1
    - "把 BTC 止盈改成 72500" → tp_price=72500, existing_tp_oid=18273645
    """
    return confirm_set_tpsl_impl(
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
    print(confirm_set_tpsl_impl(
        coin="BTC",
        position_size=0.2921,
        tp_price=72000,
        sl_price=66500,
        source_text="BTC 仓位止盈 72000，止损 66500",
    ))
    print()
    print("=== 止盈止损（比例）===")
    print(confirm_set_tpsl_impl(
        coin="ETH",
        position_size=1.0,
        tp_ratio=0.3,
        sl_ratio=0.1,
        source_text="ETH 仓位 30% 止盈，10% 止损",
    ))
    print()
    print("=== 更新已有 TPSL ===")
    print(confirm_set_tpsl_impl(
        coin="BTC",
        position_size=0.2921,
        tp_price=72500,
        existing_tp_oid=18273645,
        existing_sl_oid=1,  # 已有止损单，不改它
        source_text="把 BTC 止盈改成 72500",
    ))
