"""
Alchemy Solana RPC 封装
"""

from dotenv import load_dotenv
load_dotenv()

import os, json, urllib.request
from typing import Any

ALCHEMY_SOLANA_BASE = f"https://solana-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_API_KEY')}"


def _post_solana(method: str, params: list) -> dict[str, Any]:
    """发起 Solana RPC 请求"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    req = urllib.request.Request(
        ALCHEMY_SOLANA_BASE,
        data=json.dumps(payload).encode(),
        headers={"accept": "application/json", "content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def get_solana_portfolio(sol_address: str) -> dict[str, Any]:
    """
    查询 Solana 钱包所有代币资产

    参数:
        sol_address: Solana 钱包地址

    返回:
        {
            "ok": bool,
            "address": str,
            "total_value_usd": float,
            "assets": [...],
            "error": str | None,
        }
    """
    try:
        result = _post_solana(
            "getTokenAccountsByOwner",
            [
                sol_address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ],
        )

        accounts = result.get("result", {}).get("value", [])
        assets = []

        for acc in accounts:
            info = acc.get("account", {}).get("data", {})
            parsed = info.get("parsed", {})
            if not parsed:
                continue
            mint = parsed.get("info", {}).get("mint")
            amount = parsed.get("info", {}).get("tokenAmount", {})
            decimals = amount.get("decimals", 0)
            ui_amount = amount.get("uiAmount", 0)

            if ui_amount > 0:
                assets.append({
                    "network": "sol-mainnet",
                    "symbol": mint[:8] if mint else "UNKNOWN",
                    "name": mint or "Unknown Token",
                    "balance": ui_amount,
                    "value_usd": None,
                })

        return {
            "ok": True,
            "address": sol_address,
            "total_value_usd": 0.0,
            "assets": assets,
            "error": None,
        }
    except Exception as e:
        return {
            "ok": False,
            "address": sol_address,
            "total_value_usd": 0.0,
            "assets": [],
            "error": str(e),
        }


if __name__ == "__main__":
    from rich import print
    print(get_solana_portfolio("GdV8W4x3WRsRM4Sdouh52Lxktfn1XyuaS6ETSvi8xssq"))