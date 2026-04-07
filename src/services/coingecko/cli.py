"""
CoinGecko 代币信息查询 - 业务层

对外暴露的函数:
- get_coin_price: 获取代币价格
- get_coin_info: 获取代币详细信息（市值、排名等）
- search_coins: 搜索代币
- get_trending_coins: 获取 trending 代币
"""

from typing import Any

from .client import fetch_json, build_url, COINGECKO_API_BASE
from .normalize import (
    symbol_to_id,
    is_contract_address,
    normalize_symbol,
    SYMBOL_TO_ID,
    NETWORK_TO_COINGECKO,
)
from .fallback import rank_candidates


# =============================================================================
# 内部工具函数
# =============================================================================


def _fetch_coin_detail(coin_id: str) -> dict[str, Any]:
    """获取代币详细信息"""
    url = build_url(
        f"/coins/{coin_id}",
        params={
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        },
    )
    return fetch_json(url)


def _fetch_token_by_contract(network: str, address: str) -> dict[str, Any] | None:
    """
    通过合约地址获取代币信息

    参数:
        network: 网络名称（如 "ethereum", "base", "solana"）
        address: 合约地址

    返回:
        CoinGecko 代币详情或 None
    """
    from urllib.parse import quote

    cg_network = NETWORK_TO_COINGECKO.get(network.lower(), network.lower())
    url = f"{COINGECKO_API_BASE}/coins/{quote(cg_network)}/contract/{quote(address)}"
    try:
        return fetch_json(url)
    except Exception:
        return None


def _coin_id_from_query(query: str) -> str | None:
    """
    尝试将查询字符串转换为 coin_id

    1. 已知符号映射
    2. 搜索
    """
    normalized = normalize_symbol(query)
    # 尝试直接映射
    if normalized in SYMBOL_TO_ID:
        return SYMBOL_TO_ID[normalized]
    # 尝试搜索
    try:
        url = build_url("/search", params={"query": query})
        result = fetch_json(url)
        coins = result.get("coins", [])
        if coins:
            ranked = rank_candidates(coins, query)
            return ranked[0]["id"]
    except Exception:
        pass
    return None


def _coin_id_from_contract_address(address: str) -> tuple[str, str] | None:
    """
    通过合约地址获取 coin_id 和网络

    自动尝试多个 EVM 网络

    返回:
        (coin_id, network) 或 None
    """
    # EVM 网络优先级
    evm_networks = ["ethereum", "base", "arbitrum-one", "optimistic-ethereum"]

    for network in evm_networks:
        result = _fetch_token_by_contract(network, address)
        if result and result.get("id"):
            return result["id"], network

    return None


def _resolve_coin_input(coin: str) -> dict[str, Any]:
    """
    解析 coin 输入，返回 coin_id 和相关信息

    支持: 符号、名称搜索、合约地址

    返回:
    {
        "coin_id": str | None,
        "input_type": "symbol" | "name" | "contract" | None,
        "network": str | None,
        "original": str,
    }
    """
    # 合约地址
    if is_contract_address(coin):
        result = _coin_id_from_contract_address(coin)
        if result:
            return {
                "coin_id": result[0],
                "input_type": "contract",
                "network": result[1],
                "original": coin,
            }
        return {
            "coin_id": None,
            "input_type": "contract",
            "network": None,
            "original": coin,
        }

    # 符号/名称
    coin_id = _coin_id_from_query(coin)
    if coin_id:
        return {
            "coin_id": coin_id,
            "input_type": "symbol" if normalize_symbol(coin) in SYMBOL_TO_ID else "name",
            "network": None,
            "original": coin,
        }

    return {
        "coin_id": None,
        "input_type": None,
        "network": None,
        "original": coin,
    }


def _fetch_platforms(coin_id: str) -> dict[str, str] | None:
    """
    获取代币在各链的合约地址（轻量级调用）

    参数:
        coin_id: CoinGecko 代币 ID

    返回:
        {network: contract_address, ...} 或 None
    """
    try:
        # 只请求 platforms 信息，轻量级
        url = build_url(
            f"/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "false",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false",
            },
        )
        data = fetch_json(url)
        return data.get("platforms") or {}
    except Exception:
        return None


# =============================================================================
# 公开 API 函数
# =============================================================================


def get_coin_price(
    coin: str,
    vs: str = "usd",
) -> dict[str, Any]:
    """
    获取代币价格

    参数:
        coin: 代币符号、名称或合约地址
        vs: 计价货币 (默认 "usd")

    返回结构:
    {
        "ok": bool,
        "coin": str,
        "coin_id": str | None,
        "vs": str,
        "price": float | None,
        "change_24h": float | None,
        "source": str,
    }
    """
    resolved = _resolve_coin_input(coin)
    coin_id = resolved["coin_id"]

    if not coin_id:
        return {
            "ok": False,
            "coin": coin,
            "coin_id": None,
            "vs": vs,
            "price": None,
            "change_24h": None,
            "source": "coingecko",
            "error": f"未找到代币: {coin}",
        }

    # 获取价格
    try:
        url = build_url(
            "/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": vs,
                "include_24hr_change": "true",
            },
        )
        result = fetch_json(url)
        coin_data = result.get(coin_id, {})
        vs_data = coin_data.get(vs, 0)

        return {
            "ok": True,
            "coin": coin,
            "coin_id": coin_id,
            "vs": vs,
            "price": vs_data if isinstance(vs_data, (int, float)) else None,
            "change_24h": coin_data.get(f"{vs}_24h_change"),
            "source": "coingecko",
        }
    except Exception as e:
        return {
            "ok": False,
            "coin": coin,
            "coin_id": coin_id,
            "vs": vs,
            "price": None,
            "change_24h": None,
            "source": "coingecko",
            "error": str(e),
        }


