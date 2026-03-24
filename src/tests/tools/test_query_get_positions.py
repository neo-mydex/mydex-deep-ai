"""
测试 get_positions.py
"""

import pytest
from src.tools.perp.get_positions import get_user_position


class TestGetPositions:
    """get_positions 模块测试"""

    def test_get_user_position_returns_structure(self):
        """测试 get_user_position 返回结构"""
        # 使用一个确定不存在的地址测试
        result = get_user_position(
            address="0x0000000000000000000000000000000000000000",
            coin="INVALID_COIN",
            network="mainnet",
        )

        assert "ok" in result
        assert "address" in result
        assert "coin" in result
        assert "has_position" in result
        assert "position_side" in result
        assert "position_size" in result

    def test_no_position_returns_flat(self):
        """测试不存在的仓位返回 flat"""
        result = get_user_position(
            address="0x0000000000000000000000000000000000000000",
            coin="INVALID_COIN",
            network="mainnet",
        )

        assert result["ok"] is True
        assert result["has_position"] is False
        assert result["position_side"] == "flat"
        assert result["position_size"] is None
