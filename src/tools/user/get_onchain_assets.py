"""
钱包链上资产查询（EVM + Solana）
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


# =============================================================================
# Pydantic 类
# =============================================================================

class Asset(BaseModel):
    """单个 EVM 资产条目"""
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


class SolAsset(BaseModel):
    """单个 Solana 资产条目"""
    network: str = "sol-mainnet"
    symbol: str | None = None
    name: str | None = None
    balance: float
    value_usd: float | None = None


class SolAssetsResponse(BaseModel):
    """wallet_get_sol_assets 返回格式"""
    ok: bool
    address: str
    total_value_usd: float
    assets: list[SolAsset] = Field(default_factory=list)
    error: str | None = None


# =============================================================================
# 常量
# =============================================================================

ALL_EVM_NETWORKS = ["eth", "base", "arb", "op", "polygon", "bnb", "monad", "ink", "hyperliquid"]


# =============================================================================
# impl 纯函数
# =============================================================================

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


def wallet_get_sol_assets_impl(sol_address: str) -> dict:
    """查询 Solana 钱包资产（纯函数，可直接测试）"""
    from src.services.alchemy.solana import get_solana_portfolio

    raw = get_solana_portfolio(sol_address)
    assets = [
        SolAsset(
            network=a.get("network", "sol-mainnet"),
            symbol=a.get("symbol"),
            name=a.get("name"),
            balance=a.get("balance", 0),
            value_usd=a.get("value_usd"),
        )
        for a in raw.get("assets", [])
    ]
    return SolAssetsResponse(
        ok=raw.get("ok", False),
        address=raw.get("address", sol_address),
        total_value_usd=raw.get("total_value_usd", 0),
        assets=assets,
        error=raw.get("error"),
    ).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

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


@tool
def wallet_get_sol_assets(sol_address: str) -> SolAssetsResponse:
    """查询 Solana 钱包的所有代币资产。

    参数:
        sol_address: Solana 钱包地址（Base58 格式）"""
    if not sol_address:
        return SolAssetsResponse(
            ok=False,
            address="",
            total_value_usd=0,
            error="sol_address 不能为空",
        ).model_dump()
    return wallet_get_sol_assets_impl(sol_address)


# =============================================================================
# if __name__ == "__main__"
# =============================================================================

if __name__ == "__main__":
    from rich import print

    evm_addr = "0x269488c0F8D595CF47aAA91AC6Ef896f9F63cc9E"
    print("=== wallet_get_assets: 全量 EVM 9 条链 ===")
    print(wallet_get_assets_impl(evm_address=evm_addr))
    print()
    print("=== wallet_get_assets: 仅 eth/base ===")
    print(wallet_get_assets_impl(evm_address=evm_addr, networks=["eth", "base"]))
    print()
    sol_addr = "GdV8W4x3WRsRM4Sdouh52Lxktfn1XyuaS6ETSvi8xssq"
    print("=== wallet_get_sol_assets: Solana ===")
    print(wallet_get_sol_assets_impl(sol_addr))