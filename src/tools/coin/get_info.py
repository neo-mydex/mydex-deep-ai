"""
查询代币详情
"""

from langchain_core.tools import tool
from pydantic import BaseModel
from src.services.coingecko import get_coin_info


class CoinInfoResponse(BaseModel):
    """coin_get_info 返回格式"""
    ok: bool
    coin: str
    coin_id: str | None = None
    name: str | None = None
    symbol: str | None = None
    price: float | None = None
    change_24h: float | None = None
    market_cap: float | None = None
    rank: int | None = None
    contract_address: str | None = None
    networks: dict | None = None
    source: str = "coingecko"
    error: str | None = None


def coin_get_info_impl(coin: str) -> dict:
    """查询代币详情（纯函数，可直接测试）"""
    result = get_coin_info(coin=coin)
    return CoinInfoResponse.model_validate(result).model_dump()


@tool
def coin_get_info(coin: str) -> CoinInfoResponse:
    """查询 CoinGecko 代币详情。用于"市值、排名、24h 变化"等信息。"""
    return coin_get_info_impl(coin=coin)


if __name__ == "__main__":
    from pprint import pprint
    pprint(coin_get_info_impl(coin="BTC"))
