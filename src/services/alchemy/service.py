"""
Alchemy 链上资产查询业务逻辑

使用 Alchemy API 查询多链钱包资产组合
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from .client import ALCHEMY_DATA_API_BASE, post_json
from .network import NATIVE_TOKEN_METADATA, normalize_network


def get_wallet_portfolio(
    address: str,
    networks: list[str] | None = None,
    with_prices: bool = True,
    min_value_usd: float = 0.01,
) -> dict[str, Any]:
    """
    查询钱包在多条链上的资产组合

    参数:
        address: 钱包地址
        networks: 网络列表，默认 ["eth", "base", "arb", "op", "polygon", "bnb", "avax", "monad", "ink", "hyperliquid"]
        with_prices: 是否包含价格数据
        min_value_usd: 最小 USD 值过滤

    返回结构:
    {
        "ok": bool,
        "address": str,
        "networks": [...],
        "total_value_usd": float,
        "asset_count": int,
        "assets": [...],
        "breakdown": {...},
    }
    """
    if networks is None:
        networks = ["eth", "base", "arb", "op", "polygon", "bnb", "avax", "monad", "ink", "hyperliquid"]

    # 标准化网络名称
    normalized_networks = [normalize_network(n) for n in networks]

    try:
        assets, page_key = _fetch_wallet_assets(address, normalized_networks)

        if not assets:
            return {
                "ok": True,
                "address": address,
                "networks": normalized_networks,
                "total_value_usd": 0.0,
                "asset_count": 0,
                "assets": [],
                "breakdown": {},
            }

        # 过滤和排序
        filtered_assets = _filter_and_sort_assets(assets, min_value_usd)

        # 按网络汇总
        breakdown = _build_network_breakdown(filtered_assets)

        # 计算总价值
        total_value = sum(
            float(a.get("value_usd") or 0) for a in filtered_assets
        )

        return {
            "ok": True,
            "address": address,
            "networks": normalized_networks,
            "total_value_usd": round(total_value, 2),
            "asset_count": len(filtered_assets),
            "assets": filtered_assets,
            "breakdown": breakdown,
        }

    except Exception as e:
        return {
            "ok": False,
            "address": address,
            "networks": normalized_networks,
            "error": str(e),
            "total_value_usd": 0.0,
            "asset_count": 0,
            "assets": [],
            "breakdown": {},
        }


def get_native_balance(
    address: str,
    network: str = "eth",
) -> dict[str, Any]:
    """
    查询钱包原生代币余额（如 ETH, MATIC, BNB）

    参数:
        address: 钱包地址
        network: 网络名称

    返回结构:
    {
        "ok": bool,
        "address": str,
        "network": str,
        "symbol": str,
        "balance": float,
        "value_usd": float | None,
    }
    """
    normalized = normalize_network(network)
    metadata = NATIVE_TOKEN_METADATA.get(normalized, {})

    try:
        # 使用 Alchemy 获取原生余额
        url = f"{ALCHEMY_DATA_API_BASE}/balances"
        payload = {
            "addresses": [{"address": address, "network": normalized}],
            "includeNativeBalance": True,
        }
        result = post_json(url, payload)

        data = result.get("data", {})
        address_data = data.get(address, {}).get("native_balance", {})

        raw_balance = address_data.get("balance")
        decimals = metadata.get("decimals", 18)

        if raw_balance is None:
            return {
                "ok": False,
                "address": address,
                "network": normalized,
                "symbol": metadata.get("symbol", "UNKNOWN"),
                "balance": 0.0,
                "value_usd": None,
                "error": "Balance not found",
            }

        # 转换余额
        if isinstance(raw_balance, str) and raw_balance.startswith("0x"):
            balance_decimal = Decimal(int(raw_balance, 16))
        else:
            balance_decimal = Decimal(str(raw_balance))

        normalized_balance = balance_decimal / (Decimal(10) ** decimals)
        balance = float(normalized_balance)

        return {
            "ok": True,
            "address": address,
            "network": normalized,
            "symbol": metadata.get("symbol", "UNKNOWN"),
            "balance": balance,
            "value_usd": None,  # 需要额外查询价格
        }

    except Exception as e:
        return {
            "ok": False,
            "address": address,
            "network": normalized,
            "symbol": metadata.get("symbol", "UNKNOWN"),
            "balance": 0.0,
            "value_usd": None,
            "error": str(e),
        }


# =============================================================================
# 内部函数
# =============================================================================


def _fetch_wallet_assets(
    address: str,
    networks: list[str],
) -> tuple[list[dict[str, Any]], str | None]:
    """获取钱包所有资产"""
    page_key = None
    merged_assets: dict[tuple[str, str], dict[str, Any]] = {}

    while True:
        payload = _build_request_body(address, networks, page_key)

        tokens_payload = post_json(
            f"{ALCHEMY_DATA_API_BASE}/assets/tokens/by-address",
            payload,
        )
        balances_payload = post_json(
            f"{ALCHEMY_DATA_API_BASE}/assets/tokens/balances/by-address",
            {
                "addresses": payload["addresses"],
                "includeNativeTokens": True,
                "includeErc20Tokens": True,
                "pageSize": 100,
                **({"pageKey": page_key} if page_key else {}),
            },
        )

        token_items = ((tokens_payload.get("data") or {}).get("tokens")) or []
        balance_items = ((balances_payload.get("data") or {}).get("tokens")) or []

        for item in token_items:
            key = _asset_key(item)
            merged_assets[key] = dict(item)

        for item in balance_items:
            key = _asset_key(item)
            merged_assets[key] = _merge_asset_payload(merged_assets.get(key), item)

        new_page_key = (
            (tokens_payload.get("data") or {}).get("pageKey")
            or (balances_payload.get("data") or {}).get("pageKey")
        )

        if not new_page_key or new_page_key == page_key:
            break
        page_key = new_page_key

    return list(merged_assets.values()), page_key


def _asset_key(item: dict[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("network") or ""),
        str(item.get("address") or "") + "_" + str(item.get("tokenAddress") or "native"),
    )


def _merge_asset_payload(
    existing: dict[str, Any] | None,
    incoming: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(existing or {})
    for key, value in incoming.items():
        if value is not None or key not in merged:
            merged[key] = value
    return merged


def _build_request_body(
    address: str,
    networks: list[str],
    page_key: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "addresses": [{"address": address, "networks": networks}],
        "withMetadata": True,
        "withPrices": True,
        "includeNativeTokens": True,
        "includeErc20Tokens": True,
        "pageSize": 100,
    }
    if page_key:
        payload["pageKey"] = page_key
    return payload


def _filter_and_sort_assets(
    assets: list[dict[str, Any]],
    min_value_usd: float,
) -> list[dict[str, Any]]:
    """过滤和排序资产"""
    result = []

    for item in assets:
        asset = _map_asset(item)
        if asset.get("value_usd") and float(asset["value_usd"]) < min_value_usd:
            continue
        result.append(asset)

    # 按 USD 值降序排序
    result.sort(
        key=lambda x: float(x.get("value_usd") or 0),
        reverse=True,
    )

    return result


def _map_asset(item: dict[str, Any]) -> dict[str, Any]:
    """将 Alchemy 资产映射为标准格式"""
    metadata = dict(item.get("tokenMetadata") or {})
    network = str(item.get("network") or "")

    # 原生代币使用默认 metadata
    if item.get("tokenAddress") is None:
        metadata = _merge_native_metadata_defaults(metadata, NATIVE_TOKEN_METADATA.get(network, {}))

    prices = item.get("tokenPrices") or []
    usd_price_data = next(
        (p for p in prices if str(p.get("currency", "")).lower() == "usd"),
        None,
    )

    raw_balance = item.get("tokenBalance")
    decimals = metadata.get("decimals")
    normalized_balance = _normalize_token_balance(raw_balance, decimals)

    price_value = _decimal_or_none(usd_price_data.get("value") if usd_price_data else None)
    value_usd = None
    if normalized_balance is not None and price_value is not None:
        value_usd = float(normalized_balance * price_value)

    return {
        "network": network,
        "token_address": item.get("tokenAddress"),
        "symbol": metadata.get("symbol"),
        "name": metadata.get("name"),
        "decimals": decimals if isinstance(decimals, int) else None,
        "balance": float(normalized_balance) if normalized_balance else 0.0,
        "price_usd": float(price_value) if price_value else None,
        "value_usd": value_usd,
        "is_native": item.get("tokenAddress") is None,
        "logo": metadata.get("logo"),
    }


def _merge_native_metadata_defaults(
    metadata: dict[str, Any],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(metadata)
    for key, value in defaults.items():
        if merged.get(key) in (None, ""):
            merged[key] = value
    return merged


def _normalize_token_balance(raw_balance: Any, decimals: Any) -> Decimal | None:
    raw_decimal = _decimal_or_none(raw_balance)
    if raw_decimal is None:
        return None
    if not isinstance(decimals, int):
        return raw_decimal
    return raw_decimal / (Decimal(10) ** decimals)


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, str) and value.lower().startswith("0x"):
        try:
            return Decimal(int(value, 16))
        except ValueError:
            return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _build_network_breakdown(assets: list[dict[str, Any]]) -> dict[str, Any]:
    """按网络汇总资产"""
    breakdown: dict[str, dict[str, Any]] = {}

    for asset in assets:
        network = asset.get("network")
        if not network:
            continue

        if network not in breakdown:
            breakdown[network] = {
                "total_value_usd": 0.0,
                "asset_count": 0,
                "assets": [],
            }

        breakdown[network]["asset_count"] += 1
        breakdown[network]["total_value_usd"] += asset.get("value_usd") or 0
        breakdown[network]["assets"].append(asset)

    # 保留两位小数
    for network in breakdown:
        breakdown[network]["total_value_usd"] = round(breakdown[network]["total_value_usd"], 2)

    return breakdown
