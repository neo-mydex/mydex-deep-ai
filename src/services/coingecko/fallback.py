"""
降级/兜底逻辑

当 Pro API 不可用时尝试备用方案
"""

from typing import Any


# EVM 网络列表（按优先级排序）
EVM_FALLBACK_NETWORKS = [
    "ethereum",
    "binance-smart-chain",
    "base",
    "arbitrum-one",
    "optimistic-ethereum",
]


def should_fallback_to_free(error: Exception) -> bool:
    """
    判断是否应该降级到免费 API

    参数:
        error: 当前异常

    返回:
        是否降级
    """
    if isinstance(error, RuntimeError):
        # Pro API 可能 rate limit，尝试免费版
        if "429" in str(error) or "rate limit" in str(error).lower():
            return True
    return False


def rank_candidates(
    coins: list[dict[str, Any]], query: str
) -> list[dict[str, Any]]:
    """
    对搜索结果排序，优先返回完全匹配和市值排名靠前的

    参数:
        coins: 搜索结果列表
        query: 搜索关键词

    返回:
        排序后的列表
    """
    normalized_query = query.strip().lower()
    exact_matches: list[dict[str, Any]] = []
    partial_matches: list[dict[str, Any]] = []

    for item in coins:
        symbol = str(item.get("symbol", "")).lower()
        name = str(item.get("name", "")).lower()
        if normalized_query in {symbol, name}:
            exact_matches.append(item)
        else:
            partial_matches.append(item)

    candidate_pool = exact_matches or partial_matches or coins

    def sort_key(item: dict[str, Any]) -> tuple:
        rank = item.get("market_cap_rank")
        market_cap = item.get("market_cap_usd")
        rank_value = rank if isinstance(rank, int) else 10**9
        market_cap_value = float(market_cap) if isinstance(market_cap, (int, float)) else -1.0
        return (rank_value, -market_cap_value)

    return sorted(candidate_pool, key=sort_key)
