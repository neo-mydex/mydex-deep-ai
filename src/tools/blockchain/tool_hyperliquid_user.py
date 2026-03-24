import json
import os
from typing import Any, Literal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from hyperliquid.utils import constants

Network = Literal["mainnet", "testnet"]


def _hyperliquid_info_url(network: Network) -> str:
    if network == "mainnet":
        return constants.MAINNET_API_URL + "/info"
    if network == "testnet":
        return constants.TESTNET_API_URL + "/info"
    raise ValueError(f"Unsupported network: {network}")


def _http_post_json(url: str, payload: dict[str, Any], timeout: float = 10.0) -> Any:
    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json", "accept": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_get_json(url: str, params: dict[str, Any], timeout: float = 10.0) -> Any:
    query = urlencode({k: v for k, v in params.items() if v not in (None, "")})
    request = Request(
        url=f"{url}?{query}" if query else url,
        headers={"accept": "application/json"},
        method="GET",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def query_clearinghouse_state(
    user_address: str,
    network: Network = "mainnet",
    timeout: float = 10.0,
) -> dict[str, Any]:
    payload = {"type": "clearinghouseState", "user": user_address}
    return _http_post_json(_hyperliquid_info_url(network), payload, timeout=timeout)


def query_frontend_open_orders(
    user_address: str,
    network: Network = "mainnet",
    timeout: float = 10.0,
) -> list[dict[str, Any]]:
    payload = {"type": "frontendOpenOrders", "user": user_address}
    result = _http_post_json(_hyperliquid_info_url(network), payload, timeout=timeout)
    return result if isinstance(result, list) else []


def query_all_mids(network: Network = "mainnet", timeout: float = 10.0) -> dict[str, str]:
    payload = {"type": "allMids"}
    result = _http_post_json(_hyperliquid_info_url(network), payload, timeout=timeout)
    return result if isinstance(result, dict) else {}


def check_user_position(
    user_address: str,
    coin: str,
    network: Network = "mainnet",
    timeout: float = 10.0,
) -> dict[str, Any]:
    state = query_clearinghouse_state(user_address=user_address, network=network, timeout=timeout)

    matched_position: dict[str, Any] | None = None
    for item in state.get("assetPositions", []):
        position = item.get("position", {})
        if position.get("coin") == coin:
            matched_position = position
            break

    size = None
    side = "flat"
    has_position = False
    if matched_position is not None:
        raw_size = matched_position.get("szi")
        try:
            size = float(raw_size)
            has_position = size != 0
            side = "long" if size > 0 else "short" if size < 0 else "flat"
        except (TypeError, ValueError):
            size = None

    return {
        "ok": True,
        "network": network,
        "user": user_address,
        "coin": coin,
        "withdrawable": state.get("withdrawable"),
        "account_value": state.get("marginSummary", {}).get("accountValue"),
        "has_position": has_position,
        "position_side": side,
        "position_size": size,
        "entry_px": matched_position.get("entryPx") if matched_position else None,
        "margin_used": matched_position.get("marginUsed") if matched_position else None,
        "unrealized_pnl": matched_position.get("unrealizedPnl") if matched_position else None,
        "raw_position": matched_position,
    }


def check_user_margin_setting(
    user_address: str,
    coin: str,
    margin_api_base_url: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    base_url = (margin_api_base_url or os.getenv("PERPS_API_BASE_URL", "")).rstrip("/")
    if not base_url:
        return {
            "ok": False,
            "error": "PERPS_API_BASE_URL missing",
            "hint": "Set PERPS_API_BASE_URL or pass margin_api_base_url",
        }

    endpoint = f"{base_url}/perps-api/info/get-user-margin-setting"
    # Keep params broad for backend compatibility.
    params = {
        "user": user_address,
        "address": user_address,
        "coin": coin,
        "symbol": coin,
    }
    data = _http_get_json(endpoint, params=params, timeout=timeout)

    is_cross = data.get("isCross") if isinstance(data, dict) else None
    leverage = data.get("leverage") if isinstance(data, dict) else None
    return {
        "ok": True,
        "user": user_address,
        "coin": coin,
        "is_cross": is_cross,
        "leverage": leverage,
        "raw": data,
    }


def _is_tpsl_order(order: dict[str, Any]) -> bool:
    # Hyperliquid open order payload can vary, so detect common trigger/TPSL shapes.
    if order.get("isPositionTpsl") is True:
        return True
    if order.get("triggerCondition") is not None:
        return True
    order_type = str(order.get("orderType", "")).lower()
    if "tp" in order_type or "sl" in order_type or "trigger" in order_type:
        return True
    if order.get("triggerPx") is not None:
        return True
    return False


def check_user_open_orders(
    user_address: str,
    coin: str,
    network: Network = "mainnet",
    timeout: float = 10.0,
) -> dict[str, Any]:
    orders = query_frontend_open_orders(user_address=user_address, network=network, timeout=timeout)
    coin_orders = [o for o in orders if o.get("coin") == coin]
    coin_tpsl_orders = [o for o in coin_orders if _is_tpsl_order(o)]

    return {
        "ok": True,
        "network": network,
        "user": user_address,
        "coin": coin,
        "has_open_orders_for_coin": len(coin_orders) > 0,
        "open_order_count_for_coin": len(coin_orders),
        "has_tpsl_orders_for_coin": len(coin_tpsl_orders) > 0,
        "tpsl_order_count_for_coin": len(coin_tpsl_orders),
        "coin_orders": coin_orders,
    }


def check_market_price(
    coin: str,
    network: Network = "mainnet",
    timeout: float = 10.0,
) -> dict[str, Any]:
    mids = query_all_mids(network=network, timeout=timeout)
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


def check_before_open_plan(
    user_address: str,
    coin: str,
    network: Network = "mainnet",
    margin_api_base_url: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    position_check = check_user_position(user_address=user_address, coin=coin, network=network, timeout=timeout)
    margin_setting_check = check_user_margin_setting(
        user_address=user_address,
        coin=coin,
        margin_api_base_url=margin_api_base_url,
        timeout=timeout,
    )
    open_orders_check = check_user_open_orders(user_address=user_address, coin=coin, network=network, timeout=timeout)
    market_price_check = check_market_price(coin=coin, network=network, timeout=timeout)

    blockers: list[dict[str, str]] = []
    if not market_price_check["is_listed"]:
        blockers.append({"code": "coin_not_listed", "message": f"{coin} not listed on Hyperliquid perps"})

    withdrawable = position_check.get("withdrawable")
    try:
        if withdrawable is not None and float(withdrawable) <= 0:
            blockers.append({"code": "no_withdrawable_margin", "message": "No withdrawable collateral left"})
    except (TypeError, ValueError):
        pass

    return {
        "ok": len(blockers) == 0,
        "network": network,
        "user": user_address,
        "coin": coin,
        "checks": {
            "position": position_check,
            "margin_setting": margin_setting_check,
            "open_orders": open_orders_check,
            "market_price": market_price_check,
        },
        "blockers": blockers,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Read-only Hyperliquid user checks before OPEN_LONG/OPEN_SHORT.")
    parser.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    parser.add_argument("--address", required=True, help="User wallet address")
    parser.add_argument("--coin", required=True, help="Perp coin symbol, e.g. BTC")
    parser.add_argument("--margin-api-base-url", default="", help="Base URL for /perps-api endpoint")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    print("=== check_user_position ===")
    print(
        json.dumps(
            check_user_position(
                user_address=args.address,
                coin=args.coin,
                network=args.network,
                timeout=args.timeout,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("=== check_user_margin_setting ===")
    print(
        json.dumps(
            check_user_margin_setting(
                user_address=args.address,
                coin=args.coin,
                margin_api_base_url=args.margin_api_base_url or None,
                timeout=args.timeout,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("=== check_user_open_orders ===")
    print(
        json.dumps(
            check_user_open_orders(
                user_address=args.address,
                coin=args.coin,
                network=args.network,
                timeout=args.timeout,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("=== check_market_price ===")
    print(
        json.dumps(
            check_market_price(
                coin=args.coin,
                network=args.network,
                timeout=args.timeout,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )

    print("=== check_before_open_plan ===")
    print(
        json.dumps(
            check_before_open_plan(
                user_address=args.address,
                coin=args.coin,
                network=args.network,
                margin_api_base_url=args.margin_api_base_url or None,
                timeout=args.timeout,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
