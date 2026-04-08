"""
CoinGecko 代币信息查询工具包
"""

from .get_simple_price import coin_get_simple_price
from .get_detail_info import coin_get_detail_info
from .search_coins import coin_search_coins
from .get_trending_coins import coin_get_trending_coins

ALL_TOOLS = [
    coin_get_simple_price,
    coin_get_detail_info,
    coin_search_coins,
    coin_get_trending_coins,
]
