"""
CoinGecko 代币信息查询工具包

对外暴露的 Tool (src/tools/coin/*.py):
- coin_get_price: 获取代币价格
- coin_get_info: 获取代币详细信息（市值、排名等）
- coin_search: 搜索代币
- coin_get_trending: 获取 trending 代币
"""

from typing import Any

try:
    from langchain.tools import tool
except Exception:
    from langchain_core.tools import tool

from src.services.coingecko import (
    get_coin_price,
    get_coin_info,
    search_coins,
    get_trending_coins,
)

from .types import (  # noqa: E402, F401
    CoinPriceResponse,
    CoinInfoResponse,
    CoinCandidate,
    SearchCoinsResponse,
    TrendingCoin,
    TrendingCoinsResponse,
)


@tool
def coin_get_price(coin: str, vs: str = "usd") -> dict[str, Any]:
    """查询 CoinGecko 代币价格。用于"SOL 价格"这类问题。"""
    return get_coin_price(coin=coin, vs=vs)


@tool
def coin_get_info(coin: str) -> dict[str, Any]:
    """查询 CoinGecko 代币详情。用于"市值、排名、24h 变化"等信息。"""
    return get_coin_info(coin=coin)


@tool
def coin_search(query: str) -> dict[str, Any]:
    """搜索代币候选。用于用户只给了模糊名称时先做匹配。"""
    return search_coins(query=query)


@tool
def coin_get_trending() -> dict[str, Any]:
    """查询 CoinGecko 热门代币列表。用于"最近热门币有哪些"。"""
    return get_trending_coins()


__all__ = [
    # 函数
    "coin_get_price",
    "coin_get_info",
    "coin_search",
    "coin_get_trending",
    # 类型定义
    "CoinPriceResponse",
    "CoinInfoResponse",
    "CoinCandidate",
    "SearchCoinsResponse",
    "TrendingCoin",
    "TrendingCoinsResponse",
]
