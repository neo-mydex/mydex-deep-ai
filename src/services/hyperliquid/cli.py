"""
Hyperliquid 业务层函数 + CLI 入口

所有函数都是纯业务逻辑，不含 @tool 装饰器。
"""

from typing import Any

from typing import Literal

from .info import (
    Network,
    _build_info,
    get_all_mids,
    get_meta,
    get_meta_and_asset_ctxs,
    user_state,
    open_orders,
    frontend_open_orders,
    user_fills_by_time,
    query_order_by_oid,
)
from .normalize import (
    normalize_intent,
    Side,
    OrderType,
)


def get_perp_market_info(
    coin: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any] | None:
    """
    获取某个币的永续市场信息

    返回结构:
    {
        "coin": str,
        "listed": bool,
        "max_leverage": int | None,
        "sz_decimals": int,
        "is_delisted": bool,
        "only_isolated": bool,
        "margin_table_id": int | None,
    }
    """
    meta = get_meta(network=network, dex=dex, timeout=timeout)
    for item in meta.get("universe", []):
        if item.get("name") == coin:
            return {
                "coin": coin,
                "listed": True,
                "max_leverage": item.get("maxLeverage"),
                "sz_decimals": item.get("szDecimals"),
                "is_delisted": item.get("isDelisted", False),
                "only_isolated": item.get("onlyIsolated", False),
                "margin_table_id": item.get("marginTableId"),
            }
    return None


