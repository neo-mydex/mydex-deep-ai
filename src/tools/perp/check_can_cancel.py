"""
取消挂单前检查
"""

from typing import Any, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.perp.get_open_orders import perp_get_open_orders_impl

Network = Literal["mainnet", "testnet"]


class MatchingOrder(BaseModel):
    """单个挂单摘要"""
    oid: int
    coin: str
    size: float                          # sz → size
    type: Literal["limit", "market", "tp", "sl"]  # orderType 分类后
    side: Literal["long", "short"]       # B→long, S→short
    limit_price: float | None = None      # limitPx → limitPrice
    trigger_price: float | None = None    # triggerPx → triggerPrice
    timestamp: int
    reduce_only: bool


class CanCancelResponse(BaseModel):
    """perp_check_can_cancel 返回格式"""
    ok: bool                              # 是否有可取消的订单
    matching_orders: list[MatchingOrder] = Field(default_factory=list)  # 匹配的订单列表
    corrections: list[str] = Field(default_factory=list)  # 警告/纠正
    issues: list[dict[str, Any]] = Field(default_factory=list)  # 错误列表（block）
    follow_up_question: str = ""


def _classify_order_type(order: dict) -> Literal["limit", "market", "tp", "sl"]:
    """根据订单属性分类 type"""
    is_trigger = order.get("isTrigger", False)
    is_position_tpsl = order.get("isPositionTpsl", False)
    order_type_raw = order.get("orderType", "")

    if is_trigger:
        if is_position_tpsl:
            if "Take Profit" in order_type_raw:
                return "tp"
            elif "Stop" in order_type_raw:
                return "sl"
        else:
            trigger_cond = order.get("triggerCondition", "")
            if "above" in trigger_cond.lower():
                return "tp"
            elif "below" in trigger_cond.lower():
                return "sl"
    else:
        if "Limit" in order_type_raw:
            return "limit"
        elif "Market" in order_type_raw:
            return "market"
    return "limit"


def _translate_side(side: str) -> Literal["long", "short"]:
    """Hyperliquid side: B(uy)=long, S(ell)=short"""
    return "long" if side == "B" else "short"


def _simplify_order(order: dict) -> MatchingOrder:
    """提取订单关键字段，去除 Hyperliquid 原生冗余字段，并做字段名翻译"""
    classified_type = _classify_order_type(order)
    return MatchingOrder(
        oid=order.get("oid", 0),
        coin=order.get("coin", ""),
        size=order.get("sz", 0),
        type=classified_type,
        side=_translate_side(order.get("side", "")),
        limit_price=order.get("limitPx"),
        trigger_price=order.get("triggerPx"),
        timestamp=order.get("timestamp", 0),
        reduce_only=order.get("reduceOnly", False),
    )


def perp_check_can_cancel_impl(
    address: str,
    coin: str | None = None,
    order_type: Literal["limit", "market", "tp", "sl"] | None = None,
    network: Network = "mainnet",
) -> dict:
    """取消挂单前检查（纯函数，可直接测试）

    检查是否有符合条件的挂单可以取消。

    参数:
        address: 钱包地址
        coin: 币种名称筛选，如 "BTC"，不传则不限
        order_type: 订单类型筛选，"limit" / "market" / "tp" / "sl"，不传则不限
        network: 网络类型

    返回:
        CanCancelResponse: {
            "ok": bool,
            "matching_orders": list[MatchingOrder],
            "corrections": list[str],
            "issues": list[dict],
            "follow_up_question": str,
        }
    """
    # 1. 获取当前挂单
    orders_result = perp_get_open_orders_impl(address=address, coin=coin, network=network)
    orders = orders_result.get("orders", [])

    # 2. 按 coin 筛选（case-insensitive）
    if coin is not None:
        filtered_orders = [
            o for o in orders
            if o.get("coin", "").upper() == coin.upper()
        ]
    else:
        filtered_orders = orders

    # 3. 按 order_type 筛选
    if order_type is not None:
        filtered_orders = [
            o for o in filtered_orders
            if _classify_order_type(o) == order_type
        ]

    # 4. 构建返回
    issues = []
    if len(filtered_orders) == 0:
        type_name = {"limit": "限价单", "market": "市价单", "tp": "止盈单", "sl": "止损单"}.get(order_type, order_type)
        if coin and order_type:
            msg = f"没有找到 {coin} 的{type_name}挂单"
        elif coin:
            msg = f"没有找到 {coin} 的挂单"
        elif order_type:
            msg = f"没有找到{type_name}挂单"
        else:
            msg = "没有找到任何挂单"
        issues.append({"code": "no_matching_orders", "message": msg})

    return CanCancelResponse(
        ok=len(filtered_orders) > 0,
        matching_orders=[_simplify_order(o) for o in filtered_orders],
        corrections=[],
        issues=issues,
        follow_up_question="",
    ).model_dump()


@tool
def perp_check_can_cancel(
    address: str,
    coin: str | None = None,
    order_type: Literal["limit", "market", "tp", "sl"] | None = None,
    network: Network = "mainnet",
) -> CanCancelResponse:
    """
    取消挂单前的可行性校验工具。

    检查是否有符合条件的挂单可以取消，用于"取消 BTC 挂单"类意图。

    参数:
        address: 用户钱包地址
        coin: 币种名称，如不传则返回所有币的挂单
        order_type: 订单类型筛选，"limit" / "market" / "tp" / "sl"，不传则不限类型
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        CanCancelResponse: {
            "ok": bool,
            "matching_orders": list[MatchingOrder],
            "corrections": list[str],
            "issues": list[dict],
            "follow_up_question": str,
        }
    """
    return perp_check_can_cancel_impl(
        address=address,
        coin=coin,
        order_type=order_type,
        network=network,
    )


if __name__ == "__main__":
    from rich import print
    from dotenv import load_dotenv
    import os
    load_dotenv()
    EVM_ADDRESS = os.environ["EVM_ADDRESS"]

    print("=== check_can_cancel: BTC ===")
    print(perp_check_can_cancel_impl(address=EVM_ADDRESS, coin="BTC"))
    print()
    print("=== check_can_cancel: all ===")
    print(perp_check_can_cancel_impl(address=EVM_ADDRESS))
