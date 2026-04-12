"""
平仓前检查
"""

from typing import Any, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field, model_validator
from src.services.hyperliquid import check_can_close as service_check_can_close

from src.tools.perp.get_positions import perp_get_positions_impl

Network = Literal["mainnet", "testnet"]
Side = Literal["long", "short", "flat"]


class CanCloseInput(BaseModel):
    """perp_check_can_close 输入参数校验"""
    coin: str | None
    address: str
    close_size: float | None = Field(default=None, gt=0)                 # 币本位张数
    close_size_in_usdc: float | None = Field(default=None, gt=0)   # USDC 价值
    close_ratio: float | None = Field(default=None)                   # 0-1 比例（允许负数/超范围，内部纠正）
    network: Network = "mainnet"

    @model_validator(mode="before")
    @classmethod
    def _clamp_ratio(cls, data: Any) -> Any:
        """close_ratio 超出 (0, 1] 范围时自动纠正为 1.0"""
        if isinstance(data, dict) and data.get("close_ratio") is not None:
            ratio = data["close_ratio"]
            if ratio > 1 or ratio <= 0:
                data["close_ratio"] = 1.0
        return data

    @model_validator(mode="after")
    def exactly_one_input(self) -> "CanCloseInput":
        inputs = [self.close_size, self.close_size_in_usdc, self.close_ratio]
        provided = [x for x in inputs if x is not None]
        if len(provided) > 1:
            raise ValueError("close_size / close_size_in_usdc / close_ratio 不可同时指定")
        if len(provided) == 0:
            # 全不选：默认全平
            self.close_ratio = 1.0
        return self


class MatchingPosition(BaseModel):
    """单个仓位摘要（用于 matching_positions）"""
    coin: str
    side: Side
    size: float                        # 持仓量
    close_ratio: float | None = None  # 本次平仓比例
    close_size: float | None = None   # 本次平仓量
    mark_price: float | None = None   # 标记价格


class CanCloseResponse(BaseModel):
    """perp_check_can_close 返回格式"""
    ok: bool                              # 是否可以平仓
    matching_positions: list[MatchingPosition] = Field(default_factory=list)  # 仓位列表
    corrections: list[str] = Field(default_factory=list)  # 警告/纠正
    issues: list[dict[str, Any]] = Field(default_factory=list)  # 错误列表（block）
    follow_up_question: str = ""


