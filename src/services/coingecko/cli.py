"""
CoinGecko CLI 入口

直接运行: python -m src.services.coingecko <command>
"""

import argparse
import json

from .service import (
    get_coin_price,
    get_coin_info,
    search_coins,
    get_trending_coins,
)


def main():
    parser = argparse.ArgumentParser(description="CoinGecko 代币信息查询")
    parser.add_argument("--action", choices=["price", "info", "search", "trending"], required=True)
    parser.add_argument("--coin", default=None, help="代币符号、名称或合约地址")
    parser.add_argument("--vs", default="usd", help="计价货币 (默认 usd)")
    args = parser.parse_args()

    if args.action == "price":
        if not args.coin:
            print("Error: --coin required for price action")
            exit(1)
        result = get_coin_price(coin=args.coin, vs=args.vs)
    elif args.action == "info":
        if not args.coin:
            print("Error: --coin required for info action")
            exit(1)
        result = get_coin_info(coin=args.coin, vs=args.vs)
    elif args.action == "search":
        if not args.coin:
            print("Error: --coin required for search action")
            exit(1)
        result = search_coins(query=args.coin)
    elif args.action == "trending":
        result = get_trending_coins()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
