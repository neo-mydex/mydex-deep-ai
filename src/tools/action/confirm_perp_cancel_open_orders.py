"""
取消挂单 Confirm 模块 (CANCEL_OPEN_ORDER)

输入：预筛选好的订单列表（CancelItem）
Skill 层负责调用 check_can_cancel 获取所有订单、根据用户意图筛选，
然后把筛选结果传给 confirm。

按 hyperliquid交易卡片需求文档.md 5.11 实现
"""

from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Literal


# =============================================================================
# Pydantic 类
# =============================================================================

class ConfirmCancelOpenOrdersAction(BaseModel):
    """confirm_perp_cancel_open_orders 返回"""
    action: Literal["CANCEL_OPEN_ORDER"]
    execution_plan: list[dict]
    meta: dict


class CancelItem(BaseModel):
    """单个取消挂单项（预筛选好的）"""
    oid: int
    coin: str
    size: str                            # 订单数量（字符串）
    order_type: Literal["limit", "market", "tp", "sl"]
    direction: Literal["long", "short"]   # 已翻译好的方向
    limit_price: str | None = None      # 限价格（字符串）
    trigger_price: str | None = None     # 触发价格（字符串）
    reduce_only: bool = False
    timestamp: int = 0
    leverage: int | None = None         # 仓位杠杆
    unrealized_pnl: str | None = None   # 未实现盈亏
    entry_price: str | None = None      # 入场价格
    position_value: str | None = None    # 仓位价值


# =============================================================================
# impl 纯函数
# =============================================================================

def _str(v: float | None) -> str | None:
    """转字符串，去除无意义的 .0"""
    if v is None:
        return None
    s = str(v)
    return s[:-2] if s.endswith(".0") else s


def _build_order_item(item: CancelItem) -> dict:
    """构建单个订单的 CANCEL_OPEN_ORDER intent 项"""
    order_type = item.order_type

    if order_type == "limit":
        limit_price_str = item.limit_price
        tp_price_str = None
        sl_price_str = None
    elif order_type == "tp":
        limit_price_str = None
        tp_price_str = item.trigger_price
        sl_price_str = None
    elif order_type == "sl":
        limit_price_str = None
        tp_price_str = None
        sl_price_str = item.trigger_price
    else:
        limit_price_str = None
        tp_price_str = None
        sl_price_str = None

    return {
        "intent": "CANCEL_OPEN_ORDER",
        "oid": str(item.oid),
        "coin": item.coin.upper(),
        "direction": item.direction,
        "leverage": item.leverage,
        "type": order_type,
        "limitPrice": limit_price_str,
        "tpPrice": tp_price_str,
        "slPrice": sl_price_str,
        "size": item.size,
        "usdcSize": item.position_value or "",
        "unrealizedPnl": item.unrealized_pnl,
        "closedPnl": None,
        "entryPrice": item.entry_price,
        "exitPrice": None,
        "timestamp": item.timestamp,
    }


def confirm_perp_cancel_open_orders_impl(
    orders: list[CancelItem],
    source_text: str = "",
) -> dict:
    """取消挂单卡片（CANCEL_OPEN_ORDER）。接收预筛选好的订单列表。

    参数:
        orders: 预筛选好的订单列表（通常来自 check_can_cancel 的 matching_orders）
        source_text: 用户原始表达
    """
    if not orders:
        return ConfirmCancelOpenOrdersAction.model_validate({
            "action": "CANCEL_OPEN_ORDER",
            "execution_plan": [],
            "meta": {"source_text": source_text, "error": "没有要取消的订单"},
        }).model_dump()

    execution_plan = [_build_order_item(item) for item in orders]

    return ConfirmCancelOpenOrdersAction.model_validate({
        "action": "CANCEL_OPEN_ORDER",
        "execution_plan": execution_plan,
        "meta": {"source_text": source_text},
    }).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

@tool
def confirm_perp_cancel_open_orders(
    orders: list[CancelItem],
    source_text: str = "",
) -> dict:
    """取消挂单确认卡片（CANCEL_OPEN_ORDER）

    接收预筛选好的订单列表，生成取消确认卡片。

    参数:
        orders: 预筛选好的订单列表（通常来自 check_can_cancel 的 matching_orders）
        source_text: 用户原始表达，如"取消 SOL 限价单和 AVAX 止盈单"

    返回:
        CANCEL_OPEN_ORDER intent 列表，每个 intent 对应一个要取消的订单
    """
    return confirm_perp_cancel_open_orders_impl(
        orders=orders,
        source_text=source_text,
    )


# =============================================================================
# if __name__ == "__main__"
# =============================================================================

if __name__ == "__main__":
    from rich import print
    from dotenv import load_dotenv
    import os
    load_dotenv()
    EVM_ADDRESS = os.environ["EVM_ADDRESS"]

    # 示例：从 check_can_cancel 获取后，筛选出 SOL 限价单
    from src.tools.perp.check_can_cancel import perp_check_can_cancel_impl

    all_orders = perp_check_can_cancel_impl(address=EVM_ADDRESS)
    print(f"总挂单数: {len(all_orders['matching_orders'])}")

    # 筛选 SOL 限价单
    sol_limit = [
        o for o in all_orders["matching_orders"]
        if o["coin"] == "SOL" and o["type"] == "limit"
    ]
    print(f"SOL 限价单: {len(sol_limit)}")

    # 转为 CancelItem
    cancel_items = [
        CancelItem(
            oid=o["oid"],
            coin=o["coin"],
            size=str(o["size"]),
            order_type=o["type"],
            direction=o["side"],
            limit_price=str(o["limit_price"]) if o["limit_price"] else None,
            trigger_price=str(o["trigger_price"]) if o["trigger_price"] else None,
            reduce_only=o["reduce_only"],
            timestamp=o["timestamp"],
        )
        for o in sol_limit
    ]

    print("=== 取消 SOL 限价单 ===")
    print(confirm_perp_cancel_open_orders_impl(
        orders=cancel_items,
        source_text="取消 SOL 限价单",
    ))
