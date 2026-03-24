"""
止盈止损 Action 模块 (SET_TPSL)

按 Feature_HyperliquidAIAgentIntent.zh-CN.md 文档实现

Simple Mode 示例:
{
    "action": "SET_TPSL",
    "asset": "BTC",
    "tp": 72000,
    "sl": 66500,
    "confidence": 0.98,
    "source_text": "BTC 仓位止盈 72000，止损 66500"
}

Advanced Mode:
{
    "action": "SET_TPSL",
    "execution_plan": [
        {
            "intent": "SET_TPSL",
            "coin": "BTC",
            "size": "0.2921",
            "tpPrice": "72000",
            "slPrice": "66500",
            "existingTpOid": 0,
            "existingSlOid": 0
        }
    ],
    "meta": {
        "source_text": "BTC 仓位止盈 72000，止损 66500",
        "agent_request_id": "hl-set-tpsl-20260324-001"
    }
}

更新已有 TPSL:
{
    "action": "SET_TPSL",
    "execution_plan": [
        {
            "intent": "SET_TPSL",
            "coin": "BTC",
            "size": "0.2921",
            "tpPrice": "72500",
            "slPrice": "66800",
            "existingTpOid": 18273645,
            "existingSlOid": 18273646
        }
    ]
}
"""

from typing import Any

from .types import PositionSide


def build_set_tpsl_params(
    coin: str,
    position_side: PositionSide,
    position_size: float,
    tp: float | None = None,
    sl: float | None = None,
    existing_tp_oid: int = 0,
    existing_sl_oid: int = 0,
    network: str = "mainnet",
    source_text: str = "",
    agent_request_id: str = "",
    confidence: float = 1.0,
) -> dict[str, Any]:
    """
    构建止盈止损参数 (SET_TPSL)

    参数:
        coin: 币种（如 "BTC"）
        position_side: 持仓方向（"long", "short", "flat"）
        position_size: 当前持仓数量
        tp: 止盈价格
        sl: 止损价格
        existing_tp_oid: 已有的止盈订单 ID（0 = 新建）
        existing_sl_oid: 已有的止损订单 ID（0 = 新建）
        network: 网络
        source_text: 原始用户输入
        agent_request_id: 请求 ID
        confidence: 置信度

    返回: Advanced Mode 结构
    """
    if position_side == "flat" or position_size == 0:
        raise ValueError(f"{coin} 没有持仓，无法设置 TPSL")

    # 验证 TP/SL 价格逻辑
    if tp is not None and sl is not None:
        if position_side == "long":
            # 多仓：tp > entry, sl < entry
            if tp <= sl:
                raise ValueError(f"多仓止盈价格({tp})必须大于止损价格({sl})")
        else:
            # 空仓：tp < entry, sl > entry
            if tp >= sl:
                raise ValueError(f"空仓止盈价格({tp})必须小于止损价格({sl})")

    execution_plan: list[dict[str, Any]] = []

    if tp is not None:
        execution_plan.append({
            "intent": "SET_TPSL",
            "coin": coin.upper(),
            "size": str(round(position_size, 6)),
            "tpPrice": str(tp),
            "slPrice": None,  # TP 和 SL 分开
            "existingTpOid": existing_tp_oid,
            "existingSlOid": 0,
        })

    if sl is not None:
        execution_plan.append({
            "intent": "SET_TPSL",
            "coin": coin.upper(),
            "size": str(round(position_size, 6)),
            "tpPrice": None,
            "slPrice": str(sl),
            "existingTpOid": 0,
            "existingSlOid": existing_sl_oid,
        })

    # 如果 TP 和 SL 都有，可以合并成一个（如果有 existing OID）
    if tp is not None and sl is not None and existing_tp_oid == 0 and existing_sl_oid == 0:
        execution_plan = [{
            "intent": "SET_TPSL",
            "coin": coin.upper(),
            "size": str(round(position_size, 6)),
            "tpPrice": str(tp),
            "slPrice": str(sl),
            "existingTpOid": 0,
            "existingSlOid": 0,
        }]

    meta: dict[str, Any] = {
        "source_text": source_text,
        "agent_request_id": agent_request_id,
    }

    result: dict[str, Any] = {
        "action": "SET_TPSL",
        "execution_plan": execution_plan,
        "meta": meta,
    }

    # Simple Mode 字段
    result["asset"] = coin.upper()
    if tp is not None:
        result["tp"] = tp
    if sl is not None:
        result["sl"] = sl
    if confidence != 1.0:
        result["confidence"] = confidence
    if source_text:
        result["source_text"] = source_text

    return result


