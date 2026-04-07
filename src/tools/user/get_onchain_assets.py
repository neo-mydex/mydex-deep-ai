"""
钱包链上资产查询
"""

from langchain.tools import ToolRuntime
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.alchemy import get_wallet_portfolio, get_native_balance


class Asset(BaseModel):
    """单个资产条目（简化字段）"""
    network: str
    symbol: str | None = None
    balance: float
    value_usd: float | None = None


class WalletPortfolioResponse(BaseModel):
    """wallet_get_assets 返回格式

    注意：仅支持 EVM 链（eth、base、arb、op、polygon、bnb、avax）。
    Solana 地址查询暂不支持（Alchemy EVM API 不覆盖 Solana）。"""
    ok: bool
    address: str
    total_value_usd: float
    assets: list[Asset] = Field(default_factory=list)
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
    raw = get_wallet_portfolio(
        address=address,
        networks=networks,
        with_prices=with_prices,
        min_value_usd=min_value_usd,
    )
    # 简化响应：只保留关键字段，去除 breakdown 重复数据
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
        address=raw.get("address", address),
        total_value_usd=raw.get("total_value_usd", 0),
        assets=simplified_assets,
        error=raw.get("error"),
    ).model_dump()


def wallet_get_native_balance_impl(
    address: str,
    network: str = "eth",
) -> dict:
    """查询钱包原生代币余额（纯函数，可直接测试）"""
    result = get_native_balance(address=address, network=network)
    return NativeBalanceResponse.model_validate(result).model_dump()


@tool
def wallet_get_assets(
    runtime: ToolRuntime,
    networks: list[str] | None = None,
    with_prices: bool = True,
    min_value_usd: float = 0.01,
) -> WalletPortfolioResponse:
    """查询钱包在多条链上的资产组合。用于"我钱包里有什么资产"。

    注意：仅支持 EVM 链（eth、base、arb、op、polygon、bnb、avax）。
    Solana 地址请使用 wallet_get_native_balance 并指定 network="sol" 查询 SOL 余额。"""
    evm_address = runtime.context.evm_address if runtime.context else ""
    if not evm_address:
        return WalletPortfolioResponse(
            ok=False,
            address="",
            total_value_usd=0,
            error="未绑定 EVM 钱包地址",
        ).model_dump()
    return wallet_get_assets_impl(
        address=evm_address,
        networks=networks,
        with_prices=with_prices,
        min_value_usd=min_value_usd,
    )


@tool
def wallet_get_native_balance(
    runtime: ToolRuntime,
    network: str = "eth",
) -> NativeBalanceResponse:
    """查询钱包原生代币余额（如 ETH、MATIC、BNB、SOL）。用于"ETH/Base 链原生币余额是多少"。

    支持网络：eth、base、arb、op、polygon、bnb、avax、sol（仅原生余额）。"""
    if network == "sol":
        sol_address = runtime.context.sol_address if runtime.context else ""
        if not sol_address:
            return NativeBalanceResponse(
                ok=False,
                address="",
                network="sol",
                symbol="SOL",
                balance=0,
                error="未绑定 Solana 钱包地址",
            ).model_dump()
        address = sol_address
    else:
        evm_address = runtime.context.evm_address if runtime.context else ""
        if not evm_address:
            return NativeBalanceResponse(
                ok=False,
                address="",
                network=network,
                symbol=network.upper(),
                balance=0,
                error="未绑定 EVM 钱包地址",
            ).model_dump()
        address = evm_address
    return wallet_get_native_balance_impl(address=address, network=network)


if __name__ == "__main__":
    from rich import print
    addr = "0x1234567890abcdef1234567890abcdef12345678"
    print(wallet_get_assets_impl(address=addr))
    print(wallet_get_native_balance_impl(address=addr))
