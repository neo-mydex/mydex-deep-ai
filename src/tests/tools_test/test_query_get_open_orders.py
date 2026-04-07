"""
测试 get_open_orders.py
"""

import pytest
from unittest.mock import patch, MagicMock
from src.services.hyperliquid.cli import get_user_open_orders, _is_tpsl_order


class TestIsTpslOrder:
    """_is_tpsl_order 测试"""

    def test_is_position_tpsl(self):
        """isPositionTpsl=True 视为 TP/SL"""
        assert _is_tpsl_order({"isPositionTpsl": True}) is True
        assert _is_tpsl_order({"isPositionTpsl": False}) is False

    def test_has_trigger_condition(self):
        """有 triggerCondition 视为 TP/SL"""
        assert _is_tpsl_order({"triggerCondition": "Above"}) is True
        assert _is_tpsl_order({"triggerCondition": None}) is False

    def test_order_type_contains_tp_sl_trigger(self):
        """orderType 包含 tp/sl/trigger 视为 TP/SL"""
        assert _is_tpsl_order({"orderType": "TakeProfitMarket"}) is True
        assert _is_tpsl_order({"orderType": "StopLossLimit"}) is True
        assert _is_tpsl_order({"orderType": "TriggerFillOrKill"}) is True
        assert _is_tpsl_order({"orderType": "Limit"}) is False

    def test_has_trigger_px(self):
        """有 triggerPx 视为 TP/SL"""
        assert _is_tpsl_order({"triggerPx": "50000"}) is True
        assert _is_tpsl_order({"triggerPx": None}) is False

    def test_normal_order(self):
        """普通订单不是 TP/SL"""
        assert _is_tpsl_order({
            "coin": "BTC",
            "side": "A",
            "sz": "0.01",
            "limitPx": "60000",
        }) is False


class TestGetUserOpenOrders:
    """get_user_open_orders 测试"""

    @patch("src.services.hyperliquid.info._build_info")
    def test_returns_standard_structure(self, mock_build_info):
        """测试返回标准化结构"""
        mock_info = MagicMock()
        mock_info.frontend_open_orders.return_value = [
            {"oid": 123, "coin": "BTC", "side": "A", "sz": "0.01", "limitPx": "60000"},
            {"oid": 456, "coin": "BTC", "side": "A", "sz": "0.02", "limitPx": "61000", "isPositionTpsl": True},
        ]
        mock_build_info.return_value = mock_info

        result = get_user_open_orders(address="0x123", network="mainnet")

        assert result["ok"] is True
        assert result["address"] == "0x123"
        assert result["network"] == "mainnet"
        assert result["coin"] is None
        assert result["has_open_orders"] is True
        assert result["open_order_count"] == 2
        assert result["has_tpsl_orders"] is True
        assert result["tpsl_order_count"] == 1
        assert len(result["orders"]) == 2

    @patch("src.services.hyperliquid.info._build_info")
    def test_filters_by_coin(self, mock_build_info):
        """测试按 coin 过滤"""
        mock_info = MagicMock()
        mock_info.frontend_open_orders.return_value = [
            {"oid": 123, "coin": "BTC", "side": "A"},
            {"oid": 456, "coin": "ETH", "side": "B"},
        ]
        mock_build_info.return_value = mock_info

        result = get_user_open_orders(address="0x123", coin="BTC", network="mainnet")

        assert result["coin"] == "BTC"
        assert result["open_order_count"] == 1
        assert result["orders"][0]["coin"] == "BTC"

    @patch("src.services.hyperliquid.info._build_info")
    def test_empty_orders(self, mock_build_info):
        """测试无挂单时返回"""
        mock_info = MagicMock()
        mock_info.frontend_open_orders.return_value = []
        mock_build_info.return_value = mock_info

        result = get_user_open_orders(address="0x123", network="mainnet")

        assert result["ok"] is True
        assert result["has_open_orders"] is False
        assert result["open_order_count"] == 0
        assert result["orders"] == []
