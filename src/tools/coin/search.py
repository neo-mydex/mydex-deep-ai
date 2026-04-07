"""
搜索代币
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.coingecko import search_coins


class CoinCandidate(BaseModel):
    """搜索候选代币"""
    id: str | None = None
    name: str | None = None
    symbol: str | None = None
    rank: int | None = None
    platforms: dict | None = None


class SearchCoinsResponse(BaseModel):
    """coin_search 返回格式"""
    ok: bool
    query: str
    candidates: list[CoinCandidate] = Field(default_factory=list)
    source: str = "coingecko"
    error: str | None = None


def coin_search_impl(query: str) -> dict:
    """搜索代币（纯函数，可直接测试）"""
    result = search_coins(query=query)
    return SearchCoinsResponse.model_validate(result).model_dump()


@tool
def coin_search(query: str) -> SearchCoinsResponse:
    """搜索代币候选。用于用户只给了模糊名称时先做匹配。"""
    return coin_search_impl(query=query)


if __name__ == "__main__":
    from rich import print
    print(coin_search_impl(query="ETH"))
