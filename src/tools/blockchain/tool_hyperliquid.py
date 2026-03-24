from typing import Any, Literal

from hyperliquid.info import Info
from hyperliquid.utils import constants

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short"]
OrderType = Literal["market", "limit"]


def _get_base_url(network: Network) -> str:
    if network == "mainnet":
        return constants.MAINNET_API_URL
    if network == "testnet":
        return constants.TESTNET_API_URL
    raise ValueError(f"Unsupported network: {network}")


def _build_info(network: Network = "mainnet", timeout: float | None = None) -> Info:
    # Tools should avoid long-lived side effects, so default to HTTP-only mode.
    if network == "testnet":
        # Testnet spot metadata can be temporarily inconsistent and trigger
        # index errors in SDK initialization. Empty spot metadata keeps query
        # endpoints usable (e.g., user_state / open_orders / all_mids).
        return Info(
            _get_base_url(network),
            skip_ws=True,
            timeout=timeout,
            spot_meta={"universe": [], "tokens": []},
        )
    return Info(_get_base_url(network), skip_ws=True, timeout=timeout)


def get_user_state(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    info = _build_info(network, timeout=timeout)
    return info.user_state(address=address, dex=dex)


def get_open_orders(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> list[dict[str, Any]]:
    info = _build_info(network, timeout=timeout)
    return info.open_orders(address=address, dex=dex)


def get_all_mids(
    network: Network = "mainnet",
    dex: str = "",
    coin: str | None = None,
    timeout: float | None = None,
) -> dict[str, Any] | str | None:
    info = _build_info(network, timeout=timeout)
    mids = info.all_mids(dex=dex)
    if coin is None:
        return mids
    return mids.get(coin)


def get_meta(
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    info = _build_info(network, timeout=timeout)
    return info.meta(dex=dex)


def get_perp_mid_price(
    coin: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> str | None:
    return get_all_mids(network=network, dex=dex, coin=coin, timeout=timeout)


def get_perp_market_info(
    coin: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any] | None:
    meta = get_meta(network=network, dex=dex, timeout=timeout)
    for item in meta.get("universe", []):
        if item.get("name") == coin:
            return {
                "coin": coin,
                "listed": True,
                "max_leverage": item.get("maxLeverage"),
                "sz_decimals": item.get("szDecimals"),
                "is_delisted": item.get("isDelisted", False),
                "margin_table_id": item.get("marginTableId"),
            }
    return None


def is_perp_listed(
    coin: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> bool:
    return get_perp_market_info(coin, network=network, dex=dex, timeout=timeout) is not None


def validate_leverage(
    coin: str,
    leverage: float | int,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    market = get_perp_market_info(coin, network=network, dex=dex, timeout=timeout)
    if market is None:
        return {
            "ok": False,
            "reason": "coin_not_listed",
            "max_allowed": None,
            "requested": leverage,
        }

    max_allowed = market.get("max_leverage")
    if max_allowed is None:
        return {
            "ok": False,
            "reason": "max_leverage_unknown",
            "max_allowed": None,
            "requested": leverage,
        }

    lev = float(leverage)
    if lev <= 0:
        return {
            "ok": False,
            "reason": "invalid_leverage_non_positive",
            "max_allowed": max_allowed,
            "requested": leverage,
        }

    if lev > float(max_allowed):
        return {
            "ok": False,
            "reason": "leverage_too_high",
            "max_allowed": max_allowed,
            "requested": leverage,
        }

    return {
        "ok": True,
        "reason": "ok",
        "max_allowed": max_allowed,
        "requested": leverage,
    }


def evaluate_entry_price(
    coin: str,
    side: Side,
    target_price: float | int,
    order_type: OrderType = "limit",
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
    deviation_warn_ratio: float = 0.03,
) -> dict[str, Any]:
    mid_raw = get_perp_mid_price(coin=coin, network=network, dex=dex, timeout=timeout)
    if mid_raw is None:
        return {
            "ok": False,
            "reason": "price_unavailable",
            "coin": coin,
        }

    mid = float(mid_raw)
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


def validate_open_intent(
    intent: dict[str, Any],
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    missing_fields: list[str] = []
    required = ["coin", "side", "size"]
    for f in required:
        if intent.get(f) in (None, ""):
            missing_fields.append(f)

    if missing_fields:
        return {
            "ok": False,
            "missing_fields": missing_fields,
            "follow_up_question": f"请补充必要字段: {', '.join(missing_fields)}",
            "issues": [],
        }

    coin = str(intent["coin"]).upper()
    side = str(intent["side"]).lower()
    order_type = str(intent.get("order_type", "market")).lower()
    leverage = intent.get("leverage")
    entry_price = intent.get("entry_price")

    issues: list[dict[str, Any]] = []

    market = get_perp_market_info(coin=coin, network=network, dex=dex, timeout=timeout)
    if market is None:
        issues.append(
            {
                "code": "coin_not_listed",
                "message": f"{coin} 不在 Hyperliquid 永续列表中",
            }
        )

    if leverage is not None:
        lev_check = validate_leverage(coin=coin, leverage=leverage, network=network, dex=dex, timeout=timeout)
        if not lev_check["ok"]:
            issues.append(
                {
                    "code": lev_check["reason"],
                    "message": f"杠杆不合法，requested={lev_check['requested']} max={lev_check['max_allowed']}",
                    "detail": lev_check,
                }
            )

    if entry_price is not None and side in ("long", "short") and order_type in ("market", "limit"):
        px_check = evaluate_entry_price(
            coin=coin,
            side=side,
            target_price=float(entry_price),
            order_type=order_type,
            network=network,
            dex=dex,
            timeout=timeout,
        )
        if px_check.get("ok"):
            if order_type == "limit" and not px_check["direction_ok_for_limit"]:
                issues.append(
                    {
                        "code": "limit_price_direction_unusual",
                        "message": "该限价方向与常见开仓方向不一致，可能会立即成交或长期不成交",
                        "detail": px_check,
                    }
                )
            if px_check["deviation_warn"]:
                issues.append(
                    {
                        "code": "entry_price_far_from_market",
                        "message": "目标价与当前中间价偏差较大",
                        "detail": px_check,
                    }
                )
        else:
            issues.append(
                {
                    "code": "price_check_failed",
                    "message": "无法完成价格校验",
                    "detail": px_check,
                }
            )

    normalized_intent = {
        "coin": coin,
        "side": side if side in ("long", "short") else None,
        "size": intent["size"],
        "order_type": order_type if order_type in ("market", "limit") else None,
        "leverage": leverage,
        "entry_price": entry_price,
    }

    follow_up_question = ""
    if normalized_intent["side"] is None:
        follow_up_question = "请确认方向：`long` 还是 `short`？"
    elif normalized_intent["order_type"] is None:
        follow_up_question = "请确认下单类型：`market` 还是 `limit`？"
    elif normalized_intent["order_type"] == "limit" and normalized_intent["entry_price"] is None:
        follow_up_question = "你是限价单，请补充 `entry_price`。"

    return {
        "ok": len(issues) == 0 and follow_up_question == "",
        "missing_fields": [],
        "follow_up_question": follow_up_question,
        "issues": issues,
        "normalized_intent": normalized_intent,
    }


def get_perp_positions(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    state = get_user_state(address=address, network=network, dex=dex, timeout=timeout)
    mids = get_all_mids(network=network, dex=dex, timeout=timeout)

    result_positions: list[dict[str, Any]] = []
    for item in state.get("assetPositions", []):
        position = item.get("position", {})
        coin = position.get("coin")
        size = position.get("szi")
        if not coin or size in (None, "0", "0.0", 0):
            continue

        result_positions.append(
            {
                "coin": coin,
                "size": size,
                "entry_px": position.get("entryPx"),
                "mark_px": mids.get(coin) if isinstance(mids, dict) else None,
                "position_value": position.get("positionValue"),
                "unrealized_pnl": position.get("unrealizedPnl"),
                "leverage": position.get("leverage", {}).get("value"),
                "margin_type": position.get("leverage", {}).get("type"),
                "liquidation_px": position.get("liquidationPx"),
            }
        )

    return {
        "address": address,
        "network": network,
        "dex": dex,
        "account_value": state.get("marginSummary", {}).get("accountValue"),
        "withdrawable": state.get("withdrawable"),
        "positions": result_positions,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Hyperliquid perp query helper.")
    parser.add_argument(
        "--action",
        choices=["price", "positions", "validate_intent", "market_info"],
        required=True,
        help=(
            "price: query one coin perp mid price; "
            "positions: query account perp positions; "
            "market_info: query one coin listing + leverage rules; "
            "validate_intent: validate open-position intent."
        ),
    )
    parser.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    parser.add_argument("--dex", default="", help="Optional DEX/deployer address for perp dex.")
    parser.add_argument("--coin", default="BTC", help="Coin symbol for perp price query.")
    parser.add_argument(
        "--address",
        default="",
        help="Wallet address for positions query.",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--raw", action="store_true", help="Print raw JSON without simplified display.")
    parser.add_argument("--side", choices=["long", "short"], default="long")
    parser.add_argument("--size", type=float, default=0.0)
    parser.add_argument("--entry-price", type=float, default=None)
    parser.add_argument("--order-type", choices=["market", "limit"], default="market")
    parser.add_argument("--leverage", type=float, default=None)
    args = parser.parse_args()

    if args.action == "price":
        price = get_perp_mid_price(
            coin=args.coin,
            network=args.network,
            dex=args.dex,
            timeout=args.timeout,
        )
        if args.raw:
            print(json.dumps({"coin": args.coin, "mid_price": price}, ensure_ascii=False, indent=2))
        else:
            print(f"{args.coin} perp mid price ({args.network}): {price}")

    if args.action == "positions":
        if not args.address:
            raise ValueError("positions action requires --address")

        positions = get_perp_positions(
            address=args.address,
            network=args.network,
            dex=args.dex,
            timeout=args.timeout,
        )
        if args.raw:
            print(json.dumps(positions, ensure_ascii=False, indent=2))
        else:
            print(f"address: {positions['address']}")
            print(f"network: {positions['network']}")
            print(f"account_value: {positions['account_value']}")
            print(f"withdrawable: {positions['withdrawable']}")
            print(f"open_positions: {len(positions['positions'])}")
            for p in positions["positions"]:
                print(
                    f"- {p['coin']}: size={p['size']} entry={p['entry_px']} mark={p['mark_px']} "
                    f"uPnL={p['unrealized_pnl']} liq={p['liquidation_px']}"
                )

    if args.action == "market_info":
        info = get_perp_market_info(
            coin=args.coin,
            network=args.network,
            dex=args.dex,
            timeout=args.timeout,
        )
        if args.raw:
            print(json.dumps(info, ensure_ascii=False, indent=2))
        else:
            if info is None:
                print(f"{args.coin} is not listed on Hyperliquid perp ({args.network}).")
            else:
                print(
                    f"{info['coin']} listed={info['listed']} max_leverage={info['max_leverage']} "
                    f"delisted={info['is_delisted']}"
                )

    if args.action == "validate_intent":
        payload = {
            "coin": args.coin,
            "side": args.side,
            "size": args.size,
            "entry_price": args.entry_price,
            "order_type": args.order_type,
            "leverage": args.leverage,
        }
        result = validate_open_intent(payload, network=args.network, dex=args.dex, timeout=args.timeout)
        if args.raw:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"intent_ok: {result['ok']}")
            if result["follow_up_question"]:
                print(f"follow_up: {result['follow_up_question']}")
            print(f"issues: {len(result['issues'])}")
            for i in result["issues"]:
                print(f"- {i['code']}: {i['message']}")
