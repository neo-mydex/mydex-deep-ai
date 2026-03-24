"""
用户状态查询模块
"""

from typing import Any

from src.tools.perp._hyperliquid_info import Network, _build_info


def get_user_state(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取用户账户状态

    返回结构:
    {
        "assetPositions": [...],
        "crossMarginSummary": {...},
        "marginSummary": {...},
        "withdrawable": str,
    }
    """
    info = _build_info(network, timeout=timeout)
    return info.user_state(address=address, dex=dex)


def get_account_balance(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取账户余额信息（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "address": str,
        "network": str,
        "withdrawable": float,
        "account_value": float | None,
        "total_margin_used": float | None,
    }
    """
    state = get_user_state(address=address, network=network, dex=dex, timeout=timeout)

    withdrawable = state.get("withdrawable", "0")
    try:
        withdrawable_val = float(withdrawable)
    except (TypeError, ValueError):
        withdrawable_val = 0.0

    margin_summary = state.get("marginSummary", {})
    account_value = margin_summary.get("accountValue")
    if account_value is not None:
        try:
            account_value = float(account_value)
        except (TypeError, ValueError):
            account_value = None

    total_margin_used = margin_summary.get("totalMarginUsed")
    if total_margin_used is not None:
        try:
            total_margin_used = float(total_margin_used)
        except (TypeError, ValueError):
            total_margin_used = None

    return {
        "ok": True,
        "address": address,
        "network": network,
        "withdrawable": withdrawable_val,
        "account_value": account_value,
        "total_margin_used": total_margin_used,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Hyperliquid 用户状态查询")
    parser.add_argument("--action", choices=["state", "balance"], required=True)
    parser.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    parser.add_argument("--address", required=True)
    parser.add_argument("--dex", default="")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    if args.action == "state":
        result = get_user_state(
            address=args.address,
            network=args.network,
            dex=args.dex,
            timeout=args.timeout,
        )
    elif args.action == "balance":
        result = get_account_balance(
            address=args.address,
            network=args.network,
            dex=args.dex,
            timeout=args.timeout,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 
