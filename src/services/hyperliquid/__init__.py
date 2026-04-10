"""
Hyperliquid 永续合约服务层

提供纯业务逻辑，不含 @tool 装饰器。
"""

from .info import (
    Network,
    _build_info,
    get_all_mids,
    get_meta,
    get_meta_and_asset_ctxs,
    user_state,
    open_orders,
    frontend_open_orders,
    user_fills_by_time,
    query_order_by_oid,
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

from .cli import (
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
)

__all__ = [
    # info
    "Network",
    "_build_info",
    "get_all_mids",
    "get_meta",
    "get_meta_and_asset_ctxs",
    "user_state",
    "open_orders",
    "frontend_open_orders",
    "user_fills_by_time",
    "query_order_by_oid",
    # normalize
    "Side",
    "OrderType",
    "normalize_side",
    "normalize_order_type",
    "normalize_coin",
    "normalize_leverage",
    "normalize_size",
    "normalize_intent",
    # cli
    "get_perp_market_info",
    "is_perp_listed",
    "get_market_price",
    "get_coin_info",
    "get_account_balance",
    "get_user_positions",
    "get_user_position",
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
]
