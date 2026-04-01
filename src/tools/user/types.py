"""
User/Wallet 类型定义

本文件定义 user 模块所有工具的输入/输出 Pydantic 模型，供 agent 调用时使用。
"""

from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# JWT 解析
# =============================================================================

class JwtDecodeResponse(BaseModel):
    """get_userid_and_expired_time 返回格式"""
    user_id: str
    expire_at_utc: str
    is_expired: bool


# =============================================================================
# 链上资产
# =============================================================================

class NetworkBreakdown(BaseModel):
    """单网络资产汇总"""
    total_value_usd: float
    asset_count: int
    assets: list["Asset"] = Field(default_factory=list)


class Asset(BaseModel):
    """单个资产条目"""
    network: str
    token_address: str | None = None
    symbol: str | None = None
    name: str | None = None
    decimals: int | None = None
    balance: float
    price_usd: float | None = None
    value_usd: float | None = None
    is_native: bool = False
    logo: str | None = None


class WalletPortfolioResponse(BaseModel):
    """get_wallet_portfolio 返回格式"""
    ok: bool
    address: str
    networks: list[str] = Field(default_factory=list)
    total_value_usd: float
    asset_count: int
    assets: list[Asset] = Field(default_factory=list)
    breakdown: dict[str, dict] = Field(default_factory=dict)
    error: str | None = None


class NativeBalanceResponse(BaseModel):
    """get_native_balance 返回格式"""
    ok: bool
    address: str
    network: str
    symbol: str
    balance: float
    value_usd: float | None = None
    error: str | None = None


# =============================================================================
# 网络类型
# =============================================================================

SupportedNetwork = Literal["eth", "base", "arb", "op", "matic", "bsc"]
