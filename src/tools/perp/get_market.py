"""
市场数据查询模块
"""

from typing import Any

from src.tools.perp._hyperliquid_info import Network, _build_info


def get_all_mids(
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, str]:
    """获取所有币种的中间价"""
    info = _build_info(network, timeout=timeout)
    result = info.all_mids(dex=dex)
    return result if isinstance(result, dict) else {}


def get_perp_mid_price(
    coin: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> str | None:
    """获取某个币的永续中间价"""
    mids = get_all_mids(network=network, dex=dex, timeout=timeout)
    return mids.get(coin)


def get_meta(
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """获取交易所永续合约元数据"""
    info = _build_info(network, timeout=timeout)
    return info.meta(dex=dex)


def get_meta_and_asset_ctxs(
    network: Network = "mainnet",
    timeout: float | None = None,
) -> list[Any]:
    """获取交易所元数据+资产上下文（含 maxLeverage, onlyIsolated 等）"""
    info = _build_info(network, timeout=timeout)
    return info.meta_and_asset_ctxs()


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


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Hyperliquid 市场数据查询")
    parser.add_argument("--action", choices=["price", "coin_info", "all_mids"], required=True)
    parser.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    parser.add_argument("--coin", default="BTC")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    if args.action == "price":
        result = get_market_price(coin=args.coin, network=args.network, timeout=args.timeout)
    elif args.action == "coin_info":
        result = get_coin_info(coin=args.coin, network=args.network, timeout=args.timeout)
    elif args.action == "all_mids":
        result = get_all_mids(network=args.network, timeout=args.timeout)

    print(json.dumps(result, ensure_ascii=False, indent=2))
