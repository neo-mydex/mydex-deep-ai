"""
Hyperliquid 交易 Action 工具包

按 Feature_HyperliquidAIAgentIntent.zh-CN.md 文档实现

Card 类型:
- OPEN_LONG: 开多
- OPEN_SHORT: 开空
- CLOSE_POSITION: 平仓
- SET_TPSL: 设置止盈止损
- VIEW_POSITION: 查看仓位
- UPDATE_LEVERAGE: 更新杠杆
"""

from .types import (
    CardType,
    MarginMode,
    OrderType,
    PositionSide,
    TradeSide,
    Network,
)

# OPEN_LONG / OPEN_SHORT
from .action_open import (
    build_open_long_params,
    build_open_short_params,
    action_open_position,
)

# CLOSE_POSITION
from .action_close import (
    build_close_position_params,
    action_close_position,
)

# SET_TPSL
from .action_tpsl import (
    build_set_tpsl_params,
    action_set_tpsl,
)

# UPDATE_LEVERAGE
from .action_leverage import (
    build_update_leverage_params,
    action_update_leverage,
)

# VIEW_POSITION
from .action_view_position import (
    build_view_position_params,
    action_view_position,
)

__all__ = [
    # Types
    "CardType",
    "MarginMode",
    "OrderType",
    "PositionSide",
    "TradeSide",
    "Network",
    # OPEN_LONG / OPEN_SHORT
    "build_open_long_params",
    "build_open_short_params",
    "action_open_position",
    # CLOSE_POSITION
    "build_close_position_params",
    "action_close_position",
    # SET_TPSL
    "build_set_tpsl_params",
    "action_set_tpsl",
    # UPDATE_LEVERAGE
    "build_update_leverage_params",
    "action_update_leverage",
    # VIEW_POSITION
    "build_view_position_params",
    "action_view_position",
]
