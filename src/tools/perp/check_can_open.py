"""
开仓前检查
"""

from typing import Any, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field, model_validator
from src.services.hyperliquid import check_can_open as service_check_can_open

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short"]
OrderType = Literal["market", "limit"]


class CanOpenInput(BaseModel):
    """perp_check_can_open 输入参数校验"""
    address: str
    coin: str
    side: Side
    usdc_margin: float | None = Field(default=None, ge=0)  # USDC 保证金
    coin_size: float | None = Field(default=None, ge=0)    # 币本位头寸
    leverage: float | None = Field(default=None, ge=0)
    order_type: OrderType = "market"
    entry_price: float | None = None
    network: Network = "mainnet"

    @model_validator(mode="after")
    def check_exactly_one_size(self) -> "CanOpenInput":
        if self.usdc_margin is None and self.coin_size is None:
            raise ValueError("usdc_margin 和 coin_size 至少需要提供一个")
        if self.usdc_margin is not None and self.coin_size is not None:
            raise ValueError("usdc_margin 和 coin_size 二选一，不可同时指定")
        if self.leverage is None or self.leverage <= 0:
            raise ValueError("leverage 必须 > 0")
        if self.usdc_margin is not None and self.usdc_margin <= 0:
            raise ValueError("usdc_margin 必须 > 0")
        if self.coin_size is not None and self.coin_size <= 0:
            raise ValueError("coin_size 必须 > 0")
        return self


class CanOpenResponse(BaseModel):
    """perp_check_can_open 返回格式"""
    ok: bool
    is_add: bool = False  # True=补仓（加仓），False=开新仓
    leverage_to_use: float | None = None  # 实际使用的杠杆
    coin_size: float | None = None   # 实际下单的合约张数（币本位）
    usdc_margin: float | None = None    # 实际使用的保证金
    corrections: list[str] = Field(default_factory=list)
    issues: list[dict[str, Any]] = Field(default_factory=list)
    follow_up_question: str = ""


def perp_check_can_open_impl(
    address: str,
    coin: str,
    side: Side,
    usdc_margin: float | None = None,
    coin_size: float | None = None,
    leverage: float | None = None,
    order_type: OrderType = "market",
    entry_price: float | None = None,
    network: Network = "mainnet",
) -> dict:
    """开仓前检查（纯函数，可直接测试）"""
    # 参数校验
    CanOpenInput(
        address=address,
        coin=coin,
        side=side,
        usdc_margin=usdc_margin,
        coin_size=coin_size,
        leverage=leverage,
        order_type=order_type,
        entry_price=entry_price,
        network=network,
    )
    result = service_check_can_open(
        address=address,
        coin=coin,
        side=side,
        usdc_margin=usdc_margin,
        coin_size=coin_size,
        leverage=leverage,
        order_type=order_type,
        entry_price=entry_price,
        network=network,
    )
    return CanOpenResponse.model_validate(result).model_dump()


@tool
def perp_check_can_open(
    address: str,
    coin: str,
    side: Side,
    usdc_margin: float | None = None,
    coin_size: float | None = None,
    leverage: float | None = None,
    order_type: OrderType = "market",
    entry_price: float | None = None,
    network: Network = "mainnet",
) -> CanOpenResponse:
    """
    【强制】开仓前必须调用的可行性校验工具。

    ⚠️ 重要：调用 confirm_perp_open_order 之前，必须先调用本工具。
    禁止跳过本工具直接调用 confirm_perp_open_order。

    校验内容：
    - usdc_margin 和 coin_size 至少提供一个，且必须 > 0
    - 账户可用余额是否充足
    - 是否有反向仓位（需先平仓）
    - 是否有未成交主单（非 TPSL）
    - 杠杆是否超限（自动纠正）
    - 限价单价格是否偏离过大

    若 ok=true：用返回的 leverage_to_use / coin_size / usdc_margin 继续调用 confirm_perp_open_order
    若 ok=false：根据 issues 告知用户问题，不调用 confirm

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"、"ETH"
        side: 方向，"long" 或 "short"
        usdc_margin: USDC 保证金（如 1000 = 投入 1000 USDC）
        coin_size: 币本位头寸（如 0.1 = 0.1 BTC）
        leverage: 杠杆倍数
        order_type: 订单类型，"market" 或 "limit"
        entry_price: 限价单入场价格
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        CanOpenResponse: {
            "ok": bool,
            "is_add": bool,
            "leverage_to_use": float,
            "coin_size": float,
            "usdc_margin": float,
            "corrections": list[str],
            "issues": list[dict],
            "follow_up_question": str,
        }
    """
    return perp_check_can_open_impl(
        address=address,
        coin=coin,
        side=side,
        usdc_margin=usdc_margin,
        coin_size=coin_size,
        leverage=leverage,
        order_type=order_type,
        entry_price=entry_price,
        network=network,
    )


if __name__ == "__main__":
    from rich import print
    addr = "0x269488c0F8D595CF47aAA91AC6Ef896f9F63cc9E"
    print(perp_check_can_open_impl(
        address=addr, 
        coin="BTC", 
        side="long", 
        usdc_margin=5, 
        leverage=18, 
        network="mainnet"
    ))
