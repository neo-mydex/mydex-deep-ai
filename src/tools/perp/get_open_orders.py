"""
用户挂单查询模块
"""

from typing import Any

from src.tools.perp._hyperliquid_info import Network, _build_info


def get_open_orders(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> list[dict[str, Any]]:
    """
    获取用户所有挂单（原始数据）

    返回结构:
    [
        {
            "coin": str,
            "limitPx": str,
            "oid": int,
            "side": "A" | "B",
            "sz": str,
            "timestamp": int,
        }
    ]
    """
    info = _build_info(network, timeout=timeout)
    return info.open_orders(address=address, dex=dex)


def get_frontend_open_orders(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> list[dict[str, Any]]:
    """
    获取用户挂单（含 TP/SL 等前端信息）

    返回结构:
    [
        {
            "coin": str,
            "isPositionTpsl": bool,
            "isTrigger": bool,
            "orderType": str,
            "reduceOnly": bool,
            "side": "A" | "B",
            "sz": str,
            "limitPx": str,
            "oid": int,
            "triggerCondition": str | None,
            "triggerPx": str | None,
            ...
        }
    ]
    """
    info = _build_info(network, timeout=timeout)
    result = info.frontend_open_orders(address=address, dex=dex)
    return result if isinstance(result, list) else []


def _is_tpsl_order(order: dict[str, Any]) -> bool:
    """判断是否为 TP/SL 止盈止损挂单"""
    if order.get("isPositionTpsl") is True:
        return True
    if order.get("triggerCondition") is not None:
        return True
    order_type = str(order.get("orderType", "")).lower()
    # 检查是否包含 TP/SL/Trigger 相关关键词
    # 支持非连续匹配（如 TakeProfitMarket 中含 tp）
    tpsl_keywords = ["takeprofit", "stoploss", "trigger"]
    for keyword in tpsl_keywords:
        if keyword in order_type:
            return True
    if order.get("triggerPx") is not None:
        return True
    return False


def get_user_open_orders(
    address: str,
    coin: str | None = None,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取用户挂单（给 Agent 用的标准化返回）

    参数:
        coin: 如果不传，则返回所有币的挂单

    返回结构:
    {
        "ok": bool,
        "address": str,
        "network": str,
        "coin": str | None,
        "has_open_orders": bool,
        "open_order_count": int,
        "has_tpsl_orders": bool,
        "tpsl_order_count": int,
        "orders": [...],  # 原始订单列表
    }
    """
    orders = get_frontend_open_orders(
        address=address,
        network=network,
        dex=dex,
        timeout=timeout,
    )

    # 如果指定了 coin，则过滤
    if coin is not None:
        orders = [o for o in orders if o.get("coin") == coin]

    tpsl_orders = [o for o in orders if _is_tpsl_order(o)]

    return {
        "ok": True,
        "address": address,
        "network": network,
        "coin": coin,
        "has_open_orders": len(orders) > 0,
        "open_order_count": len(orders),
        "has_tpsl_orders": len(tpsl_orders) > 0,
        "tpsl_order_count": len(tpsl_orders),
        "orders": orders,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Hyperliquid 挂单查询")
    parser.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    parser.add_argument("--address", required=True)
    parser.add_argument("--coin", default=None, help="不传则查所有币")
    parser.add_argument("--dex", default="")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    result = get_user_open_orders(
        address=args.address,
        coin=args.coin,
        network=args.network,
        dex=args.dex,
        timeout=args.timeout,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
