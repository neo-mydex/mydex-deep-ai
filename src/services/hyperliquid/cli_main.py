"""
Hyperliquid CLI 入口

直接运行: python -m src.services.hyperliquid.cli_main <command>
"""

import argparse
import json

from .cli import (
    get_market_price,
    get_coin_info,
    get_perp_market_info,
    get_all_mids,
    get_user_positions,
    get_user_position,
    get_account_balance,
    get_user_open_orders,
)


def main():
    parser = argparse.ArgumentParser(description="Hyperliquid CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get_market subcommand
    p_market = subparsers.add_parser("get_market", help="获取市场数据")
    p_market.add_argument("--action", choices=["price", "coin_info", "perp_market_info", "all_mids"], required=True)
    p_market.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    p_market.add_argument("--coin", default="BTC")
    p_market.add_argument("--timeout", type=float, default=10.0)

    # get_positions subcommand
    p_positions = subparsers.add_parser("get_positions", help="获取仓位")
    p_positions.add_argument("--action", choices=["all", "one"], required=True)
    p_positions.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    p_positions.add_argument("--address", required=True)
    p_positions.add_argument("--coin", default="BTC")
    p_positions.add_argument("--dex", default="")
    p_positions.add_argument("--timeout", type=float, default=10.0)

    # get_balance subcommand
    p_balance = subparsers.add_parser("get_balance", help="获取账户余额")
    p_balance.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    p_balance.add_argument("--address", required=True)
    p_balance.add_argument("--dex", default="")
    p_balance.add_argument("--timeout", type=float, default=10.0)

    # get_open_orders subcommand
    p_orders = subparsers.add_parser("get_open_orders", help="获取挂单")
    p_orders.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    p_orders.add_argument("--address", required=True)
    p_orders.add_argument("--coin", default=None)
    p_orders.add_argument("--dex", default="")
    p_orders.add_argument("--timeout", type=float, default=10.0)

    args = parser.parse_args()

    if args.command == "get_market":
        if args.action == "price":
            result = get_market_price(coin=args.coin, network=args.network, timeout=args.timeout)
        elif args.action == "coin_info":
            result = get_coin_info(coin=args.coin, network=args.network, timeout=args.timeout)
        elif args.action == "perp_market_info":
            result = get_perp_market_info(coin=args.coin, network=args.network, timeout=args.timeout)
        elif args.action == "all_mids":
            result = get_all_mids(network=args.network, timeout=args.timeout)
    elif args.command == "get_positions":
        if args.action == "all":
            result = get_user_positions(address=args.address, network=args.network, dex=args.dex, timeout=args.timeout)
        elif args.action == "one":
            result = get_user_position(address=args.address, coin=args.coin, network=args.network, dex=args.dex, timeout=args.timeout)
    elif args.command == "get_balance":
        result = get_account_balance(address=args.address, network=args.network, dex=args.dex, timeout=args.timeout)
    elif args.command == "get_open_orders":
        result = get_user_open_orders(address=args.address, coin=args.coin, network=args.network, dex=args.dex, timeout=args.timeout)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
