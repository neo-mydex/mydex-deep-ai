"""
News 工具模块
"""

from .get_processed_content import (
    news_get_processed_content_by_id,
    news_get_processed_content_by_coin,
    news_get_hottest_daily_contents,
)

ALL_TOOLS = [
    news_get_processed_content_by_id,
    news_get_processed_content_by_coin,
    news_get_hottest_daily_contents,
]
