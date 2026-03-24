"""
用户仓位查询模块
"""

from typing import Any

from src.tools.perp._hyperliquid_info import Network, _build_info
from src.tools.perp.get_market import get_all_mids


def get_user_state(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """获取用户状态"""
    info = _build_info(network, timeout=timeout)
    return info.user_state(address=address, dex=dex)


def get_user_positions(
    address: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取用户所有永续仓位（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "address": str,
        "network": str,
        "account_value": float | None,
        "withdrawable": float,
        "positions": [
            {
                "coin": str,
                "size": float,
                "side": "long" | "short" | "flat",
                "entry_px": float | None,
                "mark_px": float | None,
                "position_value": float | None,
                "unrealized_pnl": float | None,
                "leverage": int | None,
                "margin_type": "cross" | "isolated" | None,
                "liquidation_px": float | None,
            }
        ]
    }
    """
    state = get_user_state(address=address, network=network, dex=dex, timeout=timeout)
    mids = get_all_mids(network=network, dex=dex, timeout=timeout)

    result_positions: list[dict[str, Any]] = []
    for item in state.get("assetPositions", []):
        position = item.get("position", {})
        coin = position.get("coin")
        raw_size = position.get("szi")

        if not coin or raw_size is None:
            continue

        try:
            size = float(raw_size)
        except (TypeError, ValueError):
            continue

        # 判断方向
        if size > 0:
            side = "long"
        elif size < 0:
            side = "short"
        else:
            side = "flat"

        # 跳过 0 仓位
        if size == 0:
            continue

        # 获取当前市价
        mark_px_raw = mids.get(coin) if isinstance(mids, dict) else None
        try:
            mark_px = float(mark_px_raw) if mark_px_raw else None
        except (TypeError, ValueError):
            mark_px = None

        # 获取入场价
        entry_px_raw = position.get("entryPx")
        try:
            entry_px = float(entry_px_raw) if entry_px_raw else None
        except (TypeError, ValueError):
            entry_px = None

        # 获取强平价格
        liq_px_raw = position.get("liquidationPx")
        try:
            liquidation_px = float(liq_px_raw) if liq_px_raw else None
        except (TypeError, ValueError):
            liquidation_px = None

        # 获取保证金信息
        leverage_obj = position.get("leverage", {})
        leverage_val = leverage_obj.get("value") if isinstance(leverage_obj, dict) else None
        margin_type = leverage_obj.get("type") if isinstance(leverage_obj, dict) else None

        result_positions.append({
            "coin": coin,
            "size": size,
            "side": side,
            "entry_px": entry_px,
            "mark_px": mark_px,
            "position_value": position.get("positionValue"),
            "unrealized_pnl": position.get("unrealizedPnl"),
            "leverage": leverage_val,
            "margin_type": margin_type,
            "liquidation_px": liquidation_px,
        })

    # 账户价值
    margin_summary = state.get("marginSummary", {})
    account_value_raw = margin_summary.get("accountValue")
    try:
        account_value = float(account_value_raw) if account_value_raw else None
    except (TypeError, ValueError):
        account_value = None

    withdrawable_raw = state.get("withdrawable")
    try:
        withdrawable = float(withdrawable_raw) if withdrawable_raw else 0.0
    except (TypeError, ValueError):
        withdrawable = 0.0

    return {
        "ok": True,
        "address": address,
        "network": network,
        "account_value": account_value,
        "withdrawable": withdrawable,
        "positions": result_positions,
    }


def get_user_position(
    address: str,
    coin: str,
    network: Network = "mainnet",
    dex: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    获取用户指定币的仓位（给 Agent 用的标准化返回）

    返回结构:
    {
        "ok": bool,
        "address": str,
        "coin": str,
        "network": str,
        "has_position": bool,
        "position_side": "long" | "short" | "flat",
        "position_size": float | None,
        "entry_px": float | None,
        "mark_px": float | None,
        "leverage": int | None,
        "margin_type": "cross" | "isolated" | None,
        "liquidation_px": float | None,
        "unrealized_pnl": float | None,
    }
    """
    positions_data = get_user_positions(
        address=address,
        network=network,
        dex=dex,
        timeout=timeout,
    )

    matched_position = None
    for p in positions_data.get("positions", []):
        if p["coin"] == coin:
            matched_position = p
            break

    if matched_position is None:
        return {
            "ok": True,
            "address": address,
            "coin": coin,
            "network": network,
            "has_position": False,
            "position_side": "flat",
            "position_size": None,
            "entry_px": None,
            "mark_px": None,
            "leverage": None,
            "margin_type": None,
            "liquidation_px": None,
            "unrealized_pnl": None,
        }

    return {
        "ok": True,
        "address": address,
        "coin": coin,
        "network": network,
        "has_position": matched_position["size"] != 0,
        "position_side": matched_position["side"],
        "position_size": matched_position["size"],
        "entry_px": matched_position["entry_px"],
        "mark_px": matched_position["mark_px"],
        "leverage": matched_position["leverage"],
        "margin_type": matched_position["margin_type"],
        "liquidation_px": matched_position["liquidation_px"],
        "unrealized_pnl": matched_position["unrealized_pnl"],
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Hyperliquid 仓位查询")
    parser.add_argument("--action", choices=["all", "one"], required=True)
    parser.add_argument("--network", choices=["mainnet", "testnet"], default="mainnet")
    parser.add_argument("--address", required=True)
    parser.add_argument("--coin", default="BTC")
    parser.add_argument("--dex", default="")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    if args.action == "all":
        result = get_user_positions(
            address=args.address,
            network=args.network,
            dex=args.dex,
            timeout=args.timeout,
        )
    elif args.action == "one":
        result = get_user_position(
            address=args.address,
            coin=args.coin,
            network=args.network,
            dex=args.dex,
            timeout=args.timeout,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
