"""
CoinGecko 代币信息查询服务

提供代币价格、信息搜索、trending 等功能

模块结构:
- client: HTTP 客户端（fetch_json, build_url, COINGECKO_API_BASE）
- normalize: 符号/ID 标准化（SYMBOL_TO_ID, NETWORK_TO_COINGECKO, symbol_to_id, is_contract_address, normalize_symbol）
- fallback: 降级逻辑（EVM_FALLBACK_NETWORKS, should_fallback_to_free, rank_candidates）
- cli: 业务层函数（get_coin_price, get_coin_info, search_coins, get_trending_coins）
"""

from .cli import (
    get_coin_price,
    get_coin_info,
    search_coins,
    get_trending_coins,
)

__all__ = [
    "get_coin_price",
    "get_coin_info",
    "search_coins",
    "get_trending_coins",
]
