"""
用户仓位查询
"""

from typing import Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.hyperliquid.cli import get_user_positions

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
    coin: str | None = None
    positions: list[PositionDetail] = Field(default_factory=list)


def perp_get_positions_impl(
    address: str,
    coin: str | None = None,
    network: Network = "mainnet",
) -> dict:
    """获取用户仓位（纯函数，可直接测试）

    - coin=None → 返回所有仓位
    - coin="BTC" → 只返回该 coin 的仓位
    """
    result = get_user_positions(address=address, network=network)

    positions: list[dict] = result.get("positions", [])
    if coin is not None:
        positions = [p for p in positions if p.get("coin") == coin]

    return PositionsResponse.model_validate({
        "ok": result.get("ok", False),
        "address": result.get("address", address),
        "network": result.get("network", network),
        "coin": coin,
        "positions": positions,
    }).model_dump()


@tool
def perp_get_positions(
    address: str,
    coin: str | None = None,
    network: Network = "mainnet",
) -> PositionsResponse:
    """
    获取 Hyperliquid 永续合约用户仓位。

    - coin 不传 → 返回用户所有仓位
    - coin 传了 → 只返回该币种仓位

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"、"ETH"，不传则查所有
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        PositionsResponse: {
            "ok": bool,
            "address": str,
            "network": str,
            "coin": str | None,
            "positions": list[PositionDetail],
        }
    """
    return perp_get_positions_impl(address=address, coin=coin, network=network)


if __name__ == "__main__":
    from rich import print
    from dotenv import load_dotenv
    import os
    load_dotenv()
    EVM_ADDRESS = os.environ["EVM_ADDRESS"]

    print("=== 查所有仓位 ===")
    print(perp_get_positions_impl(address=EVM_ADDRESS))
    print()
    print("=== 查 BTC ===")
    print(perp_get_positions_impl(address=EVM_ADDRESS, coin="BTC"))
