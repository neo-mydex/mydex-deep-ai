"""
测试 get_market.py
"""

import pytest
from src.tools.perp.get_market import (
    get_all_mids,
    get_perp_mid_price,
    get_coin_info,
    get_market_price,
    is_perp_listed,
)


class TestGetMarket:
    """get_market 模块测试"""

    def test_normalize_coin(self):
        """测试币种名称标准化"""
        from src.tools.perp._normalize_intent import normalize_coin

        assert normalize_coin("btc") == "BTC"
        assert normalize_coin("BTC") == "BTC"
        assert normalize_coin("Eth") == "ETH"
        assert normalize_coin(None) is None

    def test_get_coin_info_returns_structure(self):
        """测试 get_coin_info 返回结构"""
        # 只测试返回结构，不测试实际网络
        result = get_coin_info("INVALID_COIN_THAT_DOES_NOT_EXIST", network="mainnet")

        assert "ok" in result
        assert "coin" in result
        assert "is_listed" in result
        assert result["coin"] == "INVALID_COIN_THAT_DOES_NOT_EXIST"
        assert result["is_listed"] is False

    def test_get_market_price_returns_structure(self):
        """测试 get_market_price 返回结构"""
        result = get_market_price("INVALID_COIN_THAT_DOES_NOT_EXIST", network="mainnet")

        assert "ok" in result
        assert "coin" in result
        assert "is_listed" in result
        assert "mark_price" in result
        assert result["ok"] is False

    def test_is_perp_listed_false_for_invalid(self):
        """测试不存在的币返回 False"""
        assert is_perp_listed("INVALID_COIN") is False
