"""
开仓 Action 模块 (OPEN_LONG / OPEN_SHORT)

按 Feature_HyperliquidAIAgentIntent.zh-CN.md 文档实现

Simple Mode 示例:
{
    "action": "OPEN_LONG",
    "asset": "BTC",
    "leverage": 20,
    "usdc_size": 1000,
    "margin_mode": "cross",
    "order_type": "market",
    "tp": 72000,
    "sl": 66500,
    "confidence": 0.97,
    "source_text": "做多 BTC 20x 1000u，止盈 72000，止损 66500"
}

Advanced Mode 示例:
{
    "action": "OPEN_LONG",
    "execution_plan": [
        {
            "intent": "UPDATE_LEVERAGE",
            "coin": "BTC",
            "leverage": 20,
            "isCross": true
        },
        {
            "intent": "OPEN_ORDER",
            "coin": "BTC",
            "isBuy": true,
            "size": "0.2921",
            "markPrice": 68450.5,
            "orderType": "market",
            "limitPrice": null,
            "tpPrice": "72000",
            "slPrice": "66500"
        }
    ],
    "meta": {
        "input_usdc_size": 1000,
        "size_calc_basis": "size = usdc_size * leverage / markPrice",
        "source_text": "做多 BTC 20x 1000u，止盈 72000，止损 66500",
        "agent_request_id": "hl-open-long-20260324-001"
    }
}
"""

from typing import Any

from .types import CardType, MarginMode, OrderType, TradeSide


def build_open_long_params(
    coin: str,
    leverage: float,
    usdc_size: float,
    margin_mode: MarginMode = "cross",
    order_type: OrderType = "market",
    entry_price: float | None = None,
    tp: float | None = None,
    sl: float | None = None,
    network: str = "mainnet",
    mark_price: float | None = None,
    source_text: str = "",
    agent_request_id: str = "",
    confidence: float = 1.0,
) -> dict[str, Any]:
    """
    构建开多参数 (OPEN_LONG)

    参数:
        coin: 币种（如 "BTC"）
        leverage: 杠杆倍数
        usdc_size: 投入的保证金（USDC）
        margin_mode: 保证金模式（"cross" 或 "isolated"）
        order_type: 订单类型（"market" 或 "limit"）
        entry_price: 限价单的入场价格
        tp: 止盈价格
        sl: 止损价格
        network: 网络
        mark_price: 当前市场价格（用于计算 size）
        source_text: 原始用户输入
        agent_request_id: 请求 ID
        confidence: 置信度

    返回: Advanced Mode 结构
    """
    is_cross = margin_mode == "cross"

    # 计算 size: size = usdc_size * leverage / markPrice
    size = None
    if mark_price and mark_price > 0:
        size = usdc_size * leverage / mark_price
        # 保留合理精度
        size = round(size, 6)

    # 构建 UPDATE_LEVERAGE 步骤
    update_leverage_step = {
        "intent": "UPDATE_LEVERAGE",
        "coin": coin.upper(),
        "leverage": int(leverage),
        "isCross": is_cross,
    }

    # 构建 OPEN_ORDER 步骤
    open_order_step: dict[str, Any] = {
        "intent": "OPEN_ORDER",
        "coin": coin.upper(),
        "isBuy": True,  # 开多 = 买入
        "markPrice": mark_price,
        "orderType": order_type,
    }

    if order_type == "limit" and entry_price is not None:
        open_order_step["limitPrice"] = entry_price
    else:
        open_order_step["limitPrice"] = None

    if size is not None:
        open_order_step["size"] = str(size)

    if tp is not None:
        open_order_step["tpPrice"] = str(tp)

    if sl is not None:
        open_order_step["slPrice"] = str(sl)

    execution_plan = [update_leverage_step, open_order_step]

    meta: dict[str, Any] = {
        "input_usdc_size": usdc_size,
        "size_calc_basis": f"size = usdc_size * leverage / markPrice = {usdc_size} * {leverage} / {mark_price}" if mark_price else None,
        "source_text": source_text,
        "agent_request_id": agent_request_id,
    }

    if margin_mode:
        meta["margin_mode"] = margin_mode

    result: dict[str, Any] = {
        "action": "OPEN_LONG",
        "execution_plan": execution_plan,
        "meta": meta,
    }

    # Simple Mode 字段（供 NLP 层使用）
    result["asset"] = coin.upper()
    result["leverage"] = leverage
    result["usdc_size"] = usdc_size
    result["margin_mode"] = margin_mode
    result["order_type"] = order_type
    if tp is not None:
        result["tp"] = tp
    if sl is not None:
        result["sl"] = sl
    if confidence != 1.0:
        result["confidence"] = confidence
    if source_text:
        result["source_text"] = source_text

    return result


