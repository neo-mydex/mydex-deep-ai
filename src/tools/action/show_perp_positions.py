"""
查看仓位 Card 模块 (VIEW_POSITION)

按 hyperliquid交易卡片需求文档.md 5.8 实现

支持单个或批量查看仓位信息
"""

from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Literal

from src.tools.perp.get_positions import perp_get_positions_impl
from src.tools.perp.get_open_orders import perp_get_open_orders_impl


# =============================================================================
# Pydantic 类
# =============================================================================

class ShowPositionsAction(BaseModel):
    """show_perp_positions 返回"""
    action: Literal["VIEW_POSITION"]
    execution_plan: list[dict]
    meta: dict


# =============================================================================
# impl 纯函数
# =============================================================================

def show_perp_positions_impl(
    address: str,
    coin: str | None = None,
    include_open_orders: bool = True,
    include_tpsl: bool = True,
    source_text: str = "",
) -> dict:
    """查看仓位卡片（VIEW_POSITION）。用于"看看我 BTC 仓位"、"查看持仓"类意图。"""
    # 1. 获取仓位
    positions_result = perp_get_positions_impl(address=address, coin=coin)
    positions = positions_result.get("positions", [])

    # 2. 批量获取每个币的挂单信息
    coin_to_orders: dict[str, dict] = {}
    if include_open_orders or include_tpsl:
        for p in positions:
            p_coin = p.get("coin")
            if p_coin:
                orders_result = perp_get_open_orders_impl(address=address, coin=p_coin)
                coin_to_orders[p_coin] = orders_result

    # 3. 构建 execution_plan
    execution_plan: list[dict] = []
    for p in positions:
        p_coin = p.get("coin", "")
        side_raw = p.get("side", "flat")
        # size < 0 → short, size > 0 → long
        if isinstance(side_raw, str) and side_raw in ("long", "short"):
            side: Literal["long", "short"] = side_raw
        elif (isinstance(side_raw, (int, float)) and float(side_raw) < 0) or side_raw == "short":
            side = "short"
        else:
            side = "long"

        # 获取挂单数量
        open_orders_count = 0
        tpsl_orders_count = 0
        if p_coin in coin_to_orders:
            orders_data = coin_to_orders[p_coin]
            open_orders_count = orders_data.get("open_order_count", 0)
            tpsl_orders_count = orders_data.get("tpsl_order_count", 0)

        item = {
            "intent": "VIEW_POSITION",
            "coin": p_coin.upper(),
            "side": side,
            "size": round(float(p.get("size", 0)), 6),
            "entry_px": p.get("entry_px"),
            "mark_px": p.get("mark_px"),
            "unrealized_pnl": p.get("unrealized_pnl"),
            "leverage": p.get("leverage"),
            "liquidation_px": p.get("liquidation_px"),
            "open_orders_count": open_orders_count,
            "tpsl_orders_count": tpsl_orders_count,
        }
        execution_plan.append(item)

    return ShowPositionsAction.model_validate({
        "action": "VIEW_POSITION",
        "execution_plan": execution_plan,
        "meta": {"source_text": source_text},
    }).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

@tool
def show_perp_positions(
    address: str,
    coin: str | None = None,
    include_open_orders: bool = True,
    include_tpsl: bool = True,
    source_text: str = "",
) -> dict:
    """查看仓位卡片（VIEW_POSITION）

    用户想查看当前持仓情况时使用。支持单个或批量查看。

    注意：如果用户说"分析仓位"则用纯文本回复，不用此卡片。

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"、"ETH"，不传则返回所有仓位
        include_open_orders: 是否包含挂单数量（用于取消挂单提示），默认 True
        include_tpsl: 是否包含 TPSL 订单数量，默认 True
        source_text: 用户原始表达

    返回示例:
    - "看看我 BTC 仓位" → 单个仓位
    - "查看所有持仓" → 多个仓位
    """
    return show_perp_positions_impl(
        address=address,
        coin=coin,
        include_open_orders=include_open_orders,
        include_tpsl=include_tpsl,
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

    print("=== 查看单个仓位 ===")
    print(show_perp_positions_impl(
        address=EVM_ADDRESS,
        coin="BTC",
        source_text="看看我 BTC 仓位",
    ))
    print()
    print("=== 查看所有仓位 ===")
    print(show_perp_positions_impl(
        address=EVM_ADDRESS,
        source_text="查看所有持仓",
    ))
