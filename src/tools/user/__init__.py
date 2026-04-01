"""
用户相关工具包

对外暴露的 Tool (src/tools/user/*.py):
- decode_jwt: 解析 Privy JWT token，提取用户信息
- get_wallet_portfolio: 查询钱包多链资产组合
- get_native_balance: 查询钱包原生代币余额

内部模块 (src/tools/user/_*.py):
- _alchemy_client: Alchemy API 客户端
- _network: 网络配置和标准化
"""

from .decode_jwt import get_userid, get_jwt_expired_time, get_userid_and_expired_time
from .get_onchain_assets import get_wallet_portfolio, get_native_balance
from .types import (  # noqa: E402, F401
    JwtDecodeResponse,
    NetworkBreakdown,
    Asset,
    WalletPortfolioResponse,
    NativeBalanceResponse,
    SupportedNetwork,
)

__all__ = [
    # JWT 解析
    "get_userid",
    "get_jwt_expired_time",
    "get_userid_and_expired_time",
    # 链上资产
    "get_wallet_portfolio",
    "get_native_balance",
    # 类型定义
    "JwtDecodeResponse",
    "NetworkBreakdown",
    "Asset",
    "WalletPortfolioResponse",
    "NativeBalanceResponse",
    "SupportedNetwork",
]
