"""
用户挂单查询
"""

from typing import Any, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.hyperliquid.cli import get_user_open_orders

Network = Literal["mainnet", "testnet"]


class OrderDetail(BaseModel):
    """单个订单详情（原始结构）"""
    coin: str | None = None
    side: str | None = None
    sz: str | float | None = None
    price: str | float | None = None
    orderType: str | None = None
    triggerCondition: str | None = None
    triggerPx: str | float | None = None
    isPositionTpsl: bool | None = None
    # 其他字段保留为 Any
    extra: dict[str, Any] = Field(default_factory=dict)


class OpenOrdersResponse(BaseModel):
    """perp_get_open_orders 返回格式"""
    ok: bool
    address: str
    network: Network
    coin: str | None = None
    has_open_orders: bool
    open_order_count: int
    has_tpsl_orders: bool
    tpsl_order_count: int
    orders: list[dict[str, Any]] = Field(default_factory=list)


def perp_get_open_orders_impl(
    address: str,
    coin: str | None = None,
    network: Network = "mainnet",
) -> dict:
    """获取用户挂单（纯函数，可直接测试）"""
    result = get_user_open_orders(address=address, coin=coin, network=network)
    return OpenOrdersResponse.model_validate(result).model_dump()


@tool
def perp_get_open_orders(
    address: str,
    coin: str | None = None,
    network: Network = "mainnet",
) -> OpenOrdersResponse:
    """
    获取 Hyperliquid 永续合约用户挂单。

    用于查询用户当前挂出的永续合约订单，包括普通挂单和 TP/SL 止盈止损挂单。

    参数:
        address: 用户钱包地址
        coin: 币种名称，如不传则返回所有币的挂单
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        OpenOrdersResponse: {
            "ok": bool,
            "address": str,
            "network": str,
            "coin": str | None,
            "has_open_orders": bool,
            "open_order_count": int,
            "has_tpsl_orders": bool,
            "tpsl_order_count": int,
            "orders": list[dict],
        }
    """
    return perp_get_open_orders_impl(address=address, coin=coin, network=network)


if __name__ == "__main__":
    from pprint import pprint
    pprint(perp_get_open_orders_impl(address="0x1234567890abcdef1234567890abcdef12345678"))
