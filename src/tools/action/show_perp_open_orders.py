"""
查看当前挂单 Card 模块 (VIEW_OPEN_ORDER)

按 hyperliquid交易卡片需求文档.md 5.10 实现
"""

from langchain.tools import ToolRuntime
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Literal

from src.tools.perp.get_open_orders import perp_get_open_orders_impl
from src.tools.perp.get_positions import perp_get_positions_impl


# =============================================================================
# Pydantic 类
# =============================================================================

class ShowOpenOrdersAction(BaseModel):
    """show_perp_open_order 返回"""
    action: Literal["VIEW_OPEN_ORDER"]
    execution_plan: list[dict]
    meta: dict


# =============================================================================
# impl 纯函数
# =============================================================================

def _classify_order_type(order: dict) -> Literal["limit", "market", "tp", "sl"]:
    """根据订单属性分类 type"""
    is_trigger = order.get("isTrigger", False)
    is_position_tpsl = order.get("isPositionTpsl", False)
    order_type_raw = order.get("orderType", "")

    if is_trigger:
        if is_position_tpsl:
            # 原生 TPSL 单：TP = 止盈单，SL = 止损单
            if "Take Profit" in order_type_raw:
                return "tp"
            elif "Stop" in order_type_raw:
                return "sl"
        else:
            # 用户主动设置的触发单，根据 triggerCondition 判断
            trigger_cond = order.get("triggerCondition", "")
            if "above" in trigger_cond.lower():
                return "tp"
            elif "below" in trigger_cond.lower():
                return "sl"
    else:
        # 非触发单：limit 或 market
        if "Limit" in order_type_raw:
            return "limit"
        elif "Market" in order_type_raw:
            return "market"
    return "limit"


def _resolve_direction(order: dict, coin: str, positions_by_coin: dict) -> Literal["long", "short"]:
    """解析订单 direction

    逻辑：
    - reduceOnly=true 的订单：一定是平仓单，direction 由 side 决定
      - side=A（卖出）→ 平多 → direction="long"
      - side=B（买入）→ 平空 → direction="short"
    - reduceOnly=false 的订单：开仓单
      - side=B（买入）→ 开多 → direction="long"
      - side=A（卖出）→ 开空 → direction="short"
    """
    reduce_only = order.get("reduceOnly", False)
    side = order.get("side", "")

    if reduce_only:
        # 平仓单
        return "long" if side == "A" else "short"
    else:
        # 开仓单
        return "long" if side == "B" else "short"


def show_perp_open_order_impl(
    address: str,
    coin: str | None = None,
    source_text: str = "",
) -> dict:
    """查看当前挂单卡片（VIEW_OPEN_ORDER）。用于"看看我 BTC 的挂单"、"查一下挂单"类意图。"""
    # 1. 获取挂单
    orders_result = perp_get_open_orders_impl(address=address, coin=coin)
    orders = orders_result.get("orders", [])

    # 2. 获取仓位（用于补充 leverage、unrealizedPnl、entryPrice 等字段）
    positions_result = perp_get_positions_impl(address=address, coin=coin)
    positions = positions_result.get("positions", [])
    # 按 coin 建索引
    positions_by_coin: dict[str, dict] = {p.get("coin", "").upper(): p for p in positions}

    # 3. 构建 execution_plan
    execution_plan: list[dict] = []
    for order in orders:
        o_coin = order.get("coin", "").upper()
        pos = positions_by_coin.get(o_coin, {})

        order_type = _classify_order_type(order)
        direction = _resolve_direction(order, o_coin, positions_by_coin)

        # 根据 type 填充价格字段
        if order_type == "limit":
            limit_price = order.get("limitPx")
            tp_price = None
            sl_price = None
        elif order_type == "tp":
            limit_price = None
            tp_price = order.get("triggerPx")
            sl_price = None
        elif order_type == "sl":
            limit_price = None
            tp_price = None
            sl_price = order.get("triggerPx")
        else:
            limit_price = None
            tp_price = None
            sl_price = None

        item = {
            "intent": "VIEW_OPEN_ORDER",
            "oid": str(order.get("oid") or ""),
            "timestamp": order.get("timestamp"),
            "coin": o_coin,
            "direction": direction,
            "leverage": pos.get("leverage"),
            "type": order_type,
            "limitPrice": limit_price,
            "tpPrice": tp_price,
            "slPrice": sl_price,
            "size": order.get("sz", ""),
            "usdcSize": str(pos.get("position_value", "")) if pos else "",
            "unrealizedPnl": str(pos.get("unrealized_pnl", "")) if pos else None,
            "closedPnl": None,
            "entryPrice": str(pos.get("entry_px", "")) if pos else None,
            "exitPrice": None,
        }
        execution_plan.append(item)

    # 4. 按 timestamp 倒序（新的在前）
    execution_plan.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)

    return ShowOpenOrdersAction.model_validate({
        "action": "VIEW_OPEN_ORDER",
        "execution_plan": execution_plan,
        "meta": {"source_text": source_text},
    }).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

@tool
def show_perp_open_order(
    runtime: ToolRuntime,
    coin: str | None = None,
    source_text: str = "",
) -> dict:
    """查看当前挂单卡片（VIEW_OPEN_ORDER）

    用户想查看当前挂单（也称"委托"或"委托单"）情况时使用。支持单个或批量查看。

    注意：如果用户说"分析挂单"则用纯文本回复，不用此卡片。

    参数:
        runtime: Tool运行时，从 context 自动获取钱包地址，无需传入
        coin: 币种名称，如 "BTC"、"ETH"，不传则返回所有挂单
        source_text: 用户原始表达

    返回示例:
    - "看看我 BTC 的挂单" → BTC 挂单列表
    - "查一下挂单" → 所有挂单
    """
    ctx = runtime.context
    if not ctx or not ctx.evm_address:
        return ShowOpenOrdersAction.model_validate({
            "action": "VIEW_OPEN_ORDER",
            "execution_plan": [],
            "meta": {"source_text": source_text, "error": "无法获取用户钱包地址"},
        }).model_dump()
    return show_perp_open_order_impl(
        address=ctx.evm_address,
        coin=coin,
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

    print("=== 查看单个币种挂单 ===")
    print(show_perp_open_order_impl(
        address=EVM_ADDRESS,
        coin="BTC",
        source_text="看看我 BTC 的挂单",
    ))
    print()
    print("=== 查看所有挂单 ===")
    print(show_perp_open_order_impl(
        address=EVM_ADDRESS,
        source_text="查一下挂单",
    ))
