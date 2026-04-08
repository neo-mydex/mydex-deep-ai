"""
钱包 Solana 链上资产查询
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


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


if __name__ == "__main__":
    from rich import print
    addr = "GdV8W4x3WRsRM4Sdouh52Lxktfn1XyuaS6ETSvi8xssq"
    print(wallet_get_sol_assets_impl(addr))
