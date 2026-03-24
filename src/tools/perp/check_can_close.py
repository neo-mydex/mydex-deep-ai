"""
平仓前检查模块（公开）
"""

from typing import Any, Literal

from src.tools.perp.get_positions import get_user_position
from src.tools.perp.get_open_orders import get_user_open_orders
from src.tools.perp.get_market import get_market_price

Network = Literal["mainnet", "testnet"]


def check_can_close(
    address: str,
    coin: str,
    close_size: float | None = None,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """核心检查：验证用户是否可以平仓。"""
    issues: list[dict[str, Any]] = []
    follow_up_parts: list[str] = []

    position_check = get_user_position(
        address=address,
        coin=coin,
        network=network,
        timeout=timeout,
    )

    if not position_check["ok"]:
        issues.append({
            "code": "query_failed",
            "message": "查询仓位失败",
            "detail": position_check,
        })
        return {
            "ok": False,
            "follow_up_question": "查询失败，请稍后重试",
            "issues": issues,
            "checks": {"position": position_check},
            "position_info": None,
        }

    if not position_check["has_position"]:
        issues.append({
            "code": "no_position",
            "message": f"没有 {coin} 的仓位，无需平仓",
            "detail": position_check,
        })

    open_orders_check = get_user_open_orders(
        address=address,
        coin=coin,
        network=network,
        timeout=timeout,
    )
    if open_orders_check["has_open_orders"]:
        issues.append({
            "code": "has_open_orders",
            "message": f"有 {open_orders_check['open_order_count']} 个 {coin} 挂单，请先撤销",
            "detail": open_orders_check,
        })

    market_check = get_market_price(
        coin=coin,
        network=network,
        timeout=timeout,
    )
    if not market_check["ok"] or market_check["mark_price"] is None:
        issues.append({
            "code": "price_unavailable",
            "message": "无法获取市场价格",
            "detail": market_check,
        })

    position_size = position_check.get("position_size") or 0
    if close_size is None:
        actual_close_size = abs(position_size)
    else:
        try:
            actual_close_size = float(close_size)
            if actual_close_size <= 0:
                follow_up_parts.append("平仓数量必须 > 0")
                actual_close_size = abs(position_size)
            elif position_size != 0 and actual_close_size > abs(position_size):
                follow_up_parts.append(f"平仓数量不能超过持仓量({abs(position_size)})，将全平")
                actual_close_size = abs(position_size)
        except (TypeError, ValueError):
            actual_close_size = abs(position_size)

    if actual_close_size > 0 and position_check["has_position"]:
        liq_px = position_check.get("liquidation_px")
        mark_px = market_check.get("mark_price")

        if liq_px is not None and mark_px is not None:
            position_side = position_check["position_side"]

            if position_side == "long":
                distance_ratio = (mark_px - liq_px) / mark_px if mark_px > 0 else None
            else:
                distance_ratio = (liq_px - mark_px) / mark_px if mark_px > 0 else None

            if distance_ratio is not None and distance_ratio < 0.1:
                issues.append({
                    "code": "near_liquidation",
                    "message": f"仓位接近强平价格，距离 {distance_ratio:.1%}",
                    "detail": {
                        "liquidation_px": liq_px,
                        "mark_px": mark_px,
                        "distance_ratio": distance_ratio,
                    },
                })

    return {
        "ok": len(issues) == 0,
        "follow_up_question": " ".join(follow_up_parts),
        "issues": issues,
        "checks": {
            "position": position_check,
            "open_orders": open_orders_check,
            "market": market_check,
        },
        "position_info": {
            "has_position": position_check["has_position"],
            "position_side": position_check["position_side"],
            "position_size": position_check["position_size"],
            "close_size": actual_close_size,
        },
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="检查是否可以平仓")
    parser.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    parser.add_argument("--address", required=True)
    parser.add_argument("--coin", default="BTC")
    parser.add_argument("--close-size", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    result = check_can_close(
        address=args.address,
        coin=args.coin,
        close_size=args.close_size,
        network=args.network,
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

