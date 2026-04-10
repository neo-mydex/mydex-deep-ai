"""
平仓前检查
"""

from typing import Any, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field, model_validator
from src.services.hyperliquid import check_can_close as service_check_can_close

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short", "flat"]


class CanCloseInput(BaseModel):
    """perp_check_can_close 输入参数校验"""
    coin: str
    address: str
    close_size: float | None = Field(default=None, gt=0)              # 币本位张数
    close_size_in_usdc: float | None = Field(default=None, gt=0)   # USDC 价值
    close_ratio: float | None = Field(default=None, gt=0)           # 0-1 比例
    network: Network = "mainnet"

    @model_validator(mode="after")
    def exactly_one_input(self) -> "CanCloseInput":
        inputs = [self.close_size, self.close_size_in_usdc, self.close_ratio]
        provided = [x for x in inputs if x is not None]
        if len(provided) != 1:
            raise ValueError("close_size / close_size_in_usdc / close_ratio 三选一，不可同时指定")
        if self.close_ratio is not None and not (0 < self.close_ratio <= 1):
            raise ValueError("close_ratio 必须在 (0, 1] 范围内")
        return self


class CanCloseResponse(BaseModel):
    """perp_check_can_close 返回格式"""
    ok: bool                              # 是否可以平仓
    has_position: bool                   # 是否有仓位
    position_side: Side                  # 仓位方向
    position_size: float | None = None   # 当前持仓量（币本位）
    close_size: float | None = None     # 实际平仓量（币本位）
    close_size_in_usdc: float | None = None  # 实际平仓量（USDC 价值）
    close_ratio: float | None = None     # 实际平仓比例
    corrections: list[str] = Field(default_factory=list)  # 警告/纠正
    issues: list[dict[str, Any]] = Field(default_factory=list)  # 错误列表（block）
    follow_up_question: str = ""


def perp_check_can_close_impl(
    address: str,
    coin: str,
    close_size: float | None = None,
    close_size_in_usdc: float | None = None,
    close_ratio: float | None = None,
    network: Network = "mainnet",
) -> dict:
    """平仓前检查（纯函数，可直接测试）"""
    # 参数校验（三选一）
    CanCloseInput(
        address=address,
        coin=coin,
        close_size=close_size,
        close_size_in_usdc=close_size_in_usdc,
        close_ratio=close_ratio,
        network=network,
    )
    result = service_check_can_close(
        address=address,
        coin=coin,
        close_size=close_size,
        close_size_in_usdc=close_size_in_usdc,
        close_ratio=close_ratio,
        network=network,
    )
    return CanCloseResponse.model_validate(result).model_dump()


@tool
def perp_check_can_close(
    address: str,
    coin: str,
    close_size: float | None = None,
    close_size_in_usdc: float | None = None,
    close_ratio: float | None = None,
    network: Network = "mainnet",
) -> CanCloseResponse:
    """
    【强制】平仓前必须调用的可行性校验工具。

    ⚠️ 重要：调用 confirm_perp_close_position 之前，必须先调用本工具。

    校验内容：
    - 是否有仓位可以平
    - 是否有未成交主单（非 TPSL）
    - 市场价格是否可用
    - 平仓数量是否合法

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"、"ETH"
        close_size: 平仓数量（币本位），如 0.5 BTC
        close_size_in_usdc: 平仓价值（USDC），如 34000 USDC
        close_ratio: 平仓比例（0-1），如 0.3 = 平 30%
        network: 网络类型，"mainnet" 或 "testnet"

    注意: close_size / close_size_in_usdc / close_ratio 三选一，不可同时指定

    返回:
        CanCloseResponse: {
            "ok": bool,
            "has_position": bool,
            "position_side": str,
            "position_size": float,
            "close_size": float,
            "close_size_in_usdc": float,
            "close_ratio": float,
            "corrections": list[str],
            "issues": list[dict],
            "follow_up_question": str,
        }
    """
    return perp_check_can_close_impl(
        address=address,
        coin=coin,
        close_size=close_size,
        close_size_in_usdc=close_size_in_usdc,
        close_ratio=close_ratio,
        network=network,
    )


if __name__ == "__main__":
    from rich import print
    addr = "0x269488c0F8D595CF47aAA91AC6Ef896f9F63cc9E"
    # print("=== 只有 close_size ===")
    # print(perp_check_can_close_impl(address=addr, coin="BTC", close_size=0.0001))
    # print()
    # print("=== 只有 close_size_in_usdc ===")
    # print(perp_check_can_close_impl(address=addr, coin="BTC", close_size_in_usdc=10))
    # print()
    print("=== 只有 close_ratio ===")
    print(perp_check_can_close_impl(address=addr, coin="BTC", close_ratio=3))
    # print()
    # print("=== 全平 ===")
    # print(perp_check_can_close_impl(address=addr, coin="BTC"))
