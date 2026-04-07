"""
Alchemy CLI 入口

直接运行: python -m src.services.alchemy.cli portfolio --address 0x... --networks eth,base
"""

import argparse
import json

from .service import get_wallet_portfolio, get_native_balance


def main():
    parser = argparse.ArgumentParser(description="Alchemy 链上资产查询")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # portfolio 子命令
    p_portfolio = subparsers.add_parser("portfolio", help="查询钱包多链资产组合")
    p_portfolio.add_argument("--address", required=True, help="钱包地址")
    p_portfolio.add_argument(
        "--networks",
        default="eth,base,arb,op",
        help="网络列表，逗号分隔（默认 eth,base,arb,op）",
    )
    p_portfolio.add_argument("--min-value", type=float, default=0.01, help="最小 USD 值过滤")

    # native-balance 子命令
    p_balance = subparsers.add_parser("native-balance", help="查询钱包原生代币余额")
    p_balance.add_argument("--address", required=True, help="钱包地址")
    p_balance.add_argument("--network", default="eth", help="网络名称（默认 eth）")

    args = parser.parse_args()

    if args.command == "portfolio":
        networks = [n.strip() for n in args.networks.split(",") if n.strip()]
        result = get_wallet_portfolio(
            address=args.address,
            networks=networks,
            min_value_usd=args.min_value,
        )
    elif args.command == "native-balance":
        result = get_native_balance(
            address=args.address,
            network=args.network,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
