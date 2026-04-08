"""
钱包 EVM 链上资产查询
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class Asset(BaseModel):
    """单个资产条目"""
    network: str
    symbol: str | None = None
    balance: float
    value_usd: float | None = None


class WalletPortfolioResponse(BaseModel):
    """wallet_get_assets 返回格式"""
    ok: bool
    address: str
    total_value_usd: float
    assets: list[Asset] = Field(default_factory=list)
    error: str | None = None


# 全部支持的 EVM 网络（9 条）
ALL_EVM_NETWORKS = ["eth", "base", "arb", "op", "polygon", "bnb", "monad", "ink", "hyperliquid"]


def wallet_get_assets_impl(
    evm_address: str,
    networks: list[str] | None = None,
    with_prices: bool = True,
    min_value_usd: float = 0.01,
) -> dict:
    """查询 EVM 钱包资产组合（纯函数，可直接测试）"""
    from src.services.alchemy import get_wallet_portfolio

    target_networks = networks if networks is not None else ALL_EVM_NETWORKS
    raw = get_wallet_portfolio(
        address=evm_address,
        networks=target_networks,
        with_prices=with_prices,
        min_value_usd=min_value_usd,
    )
    simplified_assets = [
        Asset(
            network=a.get("network", ""),
            symbol=a.get("symbol"),
            balance=a.get("balance", 0),
            value_usd=a.get("value_usd"),
        )
        for a in raw.get("assets", [])
    ]
    return WalletPortfolioResponse(
        ok=raw.get("ok", False),
        address=raw.get("address", evm_address),
        total_value_usd=raw.get("total_value_usd", 0),
        assets=simplified_assets,
        error=raw.get("error"),
    ).model_dump()


@tool
def wallet_get_assets(
    evm_address: str,
    networks: list[str] | None = None,
    with_prices: bool = True,
    min_value_usd: float = 0.01,
) -> WalletPortfolioResponse:
    """查询 EVM 钱包在多条链上的资产组合。

    参数:
        evm_address: EVM 钱包地址（0x 开头）
        networks: 要查询的网络列表，默认全部 9 条 EVM 链
                  可选，如 ["eth", "base", "monad"]

    支持网络: eth, base, arb, op, polygon, bnb, monad, ink, hyperliquid"""
    if not evm_address:
        return WalletPortfolioResponse(
            ok=False,
            address="",
            total_value_usd=0,
            error="evm_address 不能为空",
        ).model_dump()
    return wallet_get_assets_impl(
        evm_address=evm_address,
        networks=networks,
        with_prices=with_prices,
        min_value_usd=min_value_usd,
    )


if __name__ == "__main__":
    from rich import print
    addr = "0x269488c0F8D595CF47aAA91AC6Ef896f9F63cc9E"
    print(wallet_get_assets_impl(evm_address=addr))
    print(wallet_get_assets_impl(evm_address=addr, networks=["eth", "base"]))