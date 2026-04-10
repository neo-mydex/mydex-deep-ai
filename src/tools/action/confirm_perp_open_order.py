"""
开仓 Confirm 模块 (OPEN_LONG / OPEN_SHORT)

按 hyperliquid交易卡片需求文档.md 5.4/5.5 实现

Key constraints:
- tp 和 tp_ratio 互斥，二选一
- sl 和 sl_ratio 互斥，二选一
- 整数价格写成字符串 "72000" 不是 "72000.0"
- UPDATE_LEVERAGE step 只在开仓时有，补仓时无
"""

from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Literal


# =============================================================================
# Pydantic 类
# =============================================================================

class ConfirmOpenOrderAction(BaseModel):
    """confirm_perp_open_order 返回"""
    action: Literal["OPEN_LONG", "OPEN_SHORT"]
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


def confirm_perp_open_order_impl(
    coin: str,
    leverage: float,
    usdc_size: float,
    side: Literal["long", "short"],
    action_mode: Literal["open", "add"] = "open",
    margin_mode: Literal["cross", "isolated"] = "cross",
    order_type: Literal["market", "limit"] = "market",
    entry_price: float | None = None,
    tp: float | None = None,
    sl: float | None = None,
    tp_ratio: float | None = None,
    sl_ratio: float | None = None,
    mark_price: float | None = None,
    source_text: str = "",
) -> dict:
    """开仓卡片（OPEN_LONG / OPEN_SHORT）。用于"做多 BTC 20x 1000u"或"做空 ETH"类意图。"""
    if tp is not None and tp_ratio is not None:
        raise ValueError("tp 和 tp_ratio 二选一，不可同时指定")
    if sl is not None and sl_ratio is not None:
        raise ValueError("sl 和 sl_ratio 二选一，不可同时指定")

    is_buy = side == "long"
    action_type = "OPEN_LONG" if is_buy else "OPEN_SHORT"
    is_cross = margin_mode == "cross"

    # 计算仓位大小
    size: str | None = None
    if mark_price and mark_price > 0:
        size_val = usdc_size * leverage / mark_price
        size = _str(round(size_val, 6))

    usdc_margin: str | None = _str(round(usdc_size, 6)) if usdc_size > 0 else None

    execution_plan: list[dict] = []

    if action_mode == "open":
        execution_plan.append({
            "intent": "UPDATE_LEVERAGE",
            "coin": coin.upper(),
            "leverage": int(leverage),
            "isCross": is_cross,
        })

    open_order: dict = {
        "intent": "OPEN_ORDER",
        "coin": coin.upper(),
        "isBuy": is_buy,
        "size": size,
        "usdcMargin": usdc_margin,
        "margin": None,
        "markPrice": mark_price,
        "orderType": order_type,
        "limitPrice": _str(entry_price) if order_type == "limit" and entry_price is not None else None,
    }

    if tp is not None:
        open_order["tpPrice"] = _str(tp)
        open_order["tpRatio"] = None
    elif tp_ratio is not None:
        open_order["tpPrice"] = None
        open_order["tpRatio"] = tp_ratio
    else:
        open_order["tpPrice"] = None
        open_order["tpRatio"] = None

    if sl is not None:
        open_order["slPrice"] = _str(sl)
        open_order["slRatio"] = None
    elif sl_ratio is not None:
        open_order["slPrice"] = None
        open_order["slRatio"] = sl_ratio
    else:
        open_order["slPrice"] = None
        open_order["slRatio"] = None

    execution_plan.append(open_order)

    return ConfirmOpenOrderAction.model_validate({
        "action": action_type,
        "execution_plan": execution_plan,
        "meta": {"source_text": source_text},
    }).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

@tool
def confirm_perp_open_order(
    coin: str,
    leverage: float,
    usdc_size: float,
    side: Literal["long", "short"],
    action_mode: Literal["open", "add"] = "open",
    margin_mode: Literal["cross", "isolated"] = "cross",
    order_type: Literal["market", "limit"] = "market",
    entry_price: float | None = None,
    tp: float | None = None,
    sl: float | None = None,
    tp_ratio: float | None = None,
    sl_ratio: float | None = None,
    mark_price: float | None = None,
    source_text: str = "",
) -> dict:
    """开仓卡片（OPEN_LONG / OPEN_SHORT）

    用户想做多或做空某个币种时使用。

    示例：
    - "做多 BTC 20x 1000u" → coin="BTC", leverage=20, usdc_size=1000, side="long"
    - "做空 ETH 10x 500u" → coin="ETH", leverage=10, usdc_size=500, side="short"
    - "做多 BTC 20x 1000u，止盈 72000，止损 66500" → tp=72000, sl=66500
    - "做多 BTC 10x 1000u，止盈30%" → tp_ratio=0.3
    - "补仓 BTC 100u" → action_mode="add", coin="BTC", usdc_size=100
    """
    return confirm_perp_open_order_impl(
        coin=coin,
        leverage=leverage,
        usdc_size=usdc_size,
        side=side,
        action_mode=action_mode,
        margin_mode=margin_mode,
        order_type=order_type,
        entry_price=entry_price,
        tp=tp,
        sl=sl,
        tp_ratio=tp_ratio,
        sl_ratio=sl_ratio,
        mark_price=mark_price,
        source_text=source_text,
    )


# =============================================================================
# if __name__ == "__main__"
# =============================================================================

if __name__ == "__main__":
    from rich import print

    # uv run python -m src.tools.action.confirm_perp_open_order

    print("=== OPEN_LONG ===")
    print(confirm_perp_open_order_impl(
        coin="BTC",
        leverage=20,
        usdc_size=1000,
        side="long",
        margin_mode="cross",
        order_type="market",
        tp=72000,
        sl=66500,
        mark_price=68450.5,
        source_text="做多 BTC 20x 1000u，止盈 72000，止损 66500",
    ))
    print()
    print("=== OPEN_SHORT ===")
    print(confirm_perp_open_order_impl(
        coin="ETH",
        leverage=10,
        usdc_size=500,
        side="short",
        margin_mode="isolated",
        order_type="limit",
        entry_price=3650.0,
        tp=3450,
        sl=3720,
        mark_price=3650.0,
        source_text="ETH 10x 限价 3650 开空 500u",
    ))
    print()
    print("=== tp_ratio/sl_ratio 模式 ===")
    print(confirm_perp_open_order_impl(
        coin="BTC",
        leverage=10,
        usdc_size=1000,
        side="long",
        margin_mode="cross",
        order_type="market",
        tp_ratio=0.3,
        sl_ratio=0.1,
        mark_price=68000,
        source_text="做多 BTC 10x 1000u，止盈30%，止损10%",
    ))
