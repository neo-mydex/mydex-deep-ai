"""
Hyperliquid 永续合约类型定义

本文件定义 perp 模块所有工具的输入/输出 Pydantic 模型，供 agent 调用时使用。
"""

from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# 枚举类型
# =============================================================================

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short", "flat"]
MarginMode = Literal["cross", "isolated"]
OrderType = Literal["market", "limit"]


# =============================================================================
# 市场数据
# =============================================================================

class MarketPriceResponse(BaseModel):
    """get_market_price 返回格式"""
    ok: bool
    network: Network
    coin: str
    mark_price: float | None = None
    mark_price_raw: str | None = None
    is_listed: bool


class PerpMarketInfoResponse(BaseModel):
    """get_perp_market_info 返回格式"""
    coin: str
    listed: bool
    max_leverage: int | None = None
    sz_decimals: int
    is_delisted: bool
    only_isolated: bool
    margin_table_id: int | None = None


class CoinInfoResponse(BaseModel):
    """get_coin_info 返回格式"""
    ok: bool
    coin: str
    network: Network
    is_listed: bool
    max_leverage: int | None = None
    only_isolated: bool
    sz_decimals: int | None = None


# =============================================================================
# 仓位
# =============================================================================

class Position(BaseModel):
    """单个仓位信息"""
    coin: str
    size: float
    side: Side
    entry_px: float | None = None
    mark_px: float | None = None
    position_value: float | None = None
    unrealized_pnl: float | None = None
    leverage: int | None = None
    margin_type: MarginMode | None = None
    liquidation_px: float | None = None


class UserPositionsResponse(BaseModel):
    """get_user_positions 返回格式"""
    ok: bool
    address: str
    network: Network
    account_value: float | None = None
    withdrawable: float
    positions: list[Position] = Field(default_factory=list)


class UserPositionResponse(BaseModel):
    """get_user_position 返回格式"""
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
    margin_type: MarginMode | None = None
    liquidation_px: float | None = None
    unrealized_pnl: float | None = None


# =============================================================================
# 账户余额
# =============================================================================

class AccountBalanceResponse(BaseModel):
    """get_account_balance 返回格式"""
    ok: bool
    address: str
    network: Network
    withdrawable: float
    account_value: float | None = None
    total_margin_used: float | None = None


# =============================================================================
# 挂单
# =============================================================================

class Order(BaseModel):
    """单个挂单信息"""
    coin: str
    limit_px: str
    oid: int
    side: Literal["A", "B"]  # A=Buy, B=Sell
    sz: str
    timestamp: int | None = None


class UserOpenOrdersResponse(BaseModel):
    """get_user_open_orders 返回格式"""
    ok: bool
    address: str
    network: Network
    coin: str | None = None
    has_open_orders: bool
    open_order_count: int
    has_tpsl_orders: bool
    tpsl_order_count: int
    orders: list[dict] = Field(default_factory=list)


# =============================================================================
# 开仓/平仓检查
# =============================================================================

class CheckCanOpenRequest(BaseModel):
    """check_can_open 输入格式"""
    address: str
    coin: str | None = None
    side: Side | None = None
    size: float | None = None
    leverage: float | None = None
    order_type: OrderType = "market"
    entry_price: float | None = None
    network: Network = "mainnet"
    timeout: float | None = None


class LeverageValidation(BaseModel):
    """杠杆验证结果"""
    ok: bool
    coin: str
    requested: float | int
    max_allowed: int | None = None
    reason: str


class EntryPriceEvaluation(BaseModel):
    """限价开仓价格评估"""
    ok: bool
    coin: str
    side: Side
    order_type: OrderType
    target_price: float
    mid_price: float | None = None
    deviation_ratio: float | None = None
    deviation_warn: bool = False
    direction_ok_for_limit: bool = False
    would_fill_immediately: bool = False


class CheckCanOpenResponse(BaseModel):
    """check_can_open 返回格式"""
    ok: bool
    missing_fields: list[str] = Field(default_factory=list)
    follow_up_question: str = ""
    issues: list[dict] = Field(default_factory=list)
    checks: dict = Field(default_factory=dict)


class CheckCanCloseRequest(BaseModel):
    """check_can_close 输入格式"""
    address: str
    coin: str
    close_size: float | None = None
    network: Network = "mainnet"
    timeout: float | None = None


class PositionInfo(BaseModel):
    """仓位信息摘要"""
    has_position: bool
    position_side: Side
    position_size: float | None = None
    close_size: float


class CheckCanCloseResponse(BaseModel):
    """check_can_close 返回格式"""
    ok: bool
    follow_up_question: str = ""
    issues: list[dict] = Field(default_factory=list)
    checks: dict = Field(default_factory=dict)
    position_info: PositionInfo | None = None
