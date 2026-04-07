"""
测试 check_can_close.py
"""

import pytest
from src.services.hyperliquid.cli import check_can_close


class TestCheckCanClose:
    """check_can_close 测试"""

    def test_no_position_returns_issue(self):
        """测试没有仓位时返回 issue"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="INVALID_COIN",
            network="mainnet",
        )

        assert "issues" in result
        # 没有仓位应该返回一个 issue
        has_no_position_issue = any(
            issue.get("code") == "no_position" for issue in result["issues"]
        )
        assert has_no_position_issue

    def test_returns_position_info(self):
        """测试返回仓位信息"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="INVALID_COIN",
            network="mainnet",
        )

        assert "position_info" in result
        assert "has_position" in result["position_info"]
        assert "position_side" in result["position_info"]

    def test_returns_checks(self):
        """测试返回检查项"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="INVALID_COIN",
            network="mainnet",
        )

        assert "checks" in result
        assert "position" in result["checks"]
