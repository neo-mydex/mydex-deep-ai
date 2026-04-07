"""
用户仓位查询
"""

from typing import Literal
from langchain_core.tools import tool
from pydantic import BaseModel
from src.services.hyperliquid.cli import get_user_positions, get_user_position

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short", "flat"]
MarginType = Literal["cross", "isolated"]


class PositionDetail(BaseModel):
    """单个仓位详情"""
    coin: str
    size: float
    side: Side
    entry_px: float | None = None
    mark_px: float | None = None
    position_value: float | None = None
    unrealized_pnl: float | None = None
    leverage: int | None = None
    margin_type: MarginType | None = None
    liquidation_px: float | None = None


class PositionsResponse(BaseModel):
    """perp_get_positions 返回格式"""
    ok: bool
    address: str
    network: Network
    account_value: float | None = None
    withdrawable: float
    positions: list[PositionDetail] = []


class SinglePositionResponse(BaseModel):
    """perp_get_position 返回格式"""
    ok: bool
    address: str
    coin: str
    network: Network
    has_position: bool
    position_side: Side
    position_size: float | None = None
    entry_px: float | None = None
    mark_px: float | None = None
    leverage: int | None = None
    margin_type: MarginType | None = None
    liquidation_px: float | None = None
    unrealized_pnl: float | None = None


def perp_get_positions_impl(
    address: str,
    network: Network = "mainnet",
) -> dict:
    """获取所有仓位（纯函数，可直接测试）"""
    result = get_user_positions(address=address, network=network)
    return PositionsResponse.model_validate(result).model_dump()


def perp_get_position_impl(
    address: str,
    coin: str,
    network: Network = "mainnet",
) -> dict:
    """获取指定币种仓位（纯函数，可直接测试）"""
    result = get_user_position(address=address, coin=coin, network=network)
    return SinglePositionResponse.model_validate(result).model_dump()


@tool
def perp_get_positions(
    address: str,
    network: Network = "mainnet",
) -> PositionsResponse:
    """
    获取 Hyperliquid 永续合约用户所有仓位。

    用于查询用户当前持有的所有永续合约仓位，包括方向、大小、盈亏等信息。

    参数:
        address: 用户钱包地址
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        PositionsResponse: {
            "ok": bool,
            "address": str,
            "network": str,
            "account_value": float | None,
            "withdrawable": float,
            "positions": list[PositionDetail],
        }
    """
    return perp_get_positions_impl(address=address, network=network)


@tool
def perp_get_position(
    address: str,
    coin: str,
    network: Network = "mainnet",
) -> SinglePositionResponse:
    """
    获取 Hyperliquid 永续合约用户指定币种的仓位。

    用于查询用户当前持有的某个特定币种的永续合约仓位。

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"、"ETH"
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        SinglePositionResponse: {
            "ok": bool,
            "address": str,
            "coin": str,
            "network": str,
            "has_position": bool,
            "position_side": "long" | "short" | "flat",
            "position_size": float | None,
            "entry_px": float | None,
            "mark_px": float | None,
            "leverage": int | None,
            "margin_type": "cross" | "isolated" | None,
            "liquidation_px": float | None,
            "unrealized_pnl": float | None,
        }
    """
    return perp_get_position_impl(address=address, coin=coin, network=network)


if __name__ == "__main__":
    from rich import print
    addr = "0x1234567890abcdef1234567890abcdef12345678"
    print(perp_get_positions_impl(address=addr))
    print(perp_get_position_impl(address=addr, coin="BTC"))
