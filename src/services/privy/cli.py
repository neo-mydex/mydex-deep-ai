"""
Privy CLI 入口

直接运行: python -m src.services.privy.cli profile --jwt <token>
"""

import argparse
import json
import os

from .service import get_user_profile


def main():
    parser = argparse.ArgumentParser(description="Privy 用户信息查询")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # profile 子命令
    p_profile = subparsers.add_parser("profile", help="获取用户资料（含钱包地址）")
    p_profile.add_argument("--jwt", required=True, help="Privy JWT token")

    args = parser.parse_args()

    if args.command == "profile":
        result = get_user_profile(args.jwt)
        result = get_user_profile(args.jwt)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
