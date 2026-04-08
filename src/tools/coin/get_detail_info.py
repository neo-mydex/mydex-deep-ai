"""
查询代币详情（完整接口）
"""

from langchain_core.tools import tool
from pydantic import BaseModel
from src.services.coingecko import get_coin_info


class CoinDetailInfoResponse(BaseModel):
    """coin_get_detail_info 返回格式"""
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


def coin_get_detail_info_impl(coin: str) -> dict:
    """查询代币详情（完整接口，纯函数）"""
    result = get_coin_info(coin=coin)
    return CoinDetailInfoResponse.model_validate(result).model_dump()


@tool
def coin_get_detail_info(coin: str) -> CoinDetailInfoResponse:
    """查询代币详情（完整接口）。

    支持输入：symbol（如 BTC）、名称（如 Bitcoin）、合约地址（如 0x...）。
    返回市值、排名、合约地址、各链地址等完整信息。
    用于需要更多详情时。"""
    return coin_get_detail_info_impl(coin=coin)


if __name__ == "__main__":
    from rich import print
    print(coin_get_detail_info_impl(coin="BTC"))
