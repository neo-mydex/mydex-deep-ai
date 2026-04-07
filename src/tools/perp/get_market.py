"""
市场数据查询
"""

from typing import Literal
from langchain_core.tools import tool
from pydantic import BaseModel
from src.services.hyperliquid.cli import get_market_price, get_coin_info

Network = Literal["mainnet", "testnet"]


class MarketPriceResponse(BaseModel):
    """perp_get_market_price 返回格式"""
    ok: bool
    network: Network
    coin: str
    mark_price: float | None = None
    mark_price_raw: str | None = None
    is_listed: bool


class CoinInfoResponse(BaseModel):
    """perp_get_coin_info 返回格式"""
    ok: bool
    coin: str
    network: Network
    is_listed: bool
    max_leverage: int | None = None
    only_isolated: bool
    sz_decimals: int | None = None


def perp_get_market_price_impl(
    coin: str,
    network: Network = "mainnet",
) -> dict:
    """获取市场当前价格（纯函数，可直接测试）"""
    result = get_market_price(coin=coin, network=network)
    return MarketPriceResponse.model_validate(result).model_dump()


def perp_get_coin_info_impl(
    coin: str,
    network: Network = "mainnet",
) -> dict:
    """获取币种详细信息（纯函数，可直接测试）"""
    result = get_coin_info(coin=coin, network=network)
    return CoinInfoResponse.model_validate(result).model_dump()


@tool
def perp_get_market_price(
    coin: str,
    network: Network = "mainnet",
) -> MarketPriceResponse:
    """
    获取 Hyperliquid 永续合约市场当前价格。

    用于查询币种的当前市场价格，帮助判断是否可以开仓/平仓。

    参数:
        coin: 币种名称，如 "BTC"、"ETH"
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        MarketPriceResponse: {
            "ok": bool,
            "network": str,
            "coin": str,
            "mark_price": float | None,
            "mark_price_raw": str | None,
            "is_listed": bool,
        }
    """
    return perp_get_market_price_impl(coin=coin, network=network)


@tool
def perp_get_coin_info(
    coin: str,
    network: Network = "mainnet",
) -> CoinInfoResponse:
    """
    获取 Hyperliquid 永续合约币种的详细信息。

    用于查询币种是否上线、最大杠杆、是否仅支持逐仓等信息。

    参数:
        coin: 币种名称，如 "BTC"、"ETH"
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        CoinInfoResponse: {
            "ok": bool,
            "coin": str,
            "network": str,
            "is_listed": bool,
            "max_leverage": int | None,
            "only_isolated": bool,
            "sz_decimals": int | None,
        }
    """
    return perp_get_coin_info_impl(coin=coin, network=network)


if __name__ == "__main__":
    from pprint import pprint
    pprint(perp_get_market_price_impl(coin="BTC"))
    pprint(perp_get_coin_info_impl(coin="BTC"))
