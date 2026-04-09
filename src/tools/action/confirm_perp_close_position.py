"""
平仓 Confirm 模块 (CLOSE_POSITION)

按 hyperliquid交易卡片需求文档.md 5.6 实现

支持单个和批量平仓
"""

from langchain_core.tools import tool
from pydantic import BaseModel, field_validator
from typing import Literal


class CloseItem(BaseModel):
    """单个平仓项（输入）"""
    coin: str
    position_side: Literal["long", "short"]
    position_size: float
    close_size: float | None = None
    close_ratio: float | None = None
    mark_price: float | None = None


class Meta(BaseModel):
    """meta"""
    source_text: str = ""


class ClosePositionIntent(BaseModel):
    """CLOSE_POSITION intent（二选一：size 或 closeRatio）"""
    intent: Literal["CLOSE_POSITION"]
    coin: str
    isLong: bool
    markPrice: float | None = None
    size: str | None = None
    closeRatio: float | None = None

    @field_validator("coin", mode="before")
    @classmethod
    def uppercase_coin(cls, v: str) -> str:
        return v.upper()


class ConfirmClosePositionAction(BaseModel):
    """confirm_perp_close_position 返回"""
    action: Literal["CLOSE_POSITION"]
    execution_plan: list[ClosePositionIntent]
    meta: Meta


def _build_close_item(item: CloseItem) -> ClosePositionIntent:
    """构建单个平仓 intent

    size 和 closeRatio 二选一：
    - 指定了 close_ratio → 只填 closeRatio
    - 指定了 close_size → 只填 size
    - 什么都没指定（全平）→ closeRatio = 1.0
    """
    is_full_close = (
        item.close_size is None
        or item.close_ratio == 1.0
        or (item.close_size is not None and item.close_size >= item.position_size)
    )
    is_long = item.position_side == "long"

    intent_dict: dict = {
        "intent": "CLOSE_POSITION",
        "coin": item.coin.upper(),
        "isLong": is_long,
        "markPrice": item.mark_price,
        "size": None,
        "closeRatio": None,
    }

    if item.close_ratio is not None:
        intent_dict["closeRatio"] = item.close_ratio
    elif item.close_size is not None:
        intent_dict["size"] = str(round(item.close_size, 6))
    else:
        intent_dict["closeRatio"] = 1.0

    return ClosePositionIntent.model_validate(intent_dict)


def confirm_perp_close_position_impl(
    closes: list[CloseItem],
    source_text: str = "",
) -> dict:
    """平仓卡片（CLOSE_POSITION）。支持单个或批量平仓。"""
    if not closes:
        raise ValueError("closes 不能为空，至少需要指定一个平仓项")

    execution_plan = [_build_close_item(item) for item in closes]
    meta = Meta(source_text=source_text)

    return ConfirmClosePositionAction.model_validate({
        "action": "CLOSE_POSITION",
        "execution_plan": execution_plan,
        "meta": meta,
    }).model_dump()


@tool
def confirm_perp_close_position(
    closes: list[CloseItem],
    source_text: str = "",
) -> dict:
    """平仓卡片（CLOSE_POSITION）

    用户想把仓位平掉时使用。支持单个或批量平仓。

    参数说明：
    - closes: 平仓项列表，支持多个币种同时平仓
      - coin: 币种名称，如 "BTC"、"ETH"
      - position_side: 仓位方向，"long" 或 "short"
      - position_size: 当前仓位大小（合约数量）
      - close_size: 本次平仓数量（不填则全平）
      - close_ratio: 本次平仓比例（0.5 = 平 50%），与 close_size 二选一
      - mark_price: 当前标记价格
    - source_text: 用户的原始表达

    示例：
    - "把 BTC 仓位全平" → closes=[{"coin": "BTC", "position_side": "long", "position_size": 1.5}]
    - "平一半 ETH 仓位" → closes=[{"coin": "ETH", "position_side": "short", "position_size": 1.0, "close_ratio": 0.5}]
    - "把 BTC 和 ETH 都平一半" → closes=[{...BTC...}, {...ETH...}]
    - "平 0.5 个 BTC" → closes=[{"coin": "BTC", "position_side": "long", "position_size": 1.5, "close_size": 0.5}]
    """
    return confirm_perp_close_position_impl(
        closes=closes,
        source_text=source_text,
    )


if __name__ == "__main__":
    from rich import print

    # uv run python -m src.tools.action.confirm_perp_close_position

    print("=== 全平单个 ===")
    print(confirm_perp_close_position_impl(
        closes=[CloseItem(
            coin="BTC",
            position_side="long",
            position_size=1.5,
            mark_price=68720.2,
        )],
        source_text="把 BTC 仓位全平掉",
    ))

    print("\n=== 部分平 50% ===")
    print(confirm_perp_close_position_impl(
        closes=[CloseItem(
            coin="ETH",
            position_side="short",
            position_size=1.0,
            close_ratio=0.5,
            mark_price=3650.0,
        )],
        source_text="平掉一半 ETH 仓位",
    ))

    print("\n=== 仅 close_size ===")
    print(confirm_perp_close_position_impl(
        closes=[CloseItem(
            coin="BTC",
            position_side="long",
            position_size=1.5,
            close_size=0.5,
            mark_price=68720.2,
        )],
        source_text="平 0.5 个 BTC",
    ))

    print("\n=== 批量平仓 ===")
    print(confirm_perp_close_position_impl(
        closes=[
            CloseItem(coin="BTC", position_side="long", position_size=1.5, close_ratio=0.5, mark_price=68720.2),
            CloseItem(coin="ETH", position_side="short", position_size=1.0, mark_price=3650.0),
        ],
        source_text="把 BTC 平一半，ETH 全平",
    ))
