"""
意图标准化辅助模块
"""

from typing import Any, Literal

Side = Literal["long", "short"]
OrderType = Literal["market", "limit"]
Network = Literal["mainnet", "testnet"]


def normalize_side(side: str | None) -> Side | None:
    """标准化方向"""
    if side is None:
        return None
    s = str(side).lower().strip()
    if s in ("long", "buy", "多", "做多", "开多"):
        return "long"
    if s in ("short", "sell", "空", "做空", "开空"):
        return "short"
    return None


def normalize_order_type(order_type: str | None) -> OrderType | None:
    """标准化订单类型"""
    if order_type is None:
        return "market"  # 默认市价单
    ot = str(order_type).lower().strip()
    if ot in ("market", "市价", "市价单", "m"):
        return "market"
    if ot in ("limit", "限价", "限价单", "l"):
        return "limit"
    return None


def normalize_coin(coin: str | None) -> str | None:
    """标准化币种名称"""
    if coin is None:
        return None
    return str(coin).upper().strip()


def normalize_leverage(leverage: float | int | str | None) -> float | None:
    """标准化杠杆"""
    if leverage is None:
        return None
    try:
        val = float(leverage)
        if val <= 0:
            return None
        return val
    except (TypeError, ValueError):
        return None


def normalize_size(size: float | int | str | None) -> float | None:
    """标准化数量"""
    if size is None:
        return None
    try:
        val = float(size)
        if val <= 0:
            return None
        return val
    except (TypeError, ValueError):
        return None


def normalize_intent(intent: dict[str, Any]) -> dict[str, Any]:
    """
    标准化用户开仓意图

    参数示例:
    {
        "coin": "btc",
        "side": "LONG",
        "size": "0.01",
        "leverage": 50,
        "order_type": "market",
        "entry_price": 50000,
    }

    返回结构:
    {
        "ok": bool,
        "normalized": {
            "coin": str | None,
            "side": "long" | "short" | None,
            "size": float | None,
            "leverage": float | None,
            "order_type": "market" | "limit" | None,
            "entry_price": float | None,
        },
        "missing_fields": list[str],
        "invalid_fields": list[str],
    }
    """
    normalized = {
        "coin": normalize_coin(intent.get("coin")),
        "side": normalize_side(intent.get("side")),
        "size": normalize_size(intent.get("size")),
        "leverage": normalize_leverage(intent.get("leverage")),
        "order_type": normalize_order_type(intent.get("order_type")),
        "entry_price": None,
    }

    # 处理限价单的输入价格
    if normalized["order_type"] == "limit":
        entry_price_raw = intent.get("entry_price")
        if entry_price_raw is not None:
            try:
                normalized["entry_price"] = float(entry_price_raw)
            except (TypeError, ValueError):
                normalized["entry_price"] = None

    # 检查缺失字段
    missing_fields = []
    if normalized["coin"] is None:
        missing_fields.append("coin")
    if normalized["side"] is None:
        missing_fields.append("side")
    if normalized["size"] is None:
        missing_fields.append("size")

    # 检查无效字段
    invalid_fields = []
    if normalized["order_type"] == "limit" and normalized["entry_price"] is None:
        invalid_fields.append("entry_price")

    return {
        "ok": len(missing_fields) == 0 and len(invalid_fields) == 0,
        "normalized": normalized,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
    }


if __name__ == "__main__":
    import json

    # 测试用例
    test_cases = [
        {"coin": "btc", "side": "LONG", "size": "0.01", "leverage": 50, "order_type": "market"},
        {"coin": "ETH", "side": "short", "size": 1.5, "leverage": "20", "order_type": "limit", "entry_price": 3000},
        {"side": "long"},  # 缺失 coin
        {"coin": "BTC", "size": "0.01"},  # 缺失 side
    ]

    for i, intent in enumerate(test_cases):
        result = normalize_intent(intent)
        print(f"\n=== Test case {i+1} ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
