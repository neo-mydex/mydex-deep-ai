"""
测试 normalize_intent.py
"""

import pytest
from src.tools.perp._normalize_intent import (
    normalize_side,
    normalize_order_type,
    normalize_coin,
    normalize_leverage,
    normalize_size,
    normalize_intent,
)


class TestNormalizeSide:
    """normalize_side 测试"""

    def test_valid_sides(self):
        assert normalize_side("long") == "long"
        assert normalize_side("LONG") == "long"
        assert normalize_side("buy") == "long"
        assert normalize_side("多") == "long"
        assert normalize_side("做多") == "long"

        assert normalize_side("short") == "short"
        assert normalize_side("SHORT") == "short"
        assert normalize_side("sell") == "short"
        assert normalize_side("空") == "short"
        assert normalize_side("做空") == "short"

    def test_invalid_side(self):
        assert normalize_side("invalid") is None
        assert normalize_side(None) is None
        assert normalize_side("") is None


class TestNormalizeOrderType:
    """normalize_order_type 测试"""

    def test_valid_types(self):
        assert normalize_order_type("market") == "market"
        assert normalize_order_type("MARKET") == "market"
        assert normalize_order_type("市价") == "market"
        assert normalize_order_type("m") == "market"

        assert normalize_order_type("limit") == "limit"
        assert normalize_order_type("LIMIT") == "limit"
        assert normalize_order_type("限价") == "limit"
        assert normalize_order_type("l") == "limit"

    def test_default_market(self):
        assert normalize_order_type(None) == "market"

    def test_invalid_type(self):
        assert normalize_order_type("invalid") is None


class TestNormalizeCoin:
    """normalize_coin 测试"""

    def test_uppercase(self):
        assert normalize_coin("btc") == "BTC"
        assert normalize_coin("Eth") == "ETH"
        assert normalize_coin("SOL") == "SOL"

    def test_strip(self):
        assert normalize_coin(" BTC ") == "BTC"

    def test_none(self):
        assert normalize_coin(None) is None


class TestNormalizeLeverage:
    """normalize_leverage 测试"""

    def test_valid_leverage(self):
        assert normalize_leverage(10) == 10.0
        assert normalize_leverage("20") == 20.0
        assert normalize_leverage(50.5) == 50.5

    def test_invalid_leverage(self):
        assert normalize_leverage(0) is None
        assert normalize_leverage(-10) is None
        assert normalize_leverage("invalid") is None
        assert normalize_leverage(None) is None


class TestNormalizeSize:
    """normalize_size 测试"""

    def test_valid_size(self):
        assert normalize_size(0.01) == 0.01
        assert normalize_size("1.5") == 1.5

    def test_invalid_size(self):
        assert normalize_size(0) is None
        assert normalize_size(-1) is None
        assert normalize_size(None) is None


class TestNormalizeIntent:
    """normalize_intent 综合测试"""

    def test_complete_intent(self):
        intent = {
            "coin": "btc",
            "side": "LONG",
            "size": "0.01",
            "leverage": 50,
            "order_type": "market",
        }
        result = normalize_intent(intent)

        assert result["ok"] is True
        assert result["normalized"]["coin"] == "BTC"
        assert result["normalized"]["side"] == "long"
        assert result["normalized"]["size"] == 0.01
        assert result["normalized"]["leverage"] == 50.0
        assert result["missing_fields"] == []

    def test_missing_required_fields(self):
        intent = {"side": "long"}
        result = normalize_intent(intent)

        assert result["ok"] is False
        assert "coin" in result["missing_fields"]

    def test_limit_order_needs_entry_price(self):
        intent = {
            "coin": "BTC",
            "side": "long",
            "size": 0.01,
            "leverage": 10,
            "order_type": "limit",
            # 缺少 entry_price
        }
        result = normalize_intent(intent)

        assert result["ok"] is False
        assert "entry_price" in result["invalid_fields"]