def perp_check_can_close_impl(
    address: str,
    coin: str | None = None,
    close_size: float | None = None,
    close_size_in_usdc: float | None = None,
    close_ratio: float | None = None,
    network: Network = "mainnet",
) -> dict:
    """平仓前检查（纯函数，可直接测试）"""
    corrections: list[str] = []

    # 参数校验（三选一），内部会把 close_ratio 超出范围的值自动 clamp 到 1.0
    validated = CanCloseInput(
        address=address,
        coin=coin,
        close_size=close_size,
        close_size_in_usdc=close_size_in_usdc,
        close_ratio=close_ratio,
        network=network,
    )
    # 若原始 ratio 超出范围，已被自动纠正为 1.0，通知用户
    if close_ratio is not None and validated.close_ratio != close_ratio:
        corrections.append("close_ratio 已自动纠正为 1.0（最多平全部仓位）")

    # coin=None：批量模式，返回所有有仓位的币
    if coin is None:
        positions_result = perp_get_positions_impl(address=address, network=network)
        all_positions = positions_result.get("positions", [])
        # 过滤出有仓位的（size != 0）
        active_positions = [p for p in all_positions if p.get("size", 0) != 0]

        matching: list[MatchingPosition] = []
        issues: list[dict[str, Any]] = []
        for p in active_positions:
            sz = p.get("size", 0)
            mark_px = p.get("mark_px")
            coin_name = p.get("coin", "")
            abs_sz = abs(sz)

            # 检查 mark_price 可用性（close_size_in_usdc 模式需要）
            if close_size_in_usdc is not None and mark_px is None:
                issues.append({
                    "code": "price_unavailable",
                    "message": f"{coin_name} 无法获取市场价格"
                })
                continue

            # 逐仓计算平仓量（每个仓位独立计算）
            if validated.close_ratio is not None:
                actual_close_size = round(abs_sz * validated.close_ratio, 9)
                actual_close_ratio = validated.close_ratio
            elif validated.close_size is not None:
                max_close_usdc = abs_sz * (mark_px or 0)
                actual_close_size = min(validated.close_size, abs_sz)
                actual_close_ratio = round(actual_close_size / abs_sz, 9) if abs_sz > 0 else None
                # 仓位太小，平不了指定的张数，correction 提示
                if actual_close_size < validated.close_size:
                    corrections.append(
                        f"{coin_name} 仓位只有 {abs_sz} 张（价值约 {max_close_usdc:.2f} USDC），"
                        f"无法平 {validated.close_size} 张，已调整为全平"
                    )
            else:  # close_size_in_usdc
                usdc_val = validated.close_size_in_usdc or 0
                max_close_usdc = abs_sz * mark_px if mark_px else 0
                actual_close_usdc = min(usdc_val, max_close_usdc)
                actual_close_size = round(actual_close_usdc / mark_px, 9) if mark_px else 0
                actual_close_ratio = round(actual_close_usdc / max_close_usdc, 9) if max_close_usdc > 0 else None
                # 仓位价值不够，correction 提示
                if actual_close_usdc < usdc_val:
                    corrections.append(
                        f"{coin_name} 仓位价值约 {max_close_usdc:.2f} USDC，"
                        f"无法平 {usdc_val} USDC，已调整为全平"
                    )

            matching.append(MatchingPosition(
                coin=coin_name,
                side=p.get("side", "flat"),
                size=abs_sz,
                close_ratio=actual_close_ratio,
                close_size=actual_close_size,
                mark_price=mark_px,
            ))

        if not matching and not issues:
            return CanCloseResponse(
                ok=False,
                corrections=corrections,
                issues=[{"code": "no_position", "message": "没有仓位，无需平仓"}],
                follow_up_question="",
            ).model_dump()

        return CanCloseResponse(
            ok=len(issues) == 0,
            matching_positions=matching,
            corrections=corrections,
            issues=issues,
            follow_up_question="",
        ).model_dump()

    # coin 有值：单币模式，调用 service（保留完整检查逻辑）
    result = service_check_can_close(
        address=address,
        coin=coin,
        close_size=validated.close_size,
        close_size_in_usdc=validated.close_size_in_usdc,
        close_ratio=validated.close_ratio,
        network=network,
    )
    # 合并 service 返回的 corrections
    if result.get("corrections"):
        corrections.extend(result["corrections"])
    else:
        result["corrections"] = corrections

    # 构建 matching_positions（单币 = 1 项）
    if result.get("has_position"):
        matching = [MatchingPosition(
            coin=coin,
            side=result.get("position_side", "flat"),
            size=abs(result.get("position_size", 0)),
            close_ratio=result.get("close_ratio"),
            close_size=result.get("close_size"),
            mark_price=None,  # service 返回里没有 mark_price，置空
        )]
    else:
        matching = []

    return CanCloseResponse(
        ok=result.get("ok", False),
        matching_positions=matching,
        corrections=corrections,
        issues=result.get("issues", []),
        follow_up_question=result.get("follow_up_question", ""),
    ).model_dump()


@tool
def perp_check_can_close(
    address: str,
    coin: str | None = None,
    close_size: float | None = None,
    close_size_in_usdc: float | None = None,
    close_ratio: float | None = None,
    network: Network = "mainnet",
) -> CanCloseResponse:
    """
    【强制】平仓前必须调用的可行性校验工具。

    ⚠️ 重要：调用 confirm_perp_close_position 之前，必须先调用本工具。

    校验内容（单币模式）：
    - 是否有仓位可以平
    - 是否有未成交主单（非 TPSL）
    - 市场价格是否可用
    - 平仓数量是否合法

    参数:
        address: 用户钱包地址
        coin: 币种名称，如 "BTC"、"ETH"，不传则返回所有仓位（批量模式）
        close_size: 平仓数量（币本位），如 0.5 BTC
        close_size_in_usdc: 平仓价值（USDC），如 34000 USDC
        close_ratio: 平仓比例（0-1），如 0.3 = 平 30%
        network: 网络类型，"mainnet" 或 "testnet"

    注意: close_size / close_size_in_usdc / close_ratio 三选一，不可同时指定

    返回:
        CanCloseResponse: {
            "ok": bool,
            "has_position": bool,
            "position_side": str,
            "position_size": float,
            "close_size": float,
            "close_size_in_usdc": float,
            "close_ratio": float,
            "matching_positions": list[dict],
            "corrections": list[str],
            "issues": list[dict],
            "follow_up_question": str,
        }
    """
    return perp_check_can_close_impl(
        address=address,
        coin=coin,
        close_size=close_size,
        close_size_in_usdc=close_size_in_usdc,
        close_ratio=close_ratio,
        network=network,
    )


if __name__ == "__main__":
    from rich import print
    addr = "0x269488c0F8D595CF47aAA91AC6Ef896f9F63cc9E"
    print("=== 只有 close_size ===")
    print(perp_check_can_close_impl(address=addr, coin="BTC", close_size=0.0001))
    print()
    print("=== 只有 close_size_in_usdc ===")
    print(perp_check_can_close_impl(address=addr, close_size_in_usdc=14))
    print()
    print("=== 只有 close_ratio ===")
    print(perp_check_can_close_impl(address=addr, close_ratio=0.1))
    print()
    print("=== 全平 ===")
    print(perp_check_can_close_impl(address=addr))
