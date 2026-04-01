"""
Hyperliquid 永续合约查询工具包

对外暴露的 Tool (src/tools/perp/*.py):
- get_market: 市场数据（get_market_price, get_coin_info）
- get_positions: 仓位（get_user_positions, get_user_position）
- get_user_state: 账户（get_account_balance）
- get_open_orders: 挂单（get_user_open_orders）
- check_can_open: 开仓前验证（公开接口）
- check_can_close: 平仓前验证（公开接口）

内部模块 (src/tools/perp/_*.py):
- _hyperliquid_info: Hyperliquid 连接配置
- _normalize_intent: 意图标准化辅助函数
"""

# Query 模块 - 市场数据
from .get_market import (
    get_all_mids,
    get_perp_mid_price,
    get_meta,
    get_meta_and_asset_ctxs,
    get_perp_market_info,
    is_perp_listed,
    get_market_price,
    get_coin_info,
)

# Query 模块 - 用户状态
from .get_user_state import (
    get_user_state,
    get_account_balance,
)

# Query 模块 - 仓位
from .get_positions import (
    get_user_positions,
    get_user_position,
)

# Query 模块 - 挂单
from .get_open_orders import (
    get_open_orders,
    get_frontend_open_orders,
    get_user_open_orders,
)

# 开仓前检查（公开接口）
from .check_can_open import (
    check_can_open,
)

# 平仓前检查（公开接口）
from .check_can_close import (
    check_can_close,
)

# 类型定义
from .types import (  # noqa: E402, F401
    Network,
    Side,
    MarginMode,
    OrderType,
    MarketPriceResponse,
    PerpMarketInfoResponse,
    CoinInfoResponse,
    Position,
    UserPositionsResponse,
    UserPositionResponse,
    AccountBalanceResponse,
    Order,
    UserOpenOrdersResponse,
    CheckCanOpenRequest,
    LeverageValidation,
    EntryPriceEvaluation,
    CheckCanOpenResponse,
    CheckCanCloseRequest,
    PositionInfo,
    CheckCanCloseResponse,
)

__all__ = [
    # 市场数据
    "get_all_mids",
    "get_perp_mid_price",
    "get_meta",
    "get_meta_and_asset_ctxs",
    "get_perp_market_info",
    "is_perp_listed",
    "get_market_price",
    "get_coin_info",
    # 用户状态
    "get_user_state",
    "get_account_balance",
    # 仓位
    "get_user_positions",
    "get_user_position",
    # 挂单
    "get_open_orders",
    "get_frontend_open_orders",
    "get_user_open_orders",
    # 开仓检查
    "check_can_open",
    # 平仓检查
    "check_can_close",
    # 类型定义
    "Network",
    "Side",
    "MarginMode",
    "OrderType",
    "MarketPriceResponse",
    "PerpMarketInfoResponse",
    "CoinInfoResponse",
    "Position",
    "UserPositionsResponse",
    "UserPositionResponse",
    "AccountBalanceResponse",
    "Order",
    "UserOpenOrdersResponse",
    "CheckCanOpenRequest",
    "LeverageValidation",
    "EntryPriceEvaluation",
    "CheckCanOpenResponse",
    "CheckCanCloseRequest",
    "PositionInfo",
    "CheckCanCloseResponse",
]
