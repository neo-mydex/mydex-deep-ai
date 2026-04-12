"""
查询 AI 处理后的内容详情
"""

from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel
from src.services.postgresql import get_processed_content_by_id, get_processed_content_by_coin, get_hottest_daily_contents


class ProcessedContentResponse(BaseModel):
    """news_get_processed_content_by_id 返回格式"""
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class ProcessedContentListResponse(BaseModel):
    """news_get_processed_content_by_coin 返回格式"""
    ok: bool
    data: list[dict[str, Any]] | None = None
    error: str | None = None


# =============================================================================
# impl 纯函数（model_validate 在 impl 内部完成）
# =============================================================================

def news_get_processed_content_by_id_impl(content_id: str) -> dict:
    """按 ID 查询 AI 处理后的内容详情。"""
    result = get_processed_content_by_id(content_id)
    return ProcessedContentResponse.model_validate(result).model_dump()


def news_get_processed_content_by_coin_impl(coin: str, limit: int = 10) -> dict:
    """按 coin 查询相关内容。"""
    result = get_processed_content_by_coin(coin=coin, limit=limit)
    return ProcessedContentListResponse.model_validate(result).model_dump()


def news_get_hottest_daily_contents_impl(coin: str | None = None, limit: int = 10) -> dict:
    """查询 24 小时内的热门内容。"""
    result = get_hottest_daily_contents(coin=coin, limit=limit)
    return ProcessedContentListResponse.model_validate(result).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

@tool
def news_get_processed_content_by_id(content_id: str) -> dict:
    """根据内容 ID 查询 AI 处理后的内容详情。

    用于用户引用某条内容并想要了解详情时调用，如：
    - "帮我分析这条内容"
    - "这条新闻说了什么"
    - 用户粘贴一个 content_id 并要求查看详情
    """
    return news_get_processed_content_by_id_impl(content_id)


@tool
def news_get_processed_content_by_coin(coin: str, limit: int = 10) -> dict:
    """按代币查询相关内容。

    在 suggested_tokens 中匹配 symbol 或 name，按 published_at 倒序返回。

    用于：
    - "帮我找一下 BTC 相关的最新内容"
    - "有哪些新闻提到了 ETH"
    """
    return news_get_processed_content_by_coin_impl(coin=coin, limit=limit)


@tool
def news_get_hottest_daily_contents(coin: str | None = None, limit: int = 10) -> dict:
    """查询 24 小时内的热门内容。

    按 hotness_score 倒序返回。若指定 coin，则在 suggested_tokens 中匹配。

    用于：
    - "今日热点有哪些"
    - "过去 24 小时最火的新闻"
    - "BTC 相关的热点新闻"
    """
    return news_get_hottest_daily_contents_impl(coin=coin, limit=limit)


# =============================================================================
# if __name__ == "__main__"
# =============================================================================

if __name__ == "__main__":
    from rich import print

    # uv run python -m src.tools.news.get_processed_content

    print("=== news_get_processed_content_by_id ===")
    print(news_get_processed_content_by_id_impl("social_2041546291302306032"))
    print()
    print("=== news_get_processed_content_by_coin (BTC) ===")
    result = news_get_processed_content_by_coin_impl("BTC", limit=3)
    print(f"count: {len(result['data'])}")
    for r in result["data"]:
        print(f"  - {r['id']} ({r['published_at']})")
    print()
    print("=== news_get_hottest_daily_contents (limit=3) ===")
    result = news_get_hottest_daily_contents_impl(limit=3)
    print(f"count: {len(result['data'])}")
    for r in result["data"]:
        print(f"  - {r['id']} hotness={r['hotness_score']}")
    print()
    print("=== news_get_hottest_daily_contents (coin=BTC, limit=3) ===")
    result = news_get_hottest_daily_contents_impl(coin="BTC", limit=3)
    print(f"count: {len(result['data'])}")
    for r in result["data"]:
        print(f"  - {r['id']} hotness={r['hotness_score']}")
