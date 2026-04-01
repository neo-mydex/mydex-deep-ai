"""
CoinGecko 代币信息查询工具包

对外暴露的 Tool (src/tools/coin/*.py):
- get_coin_price: 获取代币价格
- get_coin_info: 获取代币详细信息（市值、排名等）
- search_coins: 搜索代币
- get_trending_coins: 获取 trending 代币

内部模块 (src/tools/coin/_*.py):
- _client: HTTP 客户端配置
- _normalize: 代币符号/ID 标准化
- _fallback: 降级/兜底逻辑
"""

from .coingecko import (
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

__all__ = [
    "get_coin_price",
    "get_coin_info",
    "search_coins",
    "get_trending_coins",
    # 类型定义
    "CoinPriceResponse",
    "CoinInfoResponse",
    "CoinCandidate",
    "SearchCoinsResponse",
    "TrendingCoin",
    "TrendingCoinsResponse",
]