def action_set_tpsl(
    intent: dict[str, Any],
    position_info: dict[str, Any] | None = None,
    agent_request_id: str = "",
) -> dict[str, Any]:
    """
    外部接口：接收 Agent 传来的标准化意图，返回前端执行所需的参数

    参数:
        intent: 标准化后的 TPSL 意图
            - action: "SET_TPSL"
            - coin: 币种
            - tp: 止盈价格
            - sl: 止损价格
            - existing_tp_oid: 已有的止盈订单 ID
            - existing_sl_oid: 已有的止损订单 ID
            - source_text: 原始输入
            - confidence: 置信度
        position_info: 当前持仓信息（可选）
            - position_side: "long" / "short" / "flat"
            - position_size: float
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
    tp = float(intent["tp"]) if intent.get("tp") is not None else None
    sl = float(intent["sl"]) if intent.get("sl") is not None else None

    # 必须至少有一个
    if tp is None and sl is None:
        return {
            "ok": False,
            "error": "至少需要提供 tp 或 sl",
            "action_card": None,
        }

    # 从 position_info 获取持仓信息
    position_side = "flat"
    position_size = 0.0

    if position_info:
        position_side = position_info.get("position_side", "flat")
        position_size = float(position_info.get("position_size") or 0)

    # 如果 intent 中有明确值，覆盖上面的
    if intent.get("position_side"):
        position_side = intent["position_side"]
    if intent.get("position_size"):
        position_size = float(intent["position_size"])

    # 验证有持仓
    if position_side == "flat" or position_size == 0:
        return {
            "ok": False,
            "error": f"{coin} 没有持仓，无法设置 TPSL",
            "action_card": None,
        }

    existing_tp_oid = int(intent.get("existing_tp_oid") or 0)
    existing_sl_oid = int(intent.get("existing_sl_oid") or 0)

    try:
        action_card = build_set_tpsl_params(
            coin=coin,
            position_side=position_side,
            position_size=position_size,
            tp=tp,
            sl=sl,
            existing_tp_oid=existing_tp_oid,
            existing_sl_oid=existing_sl_oid,
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
            "error": str(e),
            "action_card": None,
        }


if __name__ == "__main__":
    import json

    # 测试用例
    test_cases = [
        # 设置 BTC TPSL
        {
            "action": "SET_TPSL",
            "coin": "BTC",
            "tp": 72000,
            "sl": 66500,
            "source_text": "BTC 仓位止盈 72000，止损 66500",
        },
        # 只设置止盈
        {
            "action": "SET_TPSL",
            "coin": "ETH",
            "tp": 3800,
            "source_text": "ETH 止盈 3800",
        },
        # 更新已有 TPSL
        {
            "action": "SET_TPSL",
            "coin": "SOL",
            "tp": 200,
            "sl": 150,
            "existing_tp_oid": 18273645,
            "existing_sl_oid": 18273646,
            "source_text": "更新 SOL TPSL",
        },
    ]

    # 模拟持仓信息
    position_infos = {
        "BTC": {"position_side": "long", "position_size": 1.5},
        "ETH": {"position_side": "short", "position_size": 2.0},
        "SOL": {"position_side": "long", "position_size": 10.0},
    }

    for i, intent in enumerate(test_cases):
        coin = intent.get("coin")
        result = action_set_tpsl(intent, position_info=position_infos.get(coin))
        print(f"\n=== Test case {i+1}: {coin} ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
