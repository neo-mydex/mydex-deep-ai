"""Agent 工具绑定配置（纯收集）"""
from src.tools.perp import (
    perp_get_market_price,
    perp_get_coin_info,
    perp_get_positions,
    perp_get_position,
    perp_get_balance,
    perp_get_open_orders,
    perp_check_can_open,
    perp_check_can_close,
)
from src.tools.coin import (
    coin_get_price,
    coin_get_info,
    coin_search,
    coin_get_trending,
)
from src.tools.user import (
    wallet_get_assets,
    wallet_get_native_balance,
)
from src.tools.user.decode_jwt import (
    get_userid,
    get_jwt_expired_time,
    get_userid_and_expired_time,
)

AGENT_TOOLS = [
    # perp
    perp_get_market_price,
    perp_get_coin_info,
    perp_get_positions,
    perp_get_position,
    perp_get_balance,
    perp_get_open_orders,
    perp_check_can_open,
    perp_check_can_close,
    # coin
    coin_get_price,
    coin_get_info,
    coin_search,
    coin_get_trending,
    # user
    get_userid,
    get_jwt_expired_time,
    get_userid_and_expired_time,
    wallet_get_assets,
    wallet_get_native_balance,
]
