"""
平仓前检查
"""

from typing import Any, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.hyperliquid import check_can_close as service_check_can_close

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short", "flat"]


class PositionInfo(BaseModel):
    """仓位信息摘要"""
    has_position: bool
    position_side: Side
    position_size: float | None = None
    close_size: float


class CanCloseChecks(BaseModel):
    """平仓检查的各项结果"""
    position: dict[str, Any] = Field(default_factory=dict)
    open_orders: dict[str, Any] = Field(default_factory=dict)
    market: dict[str, Any] = Field(default_factory=dict)


class CanCloseResponse(BaseModel):
    """perp_check_can_close 返回格式"""
    ok: bool
    follow_up_question: str = ""
    issues: list[dict[str, Any]] = Field(default_factory=list)
    checks: CanCloseChecks = Field(default_factory=CanCloseChecks)
    position_info: PositionInfo | None = None


def perp_check_can_close_impl(
    address: str,
    coin: str,
    close_size: float | None = None,
    network: Network = "mainnet",
) -> dict:
    """平仓前检查（纯函数，可直接测试）"""
    result = service_check_can_close(
        address=address,
        coin=coin,
        close_size=close_size,
        network=network,
    )
    return CanCloseResponse.model_validate(result).model_dump()


@tool
def perp_check_can_close(
    address: str,
    coin: str,
    close_size: float | None = None,
    network: Network = "mainnet",
) -> CanCloseResponse:
    """
    检查是否可以平仓。

    在实际平仓前，验证以下条件：
    - 是否有仓位可以平
    - 是否有挂单需要撤销
    - 市场价格是否可用
    - 仓位是否接近强平价格

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"、"ETH"
        close_size: 平仓数量（不传则全部平仓）
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        CanCloseResponse: {
            "ok": bool,
            "follow_up_question": str,
            "issues": list[dict],
            "checks": CanCloseChecks,
            "position_info": PositionInfo | None,
        }
    """
    return perp_check_can_close_impl(
        address=address,
        coin=coin,
        close_size=close_size,
        network=network,
    )


if __name__ == "__main__":
    from rich import print
    print(perp_check_can_close_impl(address="0x1234567890abcdef1234567890abcdef12345678", coin="BTC"))
