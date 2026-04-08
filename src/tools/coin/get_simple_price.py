"""
查询代币价格（轻量接口）
"""

from langchain_core.tools import tool
from pydantic import BaseModel
from src.services.coingecko import get_coin_price


class CoinSimplePriceResponse(BaseModel):
    """coin_get_simple_price 返回格式"""
    ok: bool
    coin: str
    coin_id: str | None = None
    vs: str = "usd"
    price: float | None = None
    change_24h: float | None = None
    source: str = "coingecko"
    error: str | None = None


def coin_get_simple_price_impl(coin: str, vs: str = "usd") -> dict:
    """查询代币价格（轻量接口，纯函数）"""
    result = get_coin_price(coin=coin, vs=vs)
    return CoinSimplePriceResponse.model_validate(result).model_dump()


@tool
def coin_get_simple_price(coin: str, vs: str = "usd") -> CoinSimplePriceResponse:
    """查询代币价格（轻量接口）。

    支持输入：symbol（如 BTC）、名称（如 Bitcoin）、合约地址（如 0x...）。
    用于"SOL 价格多少"这类简单问价格的问题。"""
    return coin_get_simple_price_impl(coin=coin, vs=vs)


if __name__ == "__main__":
    from rich import print
    print(coin_get_simple_price_impl(coin="BTC"))
