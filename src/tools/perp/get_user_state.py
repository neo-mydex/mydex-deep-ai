"""
用户状态查询
"""

from typing import Literal
from langchain_core.tools import tool
from pydantic import BaseModel
from src.services.hyperliquid.cli import get_account_balance

Network = Literal["mainnet", "testnet"]


class BalanceResponse(BaseModel):
    """perp_get_balance 返回格式"""
    ok: bool
    address: str
    network: Network
    withdrawable: float
    account_value: float | None = None
    total_margin_used: float | None = None


def perp_get_balance_impl(
    address: str,
    network: Network = "mainnet",
) -> dict:
    """获取账户余额（纯函数，可直接测试）"""
    result = get_account_balance(address=address, network=network)
    return BalanceResponse.model_validate(result).model_dump()


@tool
def perp_get_balance(
    address: str,
    network: Network = "mainnet",
) -> BalanceResponse:
    """
    获取 Hyperliquid 永续合约用户账户余额。

    用于查询用户账户的可提取余额、账户价值和已用保证金。

    参数:
        address: 用户钱包地址
        network: 网络类型，"mainnet" 或 "testnet"

    返回:
        BalanceResponse: {
            "ok": bool,
            "address": str,
            "network": str,
            "withdrawable": float,
            "account_value": float | None,
            "total_margin_used": float | None,
        }
    """
    return perp_get_balance_impl(address=address, network=network)


if __name__ == "__main__":
    from pprint import pprint
    pprint(perp_get_balance_impl(address="0x1234567890abcdef1234567890abcdef12345678"))
