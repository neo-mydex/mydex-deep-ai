"""
Hyperliquid 永续合约服务层

提供纯业务逻辑，不含 @tool 装饰器。
导出 service 层的业务函数供 agent tools 使用。
"""

from dotenv import load_dotenv
load_dotenv()

from .service import (
    get_perp_market_info,
    is_perp_listed,
    get_market_price,
    get_coin_info,
    get_account_balance,
    get_user_positions,
    get_user_position,
    get_user_open_orders,
    _is_tpsl_order,
    validate_leverage,
    evaluate_entry_price,
    check_can_open,
    check_can_close,
    get_user_fills_by_time,
    get_order_detail_by_oid,
    get_historical_orders,
)

from .normalize import (
    Side,
    OrderType,
    normalize_side,
    normalize_order_type,
    normalize_coin,
    normalize_leverage,
    normalize_size,
    normalize_intent,
)

__all__ = [
    # market
    "get_perp_market_info",
    "is_perp_listed",
    "get_market_price",
    "get_coin_info",
    # account
    "get_account_balance",
    # positions
    "get_user_positions",
    "get_user_position",
    # orders
    "get_user_open_orders",
    "_is_tpsl_order",
    # checks
    "validate_leverage",
    "evaluate_entry_price",
    "check_can_open",
    "check_can_close",
    # historical
    "get_user_fills_by_time",
    "get_order_detail_by_oid",
    "get_historical_orders",
    # normalize
    "Side",
    "OrderType",
    "normalize_side",
    "normalize_order_type",
    "normalize_coin",
    "normalize_leverage",
    "normalize_size",
    "normalize_intent",
]
