"""
测试 get_user_state.py
"""

import pytest
from src.tools.perp.get_user_state import get_account_balance


class TestGetUserState:
    """get_user_state 模块测试"""

    def test_get_account_balance_returns_structure(self):
        """测试 get_account_balance 返回结构"""
        result = get_account_balance(
            address="0x0000000000000000000000000000000000000000",
            network="mainnet",
        )

        assert "ok" in result
        assert "address" in result
        assert "network" in result
        assert "withdrawable" in result
        assert result["ok"] is True

    def test_address_normalized(self):
        """测试地址返回正确"""
        result = get_account_balance(
            address="0x0000000000000000000000000000000000000000",
            network="mainnet",
        )

        assert result["address"] == "0x0000000000000000000000000000000000000000"
        assert result["network"] == "mainnet"
