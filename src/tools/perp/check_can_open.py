"""
开仓前检查
"""

from typing import Any, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.hyperliquid.cli import check_can_open as service_check_can_open

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short"]
OrderType = Literal["market", "limit"]


class CanOpenChecks(BaseModel):
    """开仓检查的各项结果"""
    balance: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, Any] = Field(default_factory=dict)
    market: dict[str, Any] = Field(default_factory=dict)
    leverage: dict[str, Any] = Field(default_factory=dict)
    open_orders: dict[str, Any] = Field(default_factory=dict)
    entry_price: dict[str, Any] = Field(default_factory=dict)


class CanOpenResponse(BaseModel):
    """perp_check_can_open 返回格式"""
    ok: bool
    missing_fields: list[str] = Field(default_factory=list)
    follow_up_question: str = ""
    issues: list[dict[str, Any]] = Field(default_factory=list)
    checks: CanOpenChecks = Field(default_factory=CanOpenChecks)
    normalized_intent: dict[str, Any] = Field(default_factory=dict)


def perp_check_can_open_impl(
    address: str,
    coin: str | None = None,
    side: Side | None = None,
    size: float | None = None,
    leverage: float | None = None,
    order_type: OrderType = "market",
    entry_price: float | None = None,
    network: Network = "mainnet",
    intent: dict[str, Any] | None = None,
) -> dict:
    """开仓前检查（纯函数，可直接测试）"""
    result = service_check_can_open(
        address=address,
        coin=coin,
        side=side,
        size=size,
        leverage=leverage,
        order_type=order_type,
        entry_price=entry_price,
        network=network,
        intent=intent,
    )
    return CanOpenResponse.model_validate(result).model_dump()


@tool
def perp_check_can_open(
    address: str,
    coin: str | None = None,
    side: Side | None = None,
    size: float | None = None,
    leverage: float | None = None,
    order_type: OrderType = "market",
    entry_price: float | None = None,
    network: Network = "mainnet",
    intent: dict[str, Any] | None = None,
) -> CanOpenResponse:
    """
    检查是否可以开仓。

    在实际开仓前，验证以下条件：
    - 币种是否在永续合约列表中
    - 账户是否有可用余额
    - 是否已有同向或反向仓位
    - 杠杆是否合法
    - 是否有挂单需要撤销
    - 限价单价格是否合理

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"、"ETH"
        side: 方向，"long" 或 "short"
        size: 开仓数量
        leverage: 杠杆倍数
        order_type: 订单类型，"market" 或 "limit"
        entry_price: 限价单入场价格
        network: 网络类型，"mainnet" 或 "testnet"
        intent: 意图字典（可选，用于批量传参）

    返回:
        CanOpenResponse: {
            "ok": bool,
            "missing_fields": list[str],
            "follow_up_question": str,
            "issues": list[dict],
            "checks": CanOpenChecks,
            "normalized_intent": dict,
        }
    """
    return perp_check_can_open_impl(
        address=address,
        coin=coin,
        side=side,
        size=size,
        leverage=leverage,
        order_type=order_type,
        entry_price=entry_price,
        network=network,
        intent=intent,
    )


if __name__ == "__main__":
    from rich import print
    addr = "0x1234567890abcdef1234567890abcdef12345678"
    print(perp_check_can_open_impl(address=addr, coin="BTC", side="long", size=0.01, leverage=10))
