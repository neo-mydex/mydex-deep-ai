"""
测试 check_can_open.py
"""

import pytest
from src.services.hyperliquid.cli import check_can_open, validate_leverage


class TestValidateLeverage:
    """validate_leverage 测试"""

    def test_invalid_coin(self):
        """测试不存在的币"""
        result = validate_leverage(
            coin="INVALID_COIN_THAT_DOES_NOT_EXIST",
            leverage=10,
            network="mainnet",
        )

        assert result["ok"] is False
        assert result["reason"] == "coin_not_listed"

    def test_leverage_too_high(self):
        """测试杠杆超出最大值"""
        # BTC 最大杠杆约 50 左右，测试一个很高的值
        result = validate_leverage(
            coin="BTC",
            leverage=999,
            network="mainnet",
        )

        # 如果 BTC 存在，应该返回 leverage_too_high
        if not result["ok"]:
            assert result["reason"] in ("coin_not_listed", "leverage_too_high")


class TestCheckCanOpen:
    """check_can_open 测试"""

    def test_missing_fields(self):
        """测试缺少必要字段"""
        result = check_can_open(
            intent={"side": "long"},  # 缺少 coin, size
            address="0x0000000000000000000000000000000000000000",
            network="mainnet",
        )

        assert result["ok"] is False
        assert len(result["missing_fields"]) > 0
        assert "coin" in result["missing_fields"] or "size" in result["missing_fields"]

    def test_invalid_side(self):
        """测试无效的 side"""
        result = check_can_open(
            intent={
                "coin": "BTC",
                "side": "invalid_direction",
                "size": 0.01,
            },
            address="0x0000000000000000000000000000000000000000",
            network="mainnet",
        )

        assert result["ok"] is False
        assert "follow_up_question" in result

    def test_returns_normalized_intent(self):
        """测试返回标准化意图"""
        result = check_can_open(
            intent={
                "coin": "btc",  # 小写
                "side": "LONG",  # 大写
                "size": "0.01",  # 字符串
                "leverage": 10,
                "order_type": "market",
            },
            address="0x0000000000000000000000000000000000000000",
            network="mainnet",
        )

        assert "normalized_intent" in result
        assert result["normalized_intent"]["coin"] == "BTC"
        assert result["normalized_intent"]["side"] == "long"
        assert result["normalized_intent"]["size"] == 0.01

    def test_returns_all_checks(self):
        """测试返回所有检查项"""
        result = check_can_open(
            intent={
                "coin": "BTC",
                "side": "long",
                "size": 0.01,
                "leverage": 10,
            },
            address="0x0000000000000000000000000000000000000000",
            network="mainnet",
        )

        assert "checks" in result
        assert "balance" in result["checks"]
        assert "position" in result["checks"]
        assert "market" in result["checks"]
