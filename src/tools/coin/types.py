"""
CoinGecko 代币信息类型定义

本文件定义 coin 模块所有工具的输入/输出 Pydantic 模型，供 agent 调用时使用。
"""

from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# 代币价格
# =============================================================================

class CoinPriceResponse(BaseModel):
    """get_coin_price 返回格式"""
    ok: bool
    coin: str
    coin_id: str | None = None
    vs: str = "usd"
    price: float | None = None
    change_24h: float | None = None
    source: str = "coingecko"
    error: str | None = None


# =============================================================================
# 代币信息
# =============================================================================

class CoinInfoResponse(BaseModel):
    """get_coin_info 返回格式"""
    ok: bool
    coin: str
    coin_id: str | None = None
    name: str | None = None
    symbol: str | None = None
    price: float | None = None
    change_24h: float | None = None
    market_cap: float | None = None
    rank: int | None = None
    contract_address: str | None = None
    networks: dict | None = None
    source: str = "coingecko"
    error: str | None = None


# =============================================================================
# 代币搜索
# =============================================================================

class CoinCandidate(BaseModel):
    """搜索候选代币"""
    id: str | None = None
    name: str | None = None
    symbol: str | None = None
    rank: int | None = None
    platforms: dict | None = None


class SearchCoinsResponse(BaseModel):
    """search_coins 返回格式"""
    ok: bool
    query: str
    candidates: list[CoinCandidate] = Field(default_factory=list)
    source: str = "coingecko"
    error: str | None = None


# =============================================================================
# Trending
# =============================================================================

class TrendingCoin(BaseModel):
    """Trending 代币条目"""
    id: str | None = None
    name: str | None = None
    symbol: str | None = None
    rank: int | None = None
    market_cap_rank: int | None = None
    score: Any = None


class TrendingCoinsResponse(BaseModel):
    """get_trending_coins 返回格式"""
    ok: bool
    coins: list[dict] = Field(default_factory=list)
    source: str = "coingecko"
    error: str | None = None
