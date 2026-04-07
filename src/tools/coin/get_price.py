"""
查询代币价格
"""

from langchain_core.tools import tool
from pydantic import BaseModel
from src.services.coingecko import get_coin_price


class CoinPriceResponse(BaseModel):
    """coin_get_price 返回格式"""
    ok: bool
    coin: str
    coin_id: str | None = None
    vs: str = "usd"
    price: float | None = None
    change_24h: float | None = None
    source: str = "coingecko"
    error: str | None = None


def coin_get_price_impl(coin: str, vs: str = "usd") -> dict:
    """查询代币价格（纯函数，可直接测试）"""
    result = get_coin_price(coin=coin, vs=vs)
    return CoinPriceResponse.model_validate(result).model_dump()


@tool
def coin_get_price(coin: str, vs: str = "usd") -> CoinPriceResponse:
    """查询 CoinGecko 代币价格。用于"SOL 价格"这类问题。"""
    return coin_get_price_impl(coin=coin, vs=vs)


if __name__ == "__main__":
    from rich import print
    print(coin_get_price_impl(coin="BTC"))
