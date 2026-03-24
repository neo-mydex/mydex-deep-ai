"""
查看仓位 Action 模块 (VIEW_POSITION)

按 Feature_HyperliquidAIAgentIntent.zh-CN.md 文档实现

Simple Mode 示例:
{
    "action": "VIEW_POSITION",
    "asset": "BTC",
    "source_text": "看看我 BTC 仓位"
}

Advanced Mode:
{
    "action": "VIEW_POSITION",
    "query": {
        "user_address": "0x1234567890abcdef1234567890abcdef12345678",
        "asset": "BTC",
        "include_open_orders": true,
        "include_tpsl": true
    },
    "meta": {
        "agent_request_id": "hl-view-position-20260324-001"
    }
}
"""

from typing import Any


def build_view_position_params(
    user_address: str,
    coin: str,
    include_open_orders: bool = True,
    include_tpsl: bool = True,
    network: str = "mainnet",
    source_text: str = "",
    agent_request_id: str = "",
    confidence: float = 1.0,
) -> dict[str, Any]:
    """
    构建查看仓位参数 (VIEW_POSITION)

    参数:
        user_address: 用户钱包地址
        coin: 币种（如 "BTC"）
        include_open_orders: 是否包含未成交订单
        include_tpsl: 是否包含 TPSL 订单
        network: 网络
        source_text: 原始用户输入
        agent_request_id: 请求 ID
        confidence: 置信度

    返回: Advanced Mode 结构
    """
    query: dict[str, Any] = {
        "user_address": user_address,
        "asset": coin.upper(),
        "include_open_orders": include_open_orders,
        "include_tpsl": include_tpsl,
    }

    meta: dict[str, Any] = {
        "agent_request_id": agent_request_id,
    }

    if source_text:
        meta["source_text"] = source_text

    result: dict[str, Any] = {
        "action": "VIEW_POSITION",
        "query": query,
        "meta": meta,
    }

    # Simple Mode 字段
    result["asset"] = coin.upper()
    if confidence != 1.0:
        result["confidence"] = confidence
    if source_text:
        result["source_text"] = source_text

    return result


def action_view_position(
    intent: dict[str, Any],
    user_address: str = "",
    agent_request_id: str = "",
) -> dict[str, Any]:
    """
    外部接口：接收 Agent 传来的标准化意图，返回前端执行所需的参数

    参数:
        intent: 标准化后的查看仓位意图
            - action: "VIEW_POSITION"
            - coin: 币种
            - include_open_orders: 是否包含未成交订单（默认 True）
            - include_tpsl: 是否包含 TPSL 订单（默认 True）
            - source_text: 原始输入
            - confidence: 置信度
        user_address: 用户钱包地址（如果 intent 中没有）
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

    # 获取 user_address
    address = intent.get("user_address") or user_address
    if not address:
        return {
            "ok": False,
            "error": "缺少必要参数: user_address",
            "action_card": None,
        }

    include_open_orders = bool(intent.get("include_open_orders", True))
    include_tpsl = bool(intent.get("include_tpsl", True))

    try:
        action_card = build_view_position_params(
            user_address=address,
            coin=coin,
            include_open_orders=include_open_orders,
            include_tpsl=include_tpsl,
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
        # 查看 BTC 仓位
        {
            "action": "VIEW_POSITION",
            "coin": "BTC",
            "user_address": "0x1234567890abcdef1234567890abcdef12345678",
            "source_text": "看看我 BTC 仓位",
        },
        # 查看所有仓位
        {
            "action": "VIEW_POSITION",
            "coin": "ALL",
            "user_address": "0x1234567890abcdef1234567890abcdef12345678",
            "include_open_orders": True,
            "include_tpsl": True,
            "source_text": "看看我所有仓位和挂单",
        },
    ]

    for i, intent in enumerate(test_cases):
        result = action_view_position(intent)
        print(f"\n=== Test case {i+1}: {intent.get('coin')} ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
