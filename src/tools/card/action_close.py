"""
平仓 Action 模块 (CLOSE_POSITION)

按 Feature_HyperliquidAIAgentIntent.zh-CN.md 文档实现

Simple Mode 示例:
{
    "action": "CLOSE_POSITION",
    "asset": "BTC",
    "close_mode": "full",
    "confidence": 0.99,
    "source_text": "把 BTC 仓位全平掉"
}

Advanced Mode（全平）:
{
    "action": "CLOSE_POSITION",
    "execution_plan": [
        {
            "intent": "CLOSE_POSITION",
            "coin": "BTC",
            "size": "0.2921",
            "isLong": true,
            "markPrice": 68720.2,
            "isFullClose": true
        }
    ],
    "meta": {
        "source_text": "把 BTC 仓位全平掉",
        "agent_request_id": "hl-close-full-20260324-001"
    }
}

Advanced Mode（部分平仓）:
{
    "action": "CLOSE_POSITION",
    "execution_plan": [
        {
            "intent": "CLOSE_POSITION",
            "coin": "BTC",
            "size": "0.1000",
            "isLong": true,
            "markPrice": 68720.2,
            "isFullClose": false
        }
    ],
    "meta": {
        "close_ratio": 0.34,
        "source_text": "平掉三分之一 BTC 多仓",
        "agent_request_id": "hl-close-partial-20260324-001"
    }
}
"""

from typing import Any

from .types import PositionSide


def build_close_position_params(
    coin: str,
    position_side: PositionSide,
    position_size: float,
    close_size: float | None = None,
    mark_price: float | None = None,
    network: str = "mainnet",
    source_text: str = "",
    agent_request_id: str = "",
    confidence: float = 1.0,
) -> dict[str, Any]:
    """
    构建平仓参数 (CLOSE_POSITION)

    参数:
        coin: 币种（如 "BTC"）
        position_side: 持仓方向（"long", "short", "flat"）
        position_size: 当前持仓数量
        close_size: 平仓数量（None = 全平）
        mark_price: 当前市场价格
        network: 网络
        source_text: 原始用户输入
        agent_request_id: 请求 ID
        confidence: 置信度

    返回: Advanced Mode 结构
    """
    # 判断是否全平
    is_full_close = close_size is None or close_size >= position_size

    # 计算实际平仓数量
    actual_close_size = close_size if close_size is not None else position_size

    # 判断是否是多仓
    is_long = position_side == "long"

    # 构建执行计划
    execution_plan = [{
        "intent": "CLOSE_POSITION",
        "coin": coin.upper(),
        "size": str(round(actual_close_size, 6)),
        "isLong": is_long,
        "markPrice": mark_price,
        "isFullClose": is_full_close,
    }]

    # 构建 meta
    meta: dict[str, Any] = {
        "source_text": source_text,
        "agent_request_id": agent_request_id,
    }

    # 如果是部分平仓，添加比例
    if not is_full_close and position_size > 0:
        close_ratio = actual_close_size / position_size
        meta["close_ratio"] = round(close_ratio, 4)

    result: dict[str, Any] = {
        "action": "CLOSE_POSITION",
        "execution_plan": execution_plan,
        "meta": meta,
    }

    # Simple Mode 字段
    result["asset"] = coin.upper()
    result["close_mode"] = "full" if is_full_close else "partial"
    if confidence != 1.0:
        result["confidence"] = confidence
    if source_text:
        result["source_text"] = source_text

    return result


def action_close_position(
    intent: dict[str, Any],
    position_info: dict[str, Any] | None = None,
    agent_request_id: str = "",
) -> dict[str, Any]:
    """
    外部接口：接收 Agent 传来的标准化意图，返回前端执行所需的参数

    参数:
        intent: 标准化后的平仓意图
            - action: "CLOSE_POSITION"
            - coin: 币种
            - close_size: 平仓数量（None = 全平）
            - close_mode: "full" / "partial"（可选）
            - source_text: 原始输入
            - confidence: 置信度
        position_info: 当前持仓信息（可选，用于获取 position_side 和 position_size）
            - position_side: "long" / "short" / "flat"
            - position_size: float
            - mark_px: float
        agent_request_id: 请求 ID

    返回结构:
    {
        "ok": bool,
        "error": str | None,
        "action_card": {...} | None,
    }
    """
    # 验证必要字段
    if intent.get("coin") is None:
        return {
            "ok": False,
            "error": "缺少必要参数: coin",
            "action_card": None,
        }

    coin = str(intent["coin"])
    close_size = intent.get("close_size")
    close_mode = intent.get("close_mode", "full" if close_size is None else "partial")

    # 从 position_info 获取持仓信息
    position_side = "flat"
    position_size = 0.0
    mark_price = None

    if position_info:
        position_side = position_info.get("position_side", "flat")
        position_size = float(position_info.get("position_size") or 0)
        mark_price = position_info.get("mark_px")

    # 如果 intent 中有明确的 position_side，覆盖上面的值
    if intent.get("position_side"):
        position_side = intent["position_side"]
    if intent.get("position_size"):
        position_size = float(intent["position_size"])
    if intent.get("mark_price"):
        mark_price = float(intent["mark_price"])

    # 判断是否全平
    if close_mode == "full":
        actual_close_size = None  # 全平
    elif close_size is not None:
        actual_close_size = float(close_size)
    else:
        actual_close_size = None  # 默认全平

    # 验证平仓数量
    if actual_close_size is not None and actual_close_size <= 0:
        return {
            "ok": False,
            "error": "平仓数量必须 > 0",
            "action_card": None,
        }

    # 如果有持仓信息，验证平仓数量不超过持仓
    if position_info and actual_close_size is not None and actual_close_size > position_size:
        return {
            "ok": False,
            "error": f"平仓数量({actual_close_size})不能超过持仓量({position_size})",
            "action_card": None,
        }

    # 如果没有持仓信息，返回错误
    if position_side == "flat" or position_size == 0:
        return {
            "ok": False,
            "error": f"{coin} 没有持仓，无需平仓",
            "action_card": None,
        }

    try:
        action_card = build_close_position_params(
            coin=coin,
            position_side=position_side,
            position_size=position_size,
            close_size=actual_close_size,
            mark_price=mark_price,
            network=str(intent.get("network", "mainnet")),
            source_text=str(intent.get("source_text", "")),
            agent_request_id=agent_request_id,
            confidence=float(intent.get("confidence", 1.0)),
        )

        return {
            "ok": True,
            "error": None,
            "action_card": action_card,
        }

    except (TypeError, ValueError) as e:
        return {
            "ok": False,
            "error": f"参数类型错误: {str(e)}",
            "action_card": None,
        }


if __name__ == "__main__":
    import json

    # 测试用例
    test_cases = [
        # 全平 BTC
        {
            "action": "CLOSE_POSITION",
            "coin": "BTC",
            "close_size": None,
            "source_text": "把 BTC 仓位全平掉",
        },
        # 部分平 ETH
        {
            "action": "CLOSE_POSITION",
            "coin": "ETH",
            "close_size": 0.5,
            "source_text": "平掉一半 ETH 仓位",
        },
    ]

    # 模拟持仓信息
    position_infos = {
        "BTC": {
            "position_side": "long",
            "position_size": 1.5,
            "mark_px": 68720.2,
        },
        "ETH": {
            "position_side": "short",
            "position_size": 1.0,
            "mark_px": 3650.0,
        },
    }

    for i, intent in enumerate(test_cases):
        coin = intent.get("coin")
        result = action_close_position(intent, position_info=position_infos.get(coin))
        print(f"\n=== Test case {i+1}: {coin} ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
