"""
用户挂单查询
"""

from typing import Literal
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field
from src.services.hyperliquid import get_user_open_orders

Network = Literal["mainnet", "testnet"]


class OrderDetail(BaseModel):
    """单个订单详情"""
    model_config = ConfigDict(extra="ignore")

    oid: int | None = Field(default=None, description="订单唯一标识符")
    coin: str | None = Field(default=None, description="币种名称，如 BTC、ETH")
    side: str | None = Field(default=None, description="方向：A=Ask（卖出平多），B=Bid（买入平空）")
    sz: str | None = Field(default=None, description="订单数量/大小")
    limitPx: str | None = Field(default=None, description="限价价格（触发后执行价格）")
    orderType: str | None = Field(default=None, description="订单类型，如 Stop Market、Take Profit Market、Limit")
    origSz: str | None = Field(default=None, description="原始订单数量")
    tif: str | None = Field(default=None, description="Time in force，如 GTC、IOC")
    reduceOnly: bool | None = Field(default=None, description="是否只减仓（true=不会开新仓）")
    isTrigger: bool | None = Field(default=None, description="是否为触发单（价格触发后执行）")
    triggerCondition: str | None = Field(default=None, description="触发条件描述，如 Price below 65000、Price above 75000")
    triggerPx: str | None = Field(default=None, description="触发价格")
    isPositionTpsl: bool | None = Field(default=None, description="是否为仓位 TPSL 单（原生成对止盈止损）")
    timestamp: int | None = Field(default=None, description="订单创建时间戳（毫秒）")
    cloid: str | None = Field(default=None, description="Client Order ID（用户自定义订单标识）")
    children: list = Field(default_factory=list, description="子订单列表（条件单触发后的后续订单）")


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
    orders: list[OrderDetail] = Field(default_factory=list)


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
    获取 Hyperliquid 永续合约用户挂单（不含历史）。

    返回用户当前挂出的所有挂单，包含触发单（Stop Market / Take Profit Market）和 TPSL 止盈止损单。
    注意：这是 Hyperliquid 原始订单结构，TP/SL 可能由多个独立触发单组成（不成对）。

    参数:
        address: 用户钱包地址
        coin: 币种名称，如不传则返回所有币的挂单
        network: 网络类型，"mainnet" 或 "testnet"

    返回字段:
        ok: bool — 查询是否成功
        address: str — 钱包地址
        network: str — 网络类型
        coin: str | None — 本次查询的 coin（不传则查全部）
        has_open_orders: bool — 是否有挂单
        open_order_count: int — 挂单总数
        has_tpsl_orders: bool — 是否包含 TP/SL 触发单
        tpsl_order_count: int — TP/SL 触发单数量
        orders: list[OrderDetail] — 挂单列表，每个 OrderDetail 包含：
            oid: int — 订单唯一标识符（更新 TPSL 时需传入 existing_tp_oid / existing_sl_oid）
            coin: str — 币种
            side: str — 方向，A=Ask（卖出平多），B=Bid（买入平空）
            sz: str — 订单数量
            orderType: str — 订单类型，如 Stop Market、Take Profit Market、Limit
            reduceOnly: bool — 是否只减仓
            isTrigger: bool — 是否为触发单
            triggerCondition: str — 触发条件，如 Price below 65000
            triggerPx: str — 触发价格
            isPositionTpsl: bool — 是否为原生 TPSL 单（成对止盈止损）
            timestamp: int — 订单创建时间戳（毫秒）
            origSz: str — 原始订单数量
            limitPx: str — 限价价格（触发后执行价格）
            cloid: str — 客户端自定义订单 ID
            children: list — 子订单列表
    """
    return perp_get_open_orders_impl(address=address, coin=coin, network=network)


if __name__ == "__main__":
    from rich import print
    from dotenv import load_dotenv
    import os
    load_dotenv()
    EVM_ADDRESS = os.environ["EVM_ADDRESS"]
    print(perp_get_open_orders_impl(address=EVM_ADDRESS))
