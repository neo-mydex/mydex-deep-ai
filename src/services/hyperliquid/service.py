"""
Hyperliquid 业务层函数

所有函数都是纯业务逻辑，不含 @tool 装饰器，返回 {"ok": bool, ...} 结构。
"""

from typing import Any, Literal

from .client import (
    Network,
    get_all_mids,
    get_meta,
    get_meta_and_asset_ctxs,
    user_state,
    open_orders,
    frontend_open_orders,
    user_fills_by_time,
    query_order_by_oid,
    historical_orders,
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
    """获取某个币的永续市场信息"""
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
    """获取市场当前价格（给 Agent 用的标准化返回）"""
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
    """获取币种详细信息（给 Agent 用的标准化返回）"""
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
    """获取账户余额信息（给 Agent 用的标准化返回）"""
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
    """获取用户所有永续仓位（给 Agent 用的标准化返回）"""
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

        if size > 0:
            side = "long"
        elif size < 0:
            side = "short"
        else:
            side = "flat"

        if size == 0:
            continue

        mark_px_raw = mids.get(coin) if isinstance(mids, dict) else None
        try:
            mark_px = float(mark_px_raw) if mark_px_raw else None
        except (TypeError, ValueError):
            mark_px = None

        entry_px_raw = position.get("entryPx")
        try:
            entry_px = float(entry_px_raw) if entry_px_raw else None
        except (TypeError, ValueError):
            entry_px = None

        liq_px_raw = position.get("liquidationPx")
        try:
            liquidation_px = float(liq_px_raw) if liq_px_raw else None
        except (TypeError, ValueError):
            liquidation_px = None

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
    """获取用户指定币的仓位（给 Agent 用的标准化返回）"""
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
    """获取用户挂单（给 Agent 用的标准化返回）"""
    orders = frontend_open_orders(
        address=address,
        network=network,
        dex=dex,
        timeout=timeout,
    )

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
    """验证杠杆是否合法"""
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
    """评估限价开仓价格是否合理"""
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
    address: str,
    coin: str,
    side: str,
    usdc_margin: float | None,
    coin_size: float | None,
    leverage: float | None,
    order_type: str,
    entry_price: float | None,
    network: Network,
    timeout: float | None,
) -> dict[str, Any]:
    """开仓前可行性校验，返回精简结果"""
    issues: list[dict[str, Any]] = []
    corrections: list[str] = []

    if not coin or not side or leverage is None:
        return {
            "ok": False,
            "is_adding": False,
            "leverage_to_use": None,
            "coin_size": None,
            "usdc_margin": None,
            "corrections": [],
            "follow_up_question": "请提供完整的开仓参数（coin、side、leverage）",
            "issues": [{"code": "missing_params", "message": "参数不全"}],
        }

    # 获取市场数据（用于计算）
    market_price_data = get_market_price(coin=coin, network=network, timeout=timeout)
    mark_price = market_price_data.get("mark_price")

    # 1. 计算保证金和头寸
    #    - 有 usdc_margin: size = margin * leverage / price
    #    - 有 coin_size: margin = size * price / leverage
    #    - 只有单输入时保留原始值，不做换算（recalculation 仅在双输入时需要）
    user_provided_both = usdc_margin is not None and coin_size is not None
    coin_size_val: float | None = None
    usdc_margin_val: float | None = None

    if user_provided_both and mark_price and mark_price > 0:
        # 双输入时以 coin_size 为主（仓位是用户实际想要的）
        coin_size_val = coin_size
        usdc_margin_val = round(coin_size * mark_price / leverage, 6)
    elif usdc_margin is not None and mark_price and mark_price > 0:
        usdc_margin_val = usdc_margin
    elif coin_size is not None and mark_price and mark_price > 0:
        coin_size_val = coin_size

    # 2. 余额检查
    balance_check = get_account_balance(
        address=address, network=network, timeout=timeout,
    )
    if usdc_margin_val is not None and balance_check["withdrawable"] < usdc_margin_val:
        issues.append({
            "code": "no_balance",
            "message": f"可用余额 {balance_check['withdrawable']:.2f} USDC，不足 {usdc_margin_val:.2f} USDC",
        })

    # 3. 仓位检查
    position_check = get_user_position(
        address=address, coin=coin, network=network, timeout=timeout,
    )
    has_position = position_check.get("has_position", False)
    existing_side = position_check.get("position_side")

    is_adding = False
    leverage_to_use = float(leverage)

    if has_position and existing_side == side:
        # 同向仓位 → 补仓，杠杆必须和已有仓位一致
        is_adding = True
        existing_leverage = position_check.get("leverage")
        if existing_leverage is not None:
            leverage_to_use = float(existing_leverage)
            if leverage != leverage_to_use:
                corrections.append(f"杠杆已纠正为 {leverage_to_use}x（与已有仓位一致）")
                corrections.append(f"如需使用 {leverage_to_use}x 以外的杠杆，请先平仓再重新开仓")
            # 补仓时重新计算 coin_size（保证金保留用户原始值）
            if usdc_margin_val is not None and mark_price and mark_price > 0:
                # 单输入 usdc_margin：保持原始保证金，杠杆变化自动改变仓位
                coin_size_val = round(usdc_margin_val * leverage_to_use / mark_price, 6)
            elif coin_size is not None and usdc_margin_val is None and mark_price and mark_price > 0:
                # 单输入 coin_size：保持原始仓位，杠杆变化自动改变保证金
                usdc_margin_val = round(coin_size * mark_price / leverage_to_use, 6)
    elif has_position and existing_side != side:
        # 反向仓位 → 报错
        issues.append({
            "code": "opposite_position_exists",
            "message": f"已有 {coin} {existing_side} 仓位，需先平仓再开仓",
        })

    # 4. 币种和杠杆检查
    coin_info = get_coin_info(coin=coin, network=network, timeout=timeout)
    if not coin_info.get("is_listed"):
        issues.append({
            "code": "coin_not_listed",
            "message": f"{coin} 不在永续合约列表中",
        })

    if not is_adding and coin_info.get("is_listed"):
        max_leverage = coin_info.get("max_leverage")
        if max_leverage is not None and leverage > max_leverage:
            leverage_to_use = float(max_leverage)
            corrections.append(f"杠杆已从 {leverage}x 降为 {leverage_to_use}x（该币种最大 {max_leverage}x）")
            # 杠杆降低后，只有双输入时才换算；单输入保留原始值不动
            if user_provided_both and mark_price and mark_price > 0:
                if coin_size_val is not None:
                    usdc_margin_val = round(coin_size_val * mark_price / leverage_to_use, 6)
                elif usdc_margin_val is not None:
                    coin_size_val = round(usdc_margin_val * leverage_to_use / mark_price, 6)

    # 5. 未成交主单检查（TPSL 单不算）
    open_orders_result = get_user_open_orders(
        address=address, coin=coin, network=network, timeout=timeout,
    )
    main_orders = [
        o for o in open_orders_result.get("orders", [])
        if not _is_tpsl_order(o) and not o.get("reduceOnly", False)
    ]
    if main_orders:
        issues.append({
            "code": "has_main_orders",
            "message": f"有 {len(main_orders)} 个未成交主单，请先撤销",
        })

    # 6. 限价单价格校验
    if order_type == "limit" and entry_price is not None and mark_price:
        deviation = abs(entry_price - mark_price) / mark_price
        if deviation > 0.03:
            corrections.append(f"限价 {entry_price} 与市场价偏差 {deviation:.1%}，请确认价格")

    return {
        "ok": len(issues) == 0,
        "is_adding": is_adding,
        "leverage_to_use": leverage_to_use,
        "coin_size": coin_size_val,
        "usdc_margin": usdc_margin_val,
        "corrections": corrections,
        "follow_up_question": "",
        "issues": issues,
    }


def check_can_open(
    address: str,
    coin: str | None = None,
    side: Side | None = None,
    usdc_margin: float | None = None,
    coin_size: float | None = None,
    leverage: float | None = None,
    order_type: OrderType = "market",
    entry_price: float | None = None,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """检查是否可以开仓"""
    return _check_can_open_with_intent(
        address=address,
        coin=coin,
        side=side,
        usdc_margin=usdc_margin,
        coin_size=coin_size,
        leverage=leverage,
        order_type=order_type,
        entry_price=entry_price,
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
    """检查是否可以平仓"""
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
    """获取用户历史成交记录（给 Agent 用的标准化返回）"""
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
    """根据 oid 查询订单详情（给 Agent 用的标准化返回）"""
    raw = query_order_by_oid(address=address, oid=oid, network=network, timeout=timeout)
    if raw is None:
        return {"ok": False, "oid": oid}
    return {"ok": True, **raw}


def get_historical_orders(
    address: str,
    network: Network = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """获取用户历史订单（给 Agent 用的标准化返回）"""
    orders = historical_orders(address=address, network=network, timeout=timeout)
    return {
        "ok": True,
        "address": address,
        "network": network,
        "orders": orders,
    }
