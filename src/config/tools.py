"""
Agent 工具绑定配置

这里是 Agent 看到的唯一工具注册入口。
src/tools 保持独立，不依赖 agent，可继续被 CLI 直接调用。
"""

from typing import Any, Literal

try:
    from langchain.tools import tool
except Exception:  # pragma: no cover - 兼容不同 langchain 版本
    from langchain_core.tools import tool

from src.tools.perp import (
    get_market_price as _get_market_price,
    get_coin_info as _get_perp_coin_info,
    get_user_positions as _get_user_positions,
    get_user_position as _get_user_position,
    get_account_balance as _get_account_balance,
    get_user_open_orders as _get_user_open_orders,
    check_can_open as _check_can_open,
    check_can_close as _check_can_close,
)
from src.tools.coin import (
    get_coin_price as _get_coin_price,
    search_coins as _search_coins,
    get_trending_coins as _get_trending_coins,
)
from src.tools.coin.coingecko import get_coin_info as _get_coin_info
from src.tools.user import (
    get_userid as _get_userid,
    get_jwt_expired_time as _get_jwt_expired_time,
    get_userid_and_expired_time as _get_userid_and_expired_time,
    get_wallet_portfolio as _get_wallet_portfolio,
    get_native_balance as _get_native_balance,
)


@tool
def perp_get_market_price(
    coin: str,
    network: Literal["mainnet", "testnet"] = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """查询 Hyperliquid 永续某币种价格。用于“BTC 现在多少”这类问题。"""
    return _get_market_price(coin=coin, network=network, timeout=timeout)


@tool
def perp_get_coin_info(
    coin: str,
    network: Literal["mainnet", "testnet"] = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """查询 Hyperliquid 永续币种信息。用于“是否上市、最大杠杆是多少”这类问题。"""
    return _get_perp_coin_info(coin=coin, network=network, timeout=timeout)


@tool
def perp_get_positions(
    address: str,
    network: Literal["mainnet", "testnet"] = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """查询某地址所有永续仓位。用于“帮我看全部持仓”。"""
    return _get_user_positions(address=address, network=network, dex=dex, timeout=timeout)


@tool
def perp_get_position(
    address: str,
    coin: str,
    network: Literal["mainnet", "testnet"] = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """查询某地址某币种仓位。用于“看我 ETH 仓位”。"""
    return _get_user_position(address=address, coin=coin, network=network, dex=dex, timeout=timeout)


@tool
def perp_get_balance(
    address: str,
    network: Literal["mainnet", "testnet"] = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """查询 Hyperliquid 账户余额。用于“账户可用资金/总资产是多少”。"""
    return _get_account_balance(address=address, network=network, dex=dex, timeout=timeout)


@tool
def perp_get_open_orders(
    address: str,
    coin: str | None = None,
    network: Literal["mainnet", "testnet"] = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """查询 Hyperliquid 挂单。用于“我现在有哪些挂单/止盈止损单”。"""
    return _get_user_open_orders(
        address=address,
        coin=coin,
        network=network,
        dex=dex,
        timeout=timeout,
    )


@tool
def perp_check_can_open(
    address: str,
    coin: str,
    side: Literal["long", "short"],
    size: float,
    leverage: float | None = None,
    order_type: Literal["market", "limit"] = "market",
    entry_price: float | None = None,
    network: Literal["mainnet", "testnet"] = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """判断是否可以开仓。用于“我能不能开某个单”，优先使用本工具，避免多工具重复查询。"""
    return _check_can_open(
        address=address,
        coin=coin,
        side=side,
        size=size,
        leverage=leverage,
        order_type=order_type,
        entry_price=entry_price,
        network=network,
        timeout=timeout,
    )


@tool
def perp_check_can_close(
    address: str,
    coin: str,
    close_size: float | None = None,
    network: Literal["mainnet", "testnet"] = "mainnet",
    timeout: float | None = None,
) -> dict[str, Any]:
    """判断是否可以平仓。用于“我能不能先把这个仓位平掉”。"""
    return _check_can_close(
        address=address,
        coin=coin,
        close_size=close_size,
        network=network,
        timeout=timeout,
    )


@tool
def coin_get_price(coin: str, vs: str = "usd") -> dict[str, Any]:
    """查询 CoinGecko 代币价格。用于“SOL 价格”这类问题。"""
    return _get_coin_price(coin=coin, vs=vs)


@tool
def coin_get_info(coin: str) -> dict[str, Any]:
    """查询 CoinGecko 代币详情。用于“市值、排名、24h 变化”等信息。"""
    return _get_coin_info(coin=coin)


@tool
def coin_search(query: str) -> dict[str, Any]:
    """搜索代币候选。用于用户只给了模糊名称时先做匹配。"""
    return _search_coins(query=query)


@tool
def coin_get_trending() -> dict[str, Any]:
    """查询 CoinGecko 热门代币列表。用于“最近热门币有哪些”。"""
    return _get_trending_coins()


@tool
def jwt_get_userid(jwt: str) -> str:
    """从 Privy JWT 提取用户 ID（sub）。"""
    return _get_userid(jwt=jwt)


@tool
def jwt_get_expired_time(jwt: str) -> str:
    """从 Privy JWT 提取过期时间（UTC ISO8601）。"""
    return _get_jwt_expired_time(jwt=jwt).isoformat()


@tool
def jwt_get_info(jwt: str) -> dict[str, Any]:
    """从 Privy JWT 提取用户 ID + 过期信息。"""
    return _get_userid_and_expired_time(jwt=jwt)


@tool
def wallet_get_assets(
    address: str,
    networks: list[str] | None = None,
    with_prices: bool = True,
    min_value_usd: float = 0.01,
) -> dict[str, Any]:
    """查询钱包多链资产组合。用于“我钱包里有什么资产”。"""
    return _get_wallet_portfolio(
        address=address,
        networks=networks,
        with_prices=with_prices,
        min_value_usd=min_value_usd,
    )


@tool
def wallet_get_native_balance(
    address: str,
    network: str = "eth",
) -> dict[str, Any]:
    """查询钱包原生代币余额。用于“ETH/Base 链原生币余额是多少”。"""
    return _get_native_balance(address=address, network=network)


AGENT_TOOLS = [
    # perp 查询（Hyperliquid 永续合约）
    perp_get_market_price,
    perp_get_coin_info,
    perp_get_positions,
    perp_get_position,
    perp_get_balance,
    perp_get_open_orders,
    perp_check_can_open,
    perp_check_can_close,
    # coin 查询（CoinGecko）
    coin_get_price,
    coin_get_info,
    coin_search,
    coin_get_trending,
    # user 查询（JWT + 链上资产）
    jwt_get_userid,
    jwt_get_expired_time,
    jwt_get_info,
    wallet_get_assets,
    wallet_get_native_balance,
]
