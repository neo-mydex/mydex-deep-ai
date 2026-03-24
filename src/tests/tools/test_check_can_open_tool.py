"""
测试公开工具 check_can_open.py
"""

from unittest.mock import patch
from src.tools.perp.check_can_open import check_can_open


def test_check_can_open_passes_intent_fields():
    """验证公开工具能正确构造 intent 并调用内部核心逻辑"""
    captured = {}

    def _fake_check_can_open(intent, address, network, timeout):
        captured["intent"] = intent
        captured["address"] = address
        captured["network"] = network
        captured["timeout"] = timeout
        return {"ok": True, "issues": [], "checks": {}}

    with patch("src.tools.perp.check_can_open._check_can_open_with_intent", _fake_check_can_open):
        result = check_can_open(
            address="0xabc",
            coin="ETH",
            side="short",
            size=0.01,
            leverage=5,
            order_type="limit",
            entry_price=2500.0,
            network="mainnet",
            timeout=10.0,
        )

    assert result["ok"] is True
    assert captured["address"] == "0xabc"
    assert captured["network"] == "mainnet"
    assert captured["timeout"] == 10.0
    assert captured["intent"]["coin"] == "ETH"
    assert captured["intent"]["side"] == "short"
    assert captured["intent"]["size"] == 0.01
    assert captured["intent"]["leverage"] == 5
    assert captured["intent"]["order_type"] == "limit"
    assert captured["intent"]["entry_price"] == 2500.0
