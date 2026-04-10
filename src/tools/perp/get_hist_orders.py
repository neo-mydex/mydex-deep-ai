"""
用户历史订单/成交查询

合并 historical_orders（完整订单信息）和 user_fills_by_time（成交记录）数据。
"""

import time
from typing import Literal, Any
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

from src.services.hyperliquid import get_historical_orders, get_user_fills_by_time

Network = Literal["mainnet", "testnet"]

DEFAULT_DAYS = 30


class HistOrderDetail(BaseModel):
    """合并后的历史订单/成交详情

    合并来源：
    - historical_orders: entryPx, leverage, orderType, tpPrice, slPrice, limitPx
    - user_fills_by_time: coin, sz, px, closedPnl, dir, time, oid
    """
    model_config = ConfigDict(extra="ignore")

    oid: int
    coin: str
    # 成交信息（来自 user_fills_by_time）
    sz: str  # 成交数量
    px: str  # 成交价格
    closedPnl: str  # 已平仓位盈亏
    time: int  # 成交时间戳
    dir: str  # "Open Long", "Close Short" 等
    # 订单详情（来自 historical_orders）
    side: str  # "B" / "S"
    entryPx: str | None = None  # 开仓价格
    exitPx: str | None = None  # 平仓价格（从 fills 的 px 推断）
    leverage: int | None = None
    orderType: str | None = None  # "Limit", "Market" 等
    limitPx: str | None = None
    tpPrice: str | None = None
    slPrice: str | None = None


class HistOrdersResponse(BaseModel):
    """perp_get_hist_orders 返回格式"""
    ok: bool
    address: str
    network: Network
    coin: str | None = None
    orders: list[HistOrderDetail] = Field(default_factory=list)


def perp_get_hist_orders_impl(
    address: str,
    coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    network: Network = "mainnet",
) -> dict:
    """获取用户历史订单+成交（纯函数，可直接测试）

    合并 historical_orders 和 user_fills_by_time：
    - historical_orders 提供完整订单信息（entryPx、leverage、tpPrice 等）
    - user_fills_by_time 提供成交记录（closedPnl、dir、px、sz 等）
    - 两者通过 oid 关联
    """
    now_ms = int(time.time() * 1000)
    if start_time is None:
        start_time = now_ms - DEFAULT_DAYS * 24 * 60 * 60 * 1000
    if end_time is None:
        end_time = now_ms
    if start_time > end_time:
        return HistOrdersResponse.model_validate({
            "ok": False,
            "address": address,
            "network": network,
            "coin": coin,
            "orders": [],
        }).model_dump()

    # 并行调用两个 API
    hist_result = get_historical_orders(address=address, network=network)
    fills_result = get_user_fills_by_time(
        address=address,
        start_time=start_time,
        end_time=end_time,
        network=network,
    )

    # 用 fills_by_time 的数据作为主记录（因为包含成交信息）
    # 先按 oid 建索引
    fills_by_oid: dict[int, dict] = {}
    for fill in fills_result.get("fills", []):
        oid = fill.get("oid")
        if oid is not None:
            fills_by_oid[oid] = fill

    # historical_orders 是 list of {"order": {...}, "status": "...", ...}
    hist_orders = hist_result.get("orders", [])

    merged: list[dict] = []
    seen_oids: set[int] = set()

    # 先处理有 fills 的订单（实际发生过成交的）
    for fill in fills_result.get("fills", []):
        oid = fill.get("oid")
        if oid is None:
            continue
        if coin is not None and fill.get("coin") != coin:
            continue

        # 找对应的 historical_orders 记录
        order_data: dict[str, Any] = {}
        for item in hist_orders:
            order = item.get("order", {})
            if order.get("oid") == oid:
                order_data = order
                break

        fill_coin = fill.get("coin", "")
        fill_dir = fill.get("dir", "")
        fill_side = fill.get("side", "")

        # 推断 direction
        dir_lower = fill_dir.lower() if fill_dir else ""
        if "open" in dir_lower:
            direction = "long" if fill_side.lower() in ("b", "buy") else "short"
        elif "close" in dir_lower:
            direction = "short" if fill_side.lower() in ("b", "buy") else "long"
        else:
            direction = None

        # 从 historical_orders 提取字段
        order_type_raw = order_data.get("orderType", "")
        if isinstance(order_type_raw, dict):
            order_type = order_type_raw.get("type", "").lower() if order_type_raw.get("type") else None
        elif isinstance(order_type_raw, str):
            order_type = order_type_raw.lower()
        else:
            order_type = None

        leverage_val = order_data.get("leverage")
        if isinstance(leverage_val, dict):
            leverage_val = leverage_val.get("value")
        try:
            leverage = int(leverage_val) if leverage_val is not None else None
        except (TypeError, ValueError):
            leverage = None

        merged.append({
            "oid": oid,
            "coin": fill_coin,
            "sz": fill.get("sz", "0"),
            "px": fill.get("px", "0"),
            "closedPnl": fill.get("closedPnl", "0"),
            "time": fill.get("time", 0),
            "dir": fill_dir,
            "side": order_data.get("side", fill_side),
            "entryPx": order_data.get("entryPx"),
            "exitPx": None,  # exitPx 需要根据 dir 推断
            "leverage": leverage,
            "orderType": order_type,
            "limitPx": order_data.get("limitPx"),
            "tpPrice": order_data.get("tpPrice"),
            "slPrice": order_data.get("slPrice"),
        })
        seen_oids.add(oid)

    # 按 time 降序排列
    merged.sort(key=lambda x: x.get("time", 0), reverse=True)

    return HistOrdersResponse.model_validate({
        "ok": hist_result.get("ok", False),
        "address": address,
        "network": network,
        "coin": coin,
        "orders": merged,
    }).model_dump()


@tool
def perp_get_hist_orders(
    address: str,
    coin: str | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    network: Network = "mainnet",
) -> HistOrdersResponse:
    """
    查询用户历史订单和成交记录。

    合并 historical_orders（完整订单信息）和 user_fills_by_time（成交记录），
    通过 oid 关联，返回完整的订单+成交数据。

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"，不传则查所有
        start_time: 开始时间（毫秒时间戳），默认最近 30 天
        end_time: 结束时间（毫秒时间戳），默认当前时间
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        HistOrdersResponse: {
            "ok": bool,
            "address": str,
            "network": str,
            "coin": str | None,
            "orders": list[HistOrderDetail],
        }
    """
    return perp_get_hist_orders_impl(
        address=address,
        coin=coin,
        start_time=start_time,
        end_time=end_time,
        network=network,
    )


if __name__ == "__main__":
    from rich import print
    from dotenv import load_dotenv
    import os
    load_dotenv()
    EVM_ADDRESS = os.environ["EVM_ADDRESS"]

    print("=== 查 BTC 历史成交 ===")
    print(perp_get_hist_orders_impl(address=EVM_ADDRESS, coin="BTC", start_time=0))
    print()
    print("=== 查所有历史成交 ===")
    print(perp_get_hist_orders_impl(address=EVM_ADDRESS, start_time=0))