def is_perp_listed(
    coin: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> bool:
    """检查币种是否在永续合约列表中"""
    return get_perp_market_info(coin, network=network, dex=dex, timeout=timeout) is not None


def get_market_price(
    coin: str,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取市场当前价格（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "network": str,
        "coin": str,
        "mark_price": float | None,
        "mark_price_raw": str | None,
        "is_listed": bool,
    }
    """
    mids = get_all_mids(network=network, timeout=timeout)
    mark_price_raw = mids.get(coin)
    mark_price = None
    if mark_price_raw is not None:
        try:
            mark_price = float(mark_price_raw)
        except (TypeError, ValueError):
            mark_price = None

    return {
        "ok": mark_price is not None,
        "network": network,
        "coin": coin,
        "mark_price": mark_price,
        "mark_price_raw": mark_price_raw,
        "is_listed": mark_price_raw is not None,
    }


def get_coin_info(
    coin: str,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取币种详细信息（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "coin": str,
        "network": str,
        "is_listed": bool,
        "max_leverage": int | None,
        "only_isolated": bool,
        "sz_decimals": int | None,
    }
    """
    info = get_perp_market_info(coin, network=network, timeout=timeout)
    if info is None:
        return {
            "ok": False,
            "coin": coin,
            "network": network,
            "is_listed": False,
            "max_leverage": None,
            "only_isolated": False,
            "sz_decimals": None,
        }

    return {
        "ok": True,
        "coin": coin,
        "network": network,
        "is_listed": True,
        "max_leverage": info.get("max_leverage"),
        "only_isolated": info.get("only_isolated", False),
        "sz_decimals": info.get("sz_decimals"),
    }


def get_account_balance(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取账户余额信息（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "address": str,
        "network": str,
        "withdrawable": float,
        "account_value": float | None,
        "total_margin_used": float | None,
    }
    """
    state = user_state(address=address, network=network, dex=dex, timeout=timeout)

    withdrawable = state.get("withdrawable", "0")
    try:
        withdrawable_val = float(withdrawable)
    except (TypeError, ValueError):
        withdrawable_val = 0.0

    margin_summary = state.get("marginSummary", {})
    account_value = margin_summary.get("accountValue")
    if account_value is not None:
        try:
            account_value = float(account_value)
        except (TypeError, ValueError):
            account_value = None

    total_margin_used = margin_summary.get("totalMarginUsed")
    if total_margin_used is not None:
        try:
            total_margin_used = float(total_margin_used)
        except (TypeError, ValueError):
            total_margin_used = None

    return {
        "ok": True,
        "address": address,
        "network": network,
        "withdrawable": withdrawable_val,
        "account_value": account_value,
        "total_margin_used": total_margin_used,
    }


def get_user_positions(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取用户所有永续仓位（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "address": str,
        "network": str,
        "account_value": float | None,
        "withdrawable": float,
        "positions": [
            {
                "coin": str,
                "size": float,
                "side": "long" | "short" | "flat",
                "entry_px": float | None,
                "mark_px": float | None,
                "position_value": float | None,
                "unrealized_pnl": float | None,
                "leverage": int | None,
                "margin_type": "cross" | "isolated" | None,
                "liquidation_px": float | None,
            }
        ]
    }
    """
    state = user_state(address=address, network=network, dex=dex, timeout=timeout)
    mids = get_all_mids(network=network, dex=dex, timeout=timeout)

    result_positions: list[dict[str, Any]] = []
    for item in state.get("assetPositions", []):
        position = item.get("position", {})
        coin = position.get("coin")
        raw_size = position.get("szi")

        if not coin or raw_size is None:
            continue

        try:
            size = float(raw_size)
        except (TypeError, ValueError):
            continue

        # 判断方向
        if size > 0:
            side = "long"
        elif size < 0:
            side = "short"
        else:
            side = "flat"

        # 跳过 0 仓位
        if size == 0:
            continue

        # 获取当前市价
        mark_px_raw = mids.get(coin) if isinstance(mids, dict) else None
        try:
            mark_px = float(mark_px_raw) if mark_px_raw else None
        except (TypeError, ValueError):
            mark_px = None

        # 获取入场价
        entry_px_raw = position.get("entryPx")
        try:
            entry_px = float(entry_px_raw) if entry_px_raw else None
        except (TypeError, ValueError):
            entry_px = None

        # 获取强平价格
        liq_px_raw = position.get("liquidationPx")
        try:
            liquidation_px = float(liq_px_raw) if liq_px_raw else None
        except (TypeError, ValueError):
            liquidation_px = None

        # 获取保证金信息
        leverage_obj = position.get("leverage", {})
        leverage_val = leverage_obj.get("value") if isinstance(leverage_obj, dict) else None
        margin_type = leverage_obj.get("type") if isinstance(leverage_obj, dict) else None

        result_positions.append({
            "coin": coin,
            "size": size,
            "side": side,
            "entry_px": entry_px,
            "mark_px": mark_px,
            "position_value": position.get("positionValue"),
            "unrealized_pnl": position.get("unrealizedPnl"),
            "leverage": leverage_val,
            "margin_type": margin_type,
            "liquidation_px": liquidation_px,
        })

    # 账户价值
    margin_summary = state.get("marginSummary", {})
    account_value_raw = margin_summary.get("accountValue")
    try:
        account_value = float(account_value_raw) if account_value_raw else None
    except (TypeError, ValueError):
        account_value = None

    withdrawable_raw = state.get("withdrawable")
    try:
        withdrawable = float(withdrawable_raw) if withdrawable_raw else 0.0
    except (TypeError, ValueError):
        withdrawable = 0.0

    return {
        "ok": True,
        "address": address,
        "network": network,
        "account_value": account_value,
        "withdrawable": withdrawable,
        "positions": result_positions,
    }


def get_user_position(
    address: str,
    coin: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取用户指定币的仓位（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "address": str,
        "coin": str,
        "network": str,
        "has_position": bool,
        "position_side": "long" | "short" | "flat",
        "position_size": float | None,
        "entry_px": float | None,
        "mark_px": float | None,
        "leverage": int | None,
        "margin_type": "cross" | "isolated" | None,
        "liquidation_px": float | None,
        "unrealized_pnl": float | None,
    }
    """
    positions_data = get_user_positions(
        address=address,
        network=network,
        dex=dex,
        timeout=timeout,
    )

    matched_position = None
    for p in positions_data.get("positions", []):
        if p["coin"] == coin:
            matched_position = p
            break

    if matched_position is None:
        return {
            "ok": True,
            "address": address,
            "coin": coin,
            "network": network,
            "has_position": False,
            "position_side": "flat",
            "position_size": None,
            "entry_px": None,
            "mark_px": None,
            "leverage": None,
            "margin_type": None,
            "liquidation_px": None,
            "unrealized_pnl": None,
        }

    return {
        "ok": True,
        "address": address,
        "coin": coin,
        "network": network,
        "has_position": matched_position["size"] != 0,
        "position_side": matched_position["side"],
        "position_size": matched_position["size"],
        "entry_px": matched_position["entry_px"],
        "mark_px": matched_position["mark_px"],
        "leverage": matched_position["leverage"],
        "margin_type": matched_position["margin_type"],
        "liquidation_px": matched_position["liquidation_px"],
        "unrealized_pnl": matched_position["unrealized_pnl"],
    }


def _is_tpsl_order(order: dict[str, Any]) -> bool:
    """判断是否为 TP/SL 止盈止损挂单"""
    if order.get("isPositionTpsl") is True:
        return True
    if order.get("triggerCondition") is not None:
        return True
    order_type = str(order.get("orderType", "")).lower()
    # 检查是否包含 TP/SL/Trigger 相关关键词
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
    orders = frontend_open_orders(
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


# ============================================================================
# 开仓/平仓检查
# ============================================================================


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
    检查是否可以开仓

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


# ============================================================================
# 历史成交与订单查询
# ============================================================================


def get_user_fills_by_time(
    address: str,
    start_time: int,
    end_time: int | None = None,
    aggregate_by_time: bool = False,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取用户历史成交记录（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "address": str,
        "network": str,
        "fills": [list of fill dicts from user_fills_by_time]
    }
    """
    fills = user_fills_by_time(
        address=address,
        start_time=start_time,
        end_time=end_time,
        aggregate_by_time=aggregate_by_time,
        network=network,
        timeout=timeout,
    )
    return {
        "ok": True,
        "address": address,
        "network": network,
        "fills": fills if isinstance(fills, list) else [],
    }


def get_order_detail_by_oid(
    address: str,
    oid: int,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    根据 oid 查询订单详情（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "oid": int,
        "coin": str | None,
        "side": str | None,
        "sz": str | None,
        "px": str | None,
        "orderType": str | None,
        "reduceOnly": bool | None,
        "timestamp": int | None,
        "closedPnl": str | None,
    }
    """
    raw = query_order_by_oid(address=address, oid=oid, network=network, timeout=timeout)
    if raw is None:
        return {"ok": False, "oid": oid}
    return {"ok": True, **raw}


