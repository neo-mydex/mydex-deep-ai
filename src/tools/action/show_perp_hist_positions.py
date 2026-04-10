"""
查看历史仓位 Action 模块 (VIEW_HIST_POSITION)

按 hyperliquid交易卡片需求文档.md 5.9 实现

数据来源：perp_get_hist_orders（已合并 historical_orders + user_fills_by_time）
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal

from src.tools.perp.get_hist_orders import perp_get_hist_orders_impl


class ViewHistPositionIntent(BaseModel):
    """VIEW_HIST_POSITION 单条记录"""
    intent: Literal["VIEW_HIST_POSITION"] = "VIEW_HIST_POSITION"
    coin: str
    oid: str
    unrealizedPnl: str | None = None
    closedPnl: str | None = None
    entryPrice: str | None = None
    exitPrice: str | None = None
    timestamp: int | None = None
    direction: str | None = None
    leverage: int | None = None
    type: str | None = None
    limitPrice: str | None = None
    tpPrice: str | None = None
    slPrice: str | None = None
    size: str
    usdcSize: str


class ViewHistPositionAction(BaseModel):
    """show_perp_hist_positions 返回"""
    action: Literal["VIEW_HIST_POSITION"] = "VIEW_HIST_POSITION"
    execution_plan: list[ViewHistPositionIntent] = Field(default_factory=list)
    meta: dict


def show_perp_hist_positions_impl(
    address: str,
    coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    source_text: str = "",
) -> dict:
    """生成 VIEW_HIST_POSITION 卡片

    数据直接来自 perp_get_hist_orders_impl（已合并 historical_orders + user_fills_by_time），
    无需额外并发查询。
    """
    result = perp_get_hist_orders_impl(
        address=address,
        coin=coin,
        start_time=start_time,
        end_time=end_time,
    )

    orders = result.get("orders", [])
    if not orders:
        return ViewHistPositionAction.model_validate({
            "action": "VIEW_HIST_POSITION",
            "execution_plan": [],
            "meta": {"source_text": source_text},
        }).model_dump()

    execution_plan: list[dict] = []
    for order in orders:
        sz = order.get("sz", "0")
        px = order.get("px", "0")
        dir_str = order.get("dir", "")
        dir_lower = dir_str.lower() if dir_str else ""

        # 计算 usdcSize
        try:
            usdc_size = str(round(float(sz) * float(px), 6))
        except (TypeError, ValueError):
            usdc_size = "0"

        # entry/exit 价格：dir 包含 "open" 则为 entryPrice，包含 "close" 则为 exitPrice
        if "open" in dir_lower:
            entry_price = order.get("entryPx") or order.get("px")
            exit_price = None
        else:
            entry_price = None
            exit_price = order.get("entryPx") or order.get("px")

        item = {
            "intent": "VIEW_HIST_POSITION",
            "coin": order.get("coin", "").upper(),
            "oid": str(order.get("oid", "")),
            "unrealizedPnl": None,
            "closedPnl": order.get("closedPnl") if "close" in dir_lower else None,
            "entryPrice": entry_price,
            "exitPrice": exit_price,
            "timestamp": order.get("time"),
            "direction": _infer_direction(dir_str, order.get("side", "")),
            "leverage": order.get("leverage"),
            "type": order.get("orderType"),
            "limitPrice": order.get("limitPx"),
            "tpPrice": order.get("tpPrice"),
            "slPrice": order.get("slPrice"),
            "size": sz,
            "usdcSize": usdc_size,
        }
        execution_plan.append(item)

    return ViewHistPositionAction.model_validate({
        "action": "VIEW_HIST_POSITION",
        "execution_plan": execution_plan,
        "meta": {"source_text": source_text},
    }).model_dump()


def _infer_direction(dir: str, side: str) -> str | None:
    """从 dir + side 推断 direction

    Hyperliquid API 返回的原始值：
    - dir: "Open Long", "Open Short", "Close Long", "Close Short"
    - side: "B" (Buy), "S" (Sell)
    """
    dir_lower = dir.lower() if dir else ""
    side_lower = side.lower() if side else ""

    is_open = "open" in dir_lower
    is_close = "close" in dir_lower

    if is_open:
        return "long" if side_lower in ("b", "buy") else "short"
    if is_close:
        return "short" if side_lower in ("b", "buy") else "long"
    return None


@tool
def show_perp_hist_positions(
    address: str,
    coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    source_text: str = "",
) -> dict:
    """
    生成 VIEW_HIST_POSITION 卡片

    用于"看看我历史仓位"、"历史成交"类意图。

    参数:
        address: 用户钱包地址
        coin: 币种名称，如不传则查所有
        start_time: 开始时间（毫秒时间戳），默认最近 30 天
        end_time: 结束时间（毫秒时间戳），默认当前
        source_text: 用户原始表达

    返回: VIEW_HIST_POSITION card
    """
    return show_perp_hist_positions_impl(
        address=address,
        coin=coin,
        start_time=start_time,
        end_time=end_time,
        source_text=source_text,
    )


if __name__ == "__main__":
    from rich import print
    from dotenv import load_dotenv
    import os
    load_dotenv()
    EVM_ADDRESS = os.environ["EVM_ADDRESS"]

    print("=== 查看历史仓位 ===")
    print(show_perp_hist_positions_impl(
        address=EVM_ADDRESS,
        coin="BTC",
        start_time=0,
        source_text="看看我 BTC 历史仓位",
    ))
