"""
测试 action_open.py
"""

import pytest
from src.tools.card.action_open import build_open_long_params, build_open_short_params, action_open_position


class TestBuildOpenLongParams:
    """build_open_long_params 测试"""

    def test_market_long_basic(self):
        """测试市价开多基本功能"""
        result = build_open_long_params(
            coin="BTC",
            leverage=10,
            usdc_size=1000,
            mark_price=50000,
        )

        assert result["action"] == "OPEN_LONG"
        assert result["asset"] == "BTC"
        assert result["leverage"] == 10
        assert result["usdc_size"] == 1000
        assert result["margin_mode"] == "cross"
        assert result["order_type"] == "market"
        assert len(result["execution_plan"]) == 2

    def test_limit_long_with_entry_price(self):
        """测试限价开多"""
        result = build_open_long_params(
            coin="ETH",
            leverage=20,
            usdc_size=500,
            order_type="limit",
            entry_price=3500,
            mark_price=3600,
        )

        assert result["action"] == "OPEN_LONG"
        assert result["order_type"] == "limit"
        # 检查 execution_plan 中的限价单
        open_order_step = result["execution_plan"][1]
        assert open_order_step["limitPrice"] == 3500

    def test_long_with_tp_sl(self):
        """测试开多带止盈止损"""
        result = build_open_long_params(
            coin="BTC",
            leverage=10,
            usdc_size=1000,
            tp=60000,
            sl=45000,
            mark_price=50000,
        )

        open_order_step = result["execution_plan"][1]
        assert open_order_step["tpPrice"] == "60000"
        assert open_order_step["slPrice"] == "45000"

    def test_isolated_margin_mode(self):
        """测试逐仓模式"""
        result = build_open_long_params(
            coin="BTC",
            leverage=5,
            usdc_size=1000,
            margin_mode="isolated",
            mark_price=50000,
        )

        assert result["margin_mode"] == "isolated"
        update_leverage_step = result["execution_plan"][0]
        assert update_leverage_step["isCross"] is False


class TestBuildOpenShortParams:
    """build_open_short_params 测试"""

    def test_market_short_basic(self):
        """测试市价开空基本功能"""
        result = build_open_short_params(
            coin="BTC",
            leverage=10,
            usdc_size=1000,
            mark_price=50000,
        )

        assert result["action"] == "OPEN_SHORT"
        assert result["asset"] == "BTC"
        # 检查 execution_plan 中 isBuy = False
        open_order_step = result["execution_plan"][1]
        assert open_order_step["isBuy"] is False

    def test_limit_short_with_entry_price(self):
        """测试限价开空"""
        result = build_open_short_params(
            coin="ETH",
            leverage=20,
            usdc_size=500,
            order_type="limit",
            entry_price=3700,
            mark_price=3600,
        )

        assert result["order_type"] == "limit"
        open_order_step = result["execution_plan"][1]
        assert open_order_step["limitPrice"] == 3700


class TestActionOpenPosition:
    """action_open_position 测试"""

    def test_missing_required_fields(self):
        """测试缺少必要字段"""
        result = action_open_position({"side": "long"})  # 缺少 coin, leverage, usdc_size

        assert result["ok"] is False
        assert result["error"] is not None
        assert "coin" in result["error"] or "leverage" in result["error"] or "usdc_size" in result["error"]

    def test_valid_market_long_order(self):
        """测试有效的市价开多"""
        result = action_open_position({
            "coin": "BTC",
            "side": "long",
            "leverage": 10,
            "usdc_size": 1000,
            "order_type": "market",
        })

        assert result["ok"] is True
        assert result["action_card"] is not None
        assert result["error"] is None
        assert result["action_card"]["action"] == "OPEN_LONG"

    def test_valid_market_short_order(self):
        """测试有效的市价开空"""
        result = action_open_position({
            "coin": "BTC",
            "side": "short",
            "leverage": 10,
            "usdc_size": 1000,
            "order_type": "market",
        })

        assert result["ok"] is True
        assert result["action_card"]["action"] == "OPEN_SHORT"

    def test_limit_order_without_entry_price(self):
        """测试限价单没有价格"""
        result = action_open_position({
            "coin": "BTC",
            "side": "long",
            "leverage": 10,
            "usdc_size": 1000,
            "order_type": "limit",
            # 缺少 entry_price
        })

        assert result["ok"] is False
        assert "entry_price" in result["error"]

    def test_valid_limit_order(self):
        """测试有效的限价单"""
        result = action_open_position({
            "coin": "BTC",
            "side": "long",
            "leverage": 10,
            "usdc_size": 1000,
            "order_type": "limit",
            "entry_price": 50000,
        })

        assert result["ok"] is True
        assert result["action_card"] is not None

    def test_invalid_side(self):
        """测试无效的 side"""
        result = action_open_position({
            "coin": "BTC",
            "side": "invalid_direction",
            "leverage": 10,
            "usdc_size": 1000,
        })

        assert result["ok"] is False
