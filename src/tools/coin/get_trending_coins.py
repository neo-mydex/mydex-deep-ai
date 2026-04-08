"""
查询热门代币
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.coingecko import get_trending_coins


class TrendingCoinsResponse(BaseModel):
    """coin_get_trending_coins 返回格式"""
    ok: bool
    coins: list[dict] = Field(default_factory=list)
    source: str = "coingecko"
    error: str | None = None


def coin_get_trending_coins_impl() -> dict:
    """查询热门代币（纯函数）"""
    result = get_trending_coins()
    return TrendingCoinsResponse.model_validate(result).model_dump()


@tool
def coin_get_trending_coins() -> TrendingCoinsResponse:
    """查询热门代币列表。

    无需输入参数，返回 CoinGecko trending 页面的代币列表。
    用于"最近热门币有哪些"。"""
    return coin_get_trending_coins_impl()


if __name__ == "__main__":
    from rich import print
    print(coin_get_trending_coins_impl())
