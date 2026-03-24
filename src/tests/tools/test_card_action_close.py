"""
测试 action_close.py
"""

import pytest
from src.tools.card.action_close import build_close_position_params, action_close_position


class TestBuildClosePositionParams:
    """build_close_position_params 测试"""

    def test_close_full_long(self):
        """测试全平多仓"""
        result = build_close_position_params(
            coin="BTC",
            position_side="long",
            position_size=1.5,
            close_size=None,  # 全平
            mark_price=50000,
        )

        assert result["action"] == "CLOSE_POSITION"
        assert result["asset"] == "BTC"
        assert result["close_mode"] == "full"
        # 检查 execution_plan
        close_step = result["execution_plan"][0]
        assert close_step["intent"] == "CLOSE_POSITION"
        assert close_step["isLong"] is True
        assert close_step["isFullClose"] is True

    def test_close_full_short(self):
        """测试全平空仓"""
        result = build_close_position_params(
            coin="ETH",
            position_side="short",
            position_size=2.0,
            mark_price=3500,
        )

        assert result["close_mode"] == "full"
        close_step = result["execution_plan"][0]
        assert close_step["isLong"] is False

    def test_close_partial(self):
        """测试部分平仓"""
        result = build_close_position_params(
            coin="BTC",
            position_side="long",
            position_size=1.5,
            close_size=0.5,
            mark_price=50000,
        )

        assert result["close_mode"] == "partial"
        close_step = result["execution_plan"][0]
        assert float(close_step["size"]) == 0.5
        assert close_step["isFullClose"] is False
        assert "close_ratio" in result["meta"]

    def test_close_partial_full_by_size(self):
        """测试平仓数量大于等于持仓量视为全平"""
        result = build_close_position_params(
            coin="BTC",
            position_side="long",
            position_size=1.0,
            close_size=2.0,  # 超过持仓量
            mark_price=50000,
        )

        assert result["close_mode"] == "full"


class TestActionClosePosition:
    """action_close_position 测试"""

    def test_missing_coin(self):
        """测试缺少 coin"""
        result = action_close_position({})

        assert result["ok"] is False
        assert "coin" in result["error"].lower()

    def test_no_position_info(self):
        """测试没有持仓信息时返回错误"""
        result = action_close_position({
            "coin": "BTC",
            "close_size": None,
        })

        assert result["ok"] is False
        assert "没有持仓" in result["error"]

    def test_valid_close_all(self):
        """测试有效的全平"""
        result = action_close_position({
            "coin": "BTC",
            "close_size": None,
        }, position_info={
            "position_side": "long",
            "position_size": 1.5,
            "mark_px": 50000,
        })

        assert result["ok"] is True
        assert result["action_card"] is not None
        assert result["action_card"]["close_mode"] == "full"

    def test_valid_partial_close(self):
        """测试有效的部分平仓"""
        result = action_close_position({
            "coin": "BTC",
            "close_size": 0.5,
        }, position_info={
            "position_side": "long",
            "position_size": 1.5,
            "mark_px": 50000,
        })

        assert result["ok"] is True
        assert result["action_card"]["close_mode"] == "partial"

    def test_close_size_exceeds_position(self):
        """测试平仓数量超过持仓"""
        result = action_close_position({
            "coin": "BTC",
            "close_size": 10.0,  # 超过持仓
        }, position_info={
            "position_side": "long",
            "position_size": 1.5,
            "mark_px": 50000,
        })

        assert result["ok"] is False

    def test_negative_close_size_rejected(self):
        """测试负数平仓数量被拒绝"""
        result = action_close_position({
            "coin": "BTC",
            "close_size": -1,
        }, position_info={
            "position_side": "long",
            "position_size": 1.5,
            "mark_px": 50000,
        })

        assert result["ok"] is False
        assert "必须" in result["error"]
