"""
杠杆更新 Action 模块 (UPDATE_LEVERAGE)

按 Feature_HyperliquidAIAgentIntent.zh-CN.md 文档实现

Simple Mode 示例:
{
    "action": "UPDATE_LEVERAGE",
    "asset": "BTC",
    "leverage": 20,
    "margin_mode": "cross",
    "confidence": 0.99,
    "source_text": "把 BTC 杠杆调整到 20x 全仓"
}

Advanced Mode:
{
    "action": "UPDATE_LEVERAGE",
    "execution_plan": [
        {
            "intent": "UPDATE_LEVERAGE",
            "coin": "BTC",
            "leverage": 20,
            "isCross": true
        }
    ],
    "meta": {
        "source_text": "把 BTC 杠杆调整到 20x 全仓",
        "agent_request_id": "hl-update-leverage-20260324-001",
        "previous_leverage": 10,
        "previous_margin_mode": "isolated"
    }
}
"""

from typing import Any, Literal

MarginMode = Literal["cross", "isolated"]


def build_update_leverage_params(
    coin: str,
    leverage: float,
    margin_mode: MarginMode = "cross",
    network: str = "mainnet",
    source_text: str = "",
    agent_request_id: str = "",
    confidence: float = 1.0,
    previous_leverage: int | None = None,
    previous_margin_mode: MarginMode | None = None,
) -> dict[str, Any]:
    """
    构建杠杆更新参数 (UPDATE_LEVERAGE)

    参数:
        coin: 币种（如 "BTC"）
        leverage: 目标杠杆倍数
        margin_mode: 保证金模式（"cross" 或 "isolated"）
        network: 网络
        source_text: 原始用户输入
        agent_request_id: 请求 ID
        confidence: 置信度
        previous_leverage: 之前的杠杆（用于 meta）
        previous_margin_mode: 之前的保证金模式（用于 meta）

    返回: Advanced Mode 结构
    """
    is_cross = margin_mode == "cross"

    execution_plan = [{
        "intent": "UPDATE_LEVERAGE",
        "coin": coin.upper(),
        "leverage": int(leverage),
        "isCross": is_cross,
    }]

    meta: dict[str, Any] = {
        "source_text": source_text,
        "agent_request_id": agent_request_id,
    }

    if previous_leverage is not None:
        meta["previous_leverage"] = previous_leverage
    if previous_margin_mode is not None:
        meta["previous_margin_mode"] = previous_margin_mode

    result: dict[str, Any] = {
        "action": "UPDATE_LEVERAGE",
        "execution_plan": execution_plan,
        "meta": meta,
    }

    # Simple Mode 字段
    result["asset"] = coin.upper()
    result["leverage"] = int(leverage)
    result["margin_mode"] = margin_mode
    if confidence != 1.0:
        result["confidence"] = confidence
    if source_text:
        result["source_text"] = source_text

    return result


def action_update_leverage(
    intent: dict[str, Any],
    agent_request_id: str = "",
) -> dict[str, Any]:
    """
    外部接口：接收 Agent 传来的标准化意图，返回前端执行所需的参数

    参数:
        intent: 标准化后的杠杆更新意图
            - action: "UPDATE_LEVERAGE"
            - coin: 币种
            - leverage: 目标杠杆
            - margin_mode: cross/isolated
            - previous_leverage: 之前的杠杆（可选）
            - previous_margin_mode: 之前的保证金模式（可选）
            - source_text: 原始输入
            - confidence: 置信度
        agent_request_id: 请求 ID

    返回结构:
    {
        "ok": bool,
        "error": str | None,
        "action_card": {...} | None,
    }
    """
    # 验证必要字段
    required = ["coin", "leverage"]
    missing = [f for f in required if intent.get(f) is None]

    if missing:
        return {
            "ok": False,
            "error": f"缺少必要参数: {', '.join(missing)}",
            "action_card": None,
        }

    coin = str(intent["coin"])
    leverage = float(intent["leverage"])

    # 验证杠杆范围
    if leverage <= 0:
        return {
            "ok": False,
            "error": f"杠杆必须 > 0，当前: {leverage}",
            "action_card": None,
        }

    if leverage > 150:
        return {
            "ok": False,
            "error": f"杠杆不能超过 150，当前: {leverage}",
            "action_card": None,
        }

    # 验证 margin_mode
    margin_mode = intent.get("margin_mode", "cross")
    if margin_mode not in ("cross", "isolated"):
        return {
            "ok": False,
            "error": f"无效的保证金模式: {margin_mode}",
            "action_card": None,
        }

    previous_leverage = int(intent["previous_leverage"]) if intent.get("previous_leverage") is not None else None
    previous_margin_mode = intent.get("previous_margin_mode") if intent.get("previous_margin_mode") in ("cross", "isolated") else None

    try:
        action_card = build_update_leverage_params(
            coin=coin,
            leverage=leverage,
            margin_mode=margin_mode,
            network=str(intent.get("network", "mainnet")),
            source_text=str(intent.get("source_text", "")),
            agent_request_id=agent_request_id,
            confidence=float(intent.get("confidence", 1.0)),
            previous_leverage=previous_leverage,
            previous_margin_mode=previous_margin_mode,
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
        # 调整 BTC 杠杆
        {
            "action": "UPDATE_LEVERAGE",
            "coin": "BTC",
            "leverage": 20,
            "margin_mode": "cross",
            "previous_leverage": 10,
            "previous_margin_mode": "isolated",
            "source_text": "把 BTC 杠杆调整到 20x 全仓",
        },
        # 调整 ETH 杠杆
        {
            "action": "UPDATE_LEVERAGE",
            "coin": "ETH",
            "leverage": 5,
            "margin_mode": "isolated",
            "source_text": "ETH 逐仓 5x",
        },
    ]

    for i, intent in enumerate(test_cases):
        result = action_update_leverage(intent)
        print(f"\n=== Test case {i+1}: {intent['coin']} ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