def build_open_short_params(
    coin: str,
    leverage: float,
    usdc_size: float,
    margin_mode: MarginMode = "cross",
    order_type: OrderType = "market",
    entry_price: float | None = None,
    tp: float | None = None,
    sl: float | None = None,
    network: str = "mainnet",
    mark_price: float | None = None,
    source_text: str = "",
    agent_request_id: str = "",
    confidence: float = 1.0,
) -> dict[str, Any]:
    """
    构建开空参数 (OPEN_SHORT)

    参数:
        coin: 币种（如 "BTC"）
        leverage: 杠杆倍数
        usdc_size: 投入的保证金（USDC）
        margin_mode: 保证金模式（"cross" 或 "isolated"）
        order_type: 订单类型（"market" 或 "limit"）
        entry_price: 限价单的入场价格
        tp: 止盈价格
        sl: 止损价格
        network: 网络
        mark_price: 当前市场价格（用于计算 size）
        source_text: 原始用户输入
        agent_request_id: 请求 ID
        confidence: 置信度

    返回: Advanced Mode 结构
    """
    is_cross = margin_mode == "cross"

    # 计算 size: size = usdc_size * leverage / markPrice
    size = None
    if mark_price and mark_price > 0:
        size = usdc_size * leverage / mark_price
        size = round(size, 6)

    # 构建 UPDATE_LEVERAGE 步骤
    update_leverage_step = {
        "intent": "UPDATE_LEVERAGE",
        "coin": coin.upper(),
        "leverage": int(leverage),
        "isCross": is_cross,
    }

    # 构建 OPEN_ORDER 步骤
    open_order_step: dict[str, Any] = {
        "intent": "OPEN_ORDER",
        "coin": coin.upper(),
        "isBuy": False,  # 开空 = 卖出
        "markPrice": mark_price,
        "orderType": order_type,
    }

    if order_type == "limit" and entry_price is not None:
        open_order_step["limitPrice"] = entry_price
    else:
        open_order_step["limitPrice"] = None

    if size is not None:
        open_order_step["size"] = str(size)

    if tp is not None:
        open_order_step["tpPrice"] = str(tp)

    if sl is not None:
        open_order_step["slPrice"] = str(sl)

    execution_plan = [update_leverage_step, open_order_step]

    meta: dict[str, Any] = {
        "input_usdc_size": usdc_size,
        "size_calc_basis": f"size = usdc_size * leverage / markPrice = {usdc_size} * {leverage} / {mark_price}" if mark_price else None,
        "source_text": source_text,
        "agent_request_id": agent_request_id,
    }

    if margin_mode:
        meta["margin_mode"] = margin_mode

    result: dict[str, Any] = {
        "action": "OPEN_SHORT",
        "execution_plan": execution_plan,
        "meta": meta,
    }

    # Simple Mode 字段
    result["asset"] = coin.upper()
    result["leverage"] = leverage
    result["usdc_size"] = usdc_size
    result["margin_mode"] = margin_mode
    result["order_type"] = order_type
    if tp is not None:
        result["tp"] = tp
    if sl is not None:
        result["sl"] = sl
    if entry_price is not None:
        result["limit_price"] = entry_price
    if confidence != 1.0:
        result["confidence"] = confidence
    if source_text:
        result["source_text"] = source_text

    return result


