"""
钱包链上资产查询
"""

from typing import Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.alchemy import get_wallet_portfolio, get_native_balance


class Asset(BaseModel):
    """单个资产条目"""
    network: str
    token_address: str | None = None
    symbol: str | None = None
    name: str | None = None
    decimals: int | None = None
    balance: float
    price_usd: float | None = None
    value_usd: float | None = None
    is_native: bool = False
    logo: str | None = None


class WalletPortfolioResponse(BaseModel):
    """wallet_get_assets 返回格式"""
    ok: bool
    address: str
    networks: list[str] = Field(default_factory=list)
    total_value_usd: float
    asset_count: int
    assets: list[Asset] = Field(default_factory=list)
    breakdown: dict[str, dict] = Field(default_factory=dict)
    error: str | None = None


class NativeBalanceResponse(BaseModel):
    """wallet_get_native_balance 返回格式"""
    ok: bool
    address: str
    network: str
    symbol: str
    balance: float
    value_usd: float | None = None
    error: str | None = None


def wallet_get_assets_impl(
    address: str,
    networks: list[str] | None = None,
    with_prices: bool = True,
    min_value_usd: float = 0.01,
) -> dict:
    """查询钱包资产组合（纯函数，可直接测试）"""
    result = get_wallet_portfolio(
        address=address,
        networks=networks,
        with_prices=with_prices,
        min_value_usd=min_value_usd,
    )
    return WalletPortfolioResponse.model_validate(result).model_dump()


def wallet_get_native_balance_impl(
    address: str,
    network: str = "eth",
) -> dict:
    """查询钱包原生代币余额（纯函数，可直接测试）"""
    result = get_native_balance(address=address, network=network)
    return NativeBalanceResponse.model_validate(result).model_dump()


@tool
def wallet_get_assets(
    address: str,
    networks: list[str] | None = None,
    with_prices: bool = True,
    min_value_usd: float = 0.01,
) -> WalletPortfolioResponse:
    """查询钱包在多条链上的资产组合。用于"我钱包里有什么资产"。"""
    return wallet_get_assets_impl(
        address=address,
        networks=networks,
        with_prices=with_prices,
        min_value_usd=min_value_usd,
    )


@tool
def wallet_get_native_balance(
    address: str,
    network: str = "eth",
) -> NativeBalanceResponse:
    """查询钱包原生代币余额（如 ETH、MATIC、BNB）。用于"ETH/Base 链原生币余额是多少"。"""
    return wallet_get_native_balance_impl(address=address, network=network)


if __name__ == "__main__":
    from pprint import pprint
    addr = "0x1234567890abcdef1234567890abcdef12345678"
    pprint(wallet_get_assets_impl(address=addr))
    pprint(wallet_get_native_balance_impl(address=addr))
