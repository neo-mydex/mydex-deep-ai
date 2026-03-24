"""
开仓前检查模块（公开）
"""

from typing import Any, Literal

from src.tools.perp.get_market import get_coin_info, get_market_price
from src.tools.perp.get_open_orders import get_user_open_orders
from src.tools.perp.get_positions import get_user_position
from src.tools.perp.get_user_state import get_account_balance
from src.tools.perp._normalize_intent import normalize_intent

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short"]
OrderType = Literal["market", "limit"]


def validate_leverage(
    coin: str,
    leverage: float | int,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """验证杠杆是否合法。"""
    coin_info = get_coin_info(coin=coin, network=network, timeout=timeout)

    if not coin_info["ok"] or not coin_info["is_listed"]:
        return {
            "ok": False,
            "coin": coin,
            "requested": leverage,
            "max_allowed": None,
            "reason": "coin_not_listed",
        }

    max_leverage = coin_info.get("max_leverage")
    if max_leverage is None:
        return {
            "ok": False,
            "coin": coin,
            "requested": leverage,
            "max_allowed": None,
            "reason": "max_leverage_unknown",
        }

    lev = float(leverage)
    if lev <= 0:
        return {
            "ok": False,
            "coin": coin,
            "requested": leverage,
            "max_allowed": max_leverage,
            "reason": "invalid_leverage_non_positive",
        }

    if lev > float(max_leverage):
        return {
            "ok": False,
            "coin": coin,
            "requested": leverage,
            "max_allowed": max_leverage,
            "reason": "leverage_too_high",
        }

    return {
        "ok": True,
        "coin": coin,
        "requested": leverage,
        "max_allowed": max_leverage,
        "reason": "ok",
    }


def evaluate_entry_price(
    coin: str,
    side: Side,
    target_price: float | int,
    order_type: OrderType,
    network: Network = "mainnet",
    timeout: float | None = None,
    deviation_warn_ratio: float = 0.03,
) -> dict[str, Any]:
    """评估限价开仓价格是否合理。"""
    market_price = get_market_price(coin=coin, network=network, timeout=timeout)

    if not market_price["ok"] or market_price["mark_price"] is None:
        return {
            "ok": False,
            "coin": coin,
            "side": side,
            "order_type": order_type,
            "target_price": float(target_price),
            "mid_price": None,
            "deviation_ratio": None,
            "deviation_warn": False,
            "direction_ok_for_limit": False,
            "would_fill_immediately": False,
            "reason": "price_unavailable",
        }

    mid = market_price["mark_price"]
    target = float(target_price)
    deviation_ratio = abs(target - mid) / mid if mid > 0 else 0.0

    if order_type == "market":
        direction_ok = True
        would_fill_now = True
    elif side == "long":
        direction_ok = target <= mid
        would_fill_now = target >= mid
    else:
        direction_ok = target >= mid
        would_fill_now = target <= mid

    return {
        "ok": True,
        "coin": coin,
        "side": side,
        "order_type": order_type,
        "target_price": target,
        "mid_price": mid,
        "deviation_ratio": deviation_ratio,
        "deviation_warn": deviation_ratio >= deviation_warn_ratio,
        "direction_ok_for_limit": direction_ok,
        "would_fill_immediately": would_fill_now,
    }


def _check_can_open_with_intent(
    intent: dict[str, Any],
    address: str,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    follow_up_parts: list[str] = []

    intent_result = normalize_intent(intent)
    normalized = intent_result["normalized"]

    if not intent_result["ok"]:
        missing = intent_result["missing_fields"]
        if missing:
            follow_up_parts.append(f"请补充必要字段: {', '.join(missing)}")
        for field in intent_result["invalid_fields"]:
            issues.append({
                "code": f"invalid_{field}",
                "message": f"字段 {field} 无效或格式错误",
                "detail": {},
            })

    if normalized["coin"] is None or normalized["side"] is None or normalized["size"] is None:
        return {
            "ok": False,
            "missing_fields": intent_result["missing_fields"],
            "follow_up_question": " ".join(follow_up_parts),
            "issues": issues,
            "checks": {},
            "normalized_intent": normalized,
        }

    coin = normalized["coin"]
    side = normalized["side"]
    leverage = normalized["leverage"]
    order_type = normalized["order_type"]
    entry_price = normalized["entry_price"]

    balance_check = get_account_balance(
        address=address,
        network=network,
        timeout=timeout,
    )
    if balance_check["withdrawable"] <= 0:
        issues.append({
            "code": "no_balance",
            "message": "账户无可用余额",
            "detail": balance_check,
        })

    position_check = get_user_position(
        address=address,
        coin=coin,
        network=network,
        timeout=timeout,
    )
    if position_check["has_position"]:
        existing_side = position_check["position_side"]
        if existing_side == side:
            issues.append({
                "code": "position_exists_same_direction",
                "message": f"已有 {coin} 的 {side} 仓位，不能同向加仓",
                "detail": position_check,
            })
        else:
            issues.append({
                "code": "position_exists_opposite_direction",
                "message": f"已有 {coin} 的反向仓位({existing_side})，需要先平仓才能开新仓位",
                "detail": position_check,
            })

    coin_info_check = get_coin_info(
        coin=coin,
        network=network,
        timeout=timeout,
    )
    if not coin_info_check["ok"] or not coin_info_check["is_listed"]:
        issues.append({
            "code": "coin_not_listed",
            "message": f"{coin} 不在 Hyperliquid 永续合约列表中",
            "detail": coin_info_check,
        })

    leverage_check = {"ok": True}
    if leverage is not None and coin_info_check.get("is_listed"):
        leverage_check = validate_leverage(
            coin=coin,
            leverage=leverage,
            network=network,
            timeout=timeout,
        )
        if not leverage_check["ok"]:
            issues.append({
                "code": leverage_check["reason"],
                "message": (
                    f"杠杆不合法: requested={leverage_check['requested']}, "
                    f"max={leverage_check['max_allowed']}"
                ),
                "detail": leverage_check,
            })

    open_orders_check = get_user_open_orders(
        address=address,
        coin=coin,
        network=network,
        timeout=timeout,
    )

    entry_price_check = {"ok": True}
    if order_type == "limit" and entry_price is not None:
        entry_price_check = evaluate_entry_price(
            coin=coin,
            side=side,
            target_price=entry_price,
            order_type=order_type,
            network=network,
            timeout=timeout,
        )
        if not entry_price_check["ok"]:
            issues.append({
                "code": "price_unavailable",
                "message": "无法获取市场价格",
                "detail": entry_price_check,
            })
        else:
            if not entry_price_check["direction_ok_for_limit"]:
                issues.append({
                    "code": "limit_price_direction_unusual",
                    "message": "限价方向与常见开仓方向不一致，可能会立即成交或长期不成交",
                    "detail": entry_price_check,
                })
            if entry_price_check["deviation_warn"]:
                issues.append({
                    "code": "entry_price_far_from_market",
                    "message": f"目标价与当前市场价偏差 {entry_price_check['deviation_ratio']:.2%}",
                    "detail": entry_price_check,
                })

    if normalized["side"] is None:
        follow_up_parts.append("请确认方向：long 还是 short？")
    if normalized["order_type"] is None:
        follow_up_parts.append("请确认订单类型：market 还是 limit？")
    elif normalized["order_type"] == "limit" and normalized["entry_price"] is None:
        follow_up_parts.append("限价单请补充 entry_price")

    return {
        "ok": len(issues) == 0,
        "missing_fields": intent_result["missing_fields"],
        "follow_up_question": " ".join(follow_up_parts),
        "issues": issues,
        "checks": {
            "intent": intent_result,
            "balance": balance_check,
            "position": position_check,
            "market": coin_info_check,
            "leverage": leverage_check,
            "open_orders": open_orders_check,
            "entry_price": entry_price_check,
        },
        "normalized_intent": normalized,
    }


def check_can_open(
    address: str,
    coin: str | None = None,
    side: Side | None = None,
    size: float | None = None,
    leverage: float | None = None,
    order_type: OrderType = "market",
    entry_price: float | None = None,
    network: Network = "mainnet",
    timeout: float | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    检查是否可以开仓（公开接口）

    支持两种调用方式：
    1. 显式参数：address + coin + side + size...
    2. 意图参数：intent + address（兼容旧调用）
    """
    if intent is None:
        intent = {
            "coin": coin,
            "side": side,
            "size": size,
            "leverage": leverage,
            "order_type": order_type,
            "entry_price": entry_price,
        }
    return _check_can_open_with_intent(
        intent=intent,
        address=address,
        network=network,
        timeout=timeout,
    )


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="检查是否可以开仓")
    parser.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    parser.add_argument("--address", required=True)
    parser.add_argument("--coin", required=True)
    parser.add_argument("--side", choices=["long", "short"], required=True)
    parser.add_argument("--size", type=float, required=True)
    parser.add_argument("--leverage", type=float, default=None)
    parser.add_argument("--order-type", choices=["market", "limit"], default="market")
    parser.add_argument("--entry-price", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    result = check_can_open(
        address=args.address,
        coin=args.coin,
        side=args.side,
        size=args.size,
        leverage=args.leverage,
        order_type=args.order_type,
        entry_price=args.entry_price,
        network=args.network,
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