def action_open_position(
    intent: dict[str, Any],
    mark_price: float | None = None,
    agent_request_id: str = "",
) -> dict[str, Any]:
    """
    外部接口：接收 Agent 传来的标准化意图，返回前端执行所需的参数

    参数:
        intent: 标准化后的开仓意图
            - action: "OPEN_LONG" 或 "OPEN_SHORT"
            - coin: 币种
            - side: long/short（兼容旧接口）
            - leverage: 杠杆
            - usdc_size: 保证金
            - margin_mode: cross/isolated
            - order_type: market/limit
            - entry_price: 限价单价格
            - tp: 止盈
            - sl: 止损
            - source_text: 原始输入
            - confidence: 置信度
        mark_price: 当前市场价格（用于计算 size）
        agent_request_id: 请求 ID

    返回结构:
    {
        "ok": bool,
        "error": str | None,
        "action_card": {...} | None,
    }
    """
    # 验证必要字段
    required = ["coin", "leverage", "usdc_size"]
    missing = [f for f in required if intent.get(f) is None]

    if missing:
        return {
            "ok": False,
            "error": f"缺少必要参数: {', '.join(missing)}",
            "action_card": None,
        }

    # 确定 action 类型
    action = intent.get("action", "").upper()
    side = intent.get("side", "").lower()

    # 兼容旧接口：如果没传 action，通过 side 判断
    if action not in ("OPEN_LONG", "OPEN_SHORT"):
        if side == "long":
            action = "OPEN_LONG"
        elif side == "short":
            action = "OPEN_SHORT"
        else:
            return {
                "ok": False,
                "error": f"无法确定 action: {action}, side: {side}",
                "action_card": None,
            }

    # 验证 order_type
    order_type = intent.get("order_type", "market")
    if order_type not in ("market", "limit"):
        return {
            "ok": False,
            "error": f"无效的订单类型: {order_type}",
            "action_card": None,
        }

    # 限价单需要 entry_price
    if order_type == "limit" and intent.get("entry_price") is None:
        return {
            "ok": False,
            "error": "限价单需要 entry_price",
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

    try:
        if action == "OPEN_LONG":
            action_card = build_open_long_params(
                coin=str(intent["coin"]),
                leverage=float(intent["leverage"]),
                usdc_size=float(intent["usdc_size"]),
                margin_mode=margin_mode,
                order_type=order_type,
                entry_price=float(intent["entry_price"]) if intent.get("entry_price") else None,
                tp=float(intent["tp"]) if intent.get("tp") else None,
                sl=float(intent["sl"]) if intent.get("sl") else None,
                network=str(intent.get("network", "mainnet")),
                mark_price=mark_price,
                source_text=str(intent.get("source_text", "")),
                agent_request_id=agent_request_id,
                confidence=float(intent.get("confidence", 1.0)),
            )
        else:  # OPEN_SHORT
            action_card = build_open_short_params(
                coin=str(intent["coin"]),
                leverage=float(intent["leverage"]),
                usdc_size=float(intent["usdc_size"]),
                margin_mode=margin_mode,
                order_type=order_type,
                entry_price=float(intent["entry_price"]) if intent.get("entry_price") else None,
                tp=float(intent["tp"]) if intent.get("tp") else None,
                sl=float(intent["sl"]) if intent.get("sl") else None,
                network=str(intent.get("network", "mainnet")),
                mark_price=mark_price,
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
        # OPEN_LONG
        {
            "action": "OPEN_LONG",
            "coin": "BTC",
            "leverage": 20,
            "usdc_size": 1000,
            "margin_mode": "cross",
            "order_type": "market",
            "tp": 72000,
            "sl": 66500,
            "source_text": "做多 BTC 20x 1000u，止盈 72000，止损 66500",
        },
        # OPEN_SHORT 限价
        {
            "action": "OPEN_SHORT",
            "coin": "ETH",
            "leverage": 10,
            "usdc_size": 500,
            "margin_mode": "isolated",
            "order_type": "limit",
            "entry_price": 3650,
            "tp": 3450,
            "sl": 3720,
            "source_text": "ETH 10x 限价 3650 开空 500u",
        },
    ]

    for i, intent in enumerate(test_cases):
        # 模拟传入 mark_price
        mark_prices = {"BTC": 68450.5, "ETH": 3650.0}
        coin = intent.get("coin", "BTC")
        result = action_open_position(intent, mark_price=mark_prices.get(coin))
        print(f"\n=== Test case {i+1}: {intent.get('action')} ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
