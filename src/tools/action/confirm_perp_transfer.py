"""
合约资金划转 Confirm 模块 (PERPS_DEPOSIT / PERPS_WITHDRAW)

按 hyperliquid交易卡片需求文档.md 5.2/5.3 实现
"""

from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Literal


# =============================================================================
# Pydantic 类
# =============================================================================

class ConfirmTransferIntent(BaseModel):
    """划转 intent"""
    intent: Literal["PERPS_DEPOSIT", "PERPS_WITHDRAW"]
    amount: float
    asset: str


class ConfirmTransferAction(BaseModel):
    """划转返回"""
    action: Literal["PERPS_DEPOSIT", "PERPS_WITHDRAW"]
    execution_plan: list[ConfirmTransferIntent]
    meta: dict


# =============================================================================
# impl 纯函数
# =============================================================================

def confirm_perp_transfer_impl(
    action_type: Literal["PERPS_DEPOSIT", "PERPS_WITHDRAW"],
    amount: float,
    asset: str = "USDC",
    source_text: str = "",
) -> dict:
    """合约资金划转卡片（PERPS_DEPOSIT / PERPS_WITHDRAW）。用于"往合约存款"或"从合约取款"类意图。"""
    if action_type not in ("PERPS_DEPOSIT", "PERPS_WITHDRAW"):
        raise ValueError("action_type 必须是 PERPS_DEPOSIT 或 PERPS_WITHDRAW")
    item_dict = {
        "intent": action_type,
        "amount": amount,
        "asset": asset,
    }
    return ConfirmTransferAction.model_validate({
        "action": action_type,
        "execution_plan": [item_dict],
        "meta": {"source_text": source_text},
    }).model_dump()


# =============================================================================
# @tool 函数
# =============================================================================

@tool
def confirm_perp_transfer(
    action_type: Literal["PERPS_DEPOSIT", "PERPS_WITHDRAW"],
    amount: float,
    asset: str = "USDC",
    source_text: str = "",
) -> dict:
    """合约资金划转卡片（PERPS_DEPOSIT / PERPS_WITHDRAW）。用于"往合约存款"或"从合约取款"类意图。"""
    return confirm_perp_transfer_impl(
        action_type=action_type,
        amount=amount,
        asset=asset,
        source_text=source_text,
    )


# =============================================================================
# if __name__ == "__main__"
# =============================================================================

if __name__ == "__main__":
    from rich import print

    # uv run python -m src.tools.action.confirm_perp_transfer

    print("=== PERPS_DEPOSIT ===")
    print(confirm_perp_transfer_impl(
        action_type="PERPS_DEPOSIT",
        amount=500,
        source_text="我要往合约存款",
    ))
    print()
    print("=== PERPS_WITHDRAW ===")
    print(confirm_perp_transfer_impl(
        action_type="PERPS_WITHDRAW",
        amount=500,
        source_text="我要从合约取款",
    ))