def get_coin_info(
    coin: str,
    vs: str = "usd",
) -> dict[str, Any]:
    """
    获取代币详细信息（市值、排名、价格等）

    参数:
        coin: 代币符号、名称或合约地址
        vs: 计价货币 (默认 "usd")

    返回结构:
    {
        "ok": bool,
        "coin": str,
        "coin_id": str | None,
        "name": str | None,
        "symbol": str | None,
        "price": float | None,
        "change_24h": float | None,
        "market_cap": float | None,
        "rank": int | None,
        "contract_address": str | None,
        "networks": {...},
        "source": str,
    }
    """
    resolved = _resolve_coin_input(coin)
    coin_id = resolved["coin_id"]

    if not coin_id:
        return {
            "ok": False,
            "coin": coin,
            "coin_id": None,
            "name": None,
            "symbol": None,
            "price": None,
            "change_24h": None,
            "market_cap": None,
            "rank": None,
            "contract_address": coin if is_contract_address(coin) else None,
            "networks": None,
            "source": "coingecko",
            "error": f"未找到代币: {coin}",
        }

    try:
        # 合约地址查询直接返回完整数据
        if resolved["input_type"] == "contract":
            data = _fetch_token_by_contract(resolved["network"], coin)
        else:
            data = _fetch_coin_detail(coin_id)

        if not data:
            return {
                "ok": False,
                "coin": coin,
                "coin_id": coin_id,
                "name": None,
                "symbol": None,
                "price": None,
                "change_24h": None,
                "market_cap": None,
                "rank": None,
                "contract_address": coin if is_contract_address(coin) else None,
                "networks": None,
                "source": "coingecko",
                "error": "获取详情失败",
            }

        market_data = data.get("market_data", {}) or {}

        return {
            "ok": True,
            "coin": coin,
            "coin_id": data.get("id"),
            "name": data.get("name"),
            "symbol": data.get("symbol", "").upper(),
            "price": market_data.get("current_price", {}).get(vs.lower()),
            "change_24h": market_data.get("price_change_percentage_24h"),
            "market_cap": market_data.get("market_cap", {}).get(vs.lower()),
            "rank": data.get("market_cap_rank"),
            "contract_address": coin if is_contract_address(coin) else None,
            "networks": data.get("platforms") or {},
            "source": "coingecko",
        }
    except Exception as e:
        return {
            "ok": False,
            "coin": coin,
            "coin_id": coin_id,
            "name": None,
            "symbol": None,
            "price": None,
            "change_24h": None,
            "market_cap": None,
            "rank": None,
            "source": "coingecko",
            "error": str(e),
        }


def search_coins(
    query: str,
    limit: int = 5,
) -> dict[str, Any]:
    """
    搜索代币（包含合约地址）

    参数:
        query: 搜索关键词（符号、名称）
        limit: 返回数量 (默认 5)

    返回结构:
    {
        "ok": bool,
        "query": str,
        "candidates": [
            {
                "id": str,
                "name": str,
                "symbol": str,
                "rank": int | None,
                "platforms": {network: address, ...},
            },
            ...
        ],
        "source": str,
    }
    """
    if is_contract_address(query):
        return {
            "ok": False,
            "query": query,
            "candidates": [],
            "source": "coingecko",
            "error": "合约地址请使用 get_coin_info",
        }

    try:
        url = build_url("/search", params={"query": query})
        result = fetch_json(url)
        coins = result.get("coins", [])

        if not coins:
            return {
                "ok": True,
                "query": query,
                "candidates": [],
                "source": "coingecko",
            }

        ranked = rank_candidates(coins, query)
        candidates = []
        for item in ranked[:limit]:
            coin_id = item.get("id")
            # 获取合约地址（只对 top 3 做这个额外调用）
            platforms = None
            if coin_id and len(candidates) < 3:
                platforms = _fetch_platforms(coin_id)

            candidate = {
                "id": coin_id,
                "name": item.get("name"),
                "symbol": item.get("symbol", "").upper(),
                "rank": item.get("market_cap_rank"),
            }
            if platforms:
                candidate["platforms"] = platforms

            candidates.append(candidate)

        return {
            "ok": True,
            "query": query,
            "candidates": candidates,
            "source": "coingecko",
        }
    except Exception as e:
        return {
            "ok": False,
            "query": query,
            "candidates": [],
            "source": "coingecko",
            "error": str(e),
        }


def get_trending_coins() -> dict[str, Any]:
    """
    获取 trending 代币

    返回结构:
    {
        "ok": bool,
        "coins": [...],
        "source": str,
    }
    """
    try:
        url = build_url("/search/trending")
        result = fetch_json(url)
        return {
            "ok": True,
            "coins": result.get("coins", []),
            "source": "coingecko",
        }
    except Exception as e:
        return {
            "ok": False,
            "coins": [],
            "source": "coingecko",
            "error": str(e),
        }
