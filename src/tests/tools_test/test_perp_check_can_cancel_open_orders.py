import pytest
from unittest.mock import patch

MOCK_ORDERS_RESPONSE = {
    "ok": True,
    "address": "0x123",
    "network": "mainnet",
    "coin": None,
    "has_open_orders": True,
    "open_order_count": 2,
    "has_tpsl_orders": False,
    "tpsl_order_count": 0,
    "orders": [
        {
            "oid": 123456,
            "coin": "BTC",
            "side": "B",
            "sz": "0.02",
            "limitPx": "67000",
            "orderType": "Limit",
            "reduceOnly": False,
            "isTrigger": False,
            "isPositionTpsl": False,
            "timestamp": 1712000000000,
        },
        {
            "oid": 789012,
            "coin": "ETH",
            "side": "B",
            "sz": "1.0",
            "limitPx": "3500",
            "orderType": "Limit",
            "reduceOnly": False,
            "isTrigger": False,
            "isPositionTpsl": False,
            "timestamp": 1712000001000,
        },
    ],
}

MOCK_ORDERS_EMPTY_RESPONSE = {
    "ok": True,
    "address": "0x123",
    "network": "mainnet",
    "coin": None,
    "has_open_orders": False,
    "open_order_count": 0,
    "has_tpsl_orders": False,
    "tpsl_order_count": 0,
    "orders": [],
}


class TestCheckCanCancelOpenOrders:
    """perp_check_can_cancel_impl 测试"""

    @patch("src.tools.perp.check_can_cancel.perp_get_open_orders_impl")
    def test_has_matching_orders(self, mock_get_orders):
        """测试有匹配的订单"""
        mock_get_orders.return_value = MOCK_ORDERS_RESPONSE

        from src.tools.perp.check_can_cancel import perp_check_can_cancel_impl
        result = perp_check_can_cancel_impl(
            address="0x123",
            coin="BTC",
            order_type="limit",
        )

        assert result["ok"] is True
        assert len(result["matching_orders"]) == 1
        assert result["matching_orders"][0]["coin"] == "BTC"
        assert result["matching_orders"][0]["oid"] == 123456

    @patch("src.tools.perp.check_can_cancel.perp_get_open_orders_impl")
    def test_no_matching_orders(self, mock_get_orders):
        """测试没有匹配的订单"""
        mock_get_orders.return_value = MOCK_ORDERS_RESPONSE

        from src.tools.perp.check_can_cancel import perp_check_can_cancel_impl
        result = perp_check_can_cancel_impl(
            address="0x123",
            coin="BTC",
            order_type="sl",
        )

        assert result["ok"] is False
        assert len(result["matching_orders"]) == 0

    @patch("src.tools.perp.check_can_cancel.perp_get_open_orders_impl")
    def test_filter_by_coin_only(self, mock_get_orders):
        """测试只按 coin 筛选"""
        mock_get_orders.return_value = MOCK_ORDERS_RESPONSE

        from src.tools.perp.check_can_cancel import perp_check_can_cancel_impl
        result = perp_check_can_cancel_impl(
            address="0x123",
            coin="BTC",
        )

        assert result["ok"] is True
        assert len(result["matching_orders"]) == 1

    @patch("src.tools.perp.check_can_cancel.perp_get_open_orders_impl")
    def test_no_filters_returns_all(self, mock_get_orders):
        """测试没有筛选条件时返回所有订单"""
        mock_get_orders.return_value = MOCK_ORDERS_RESPONSE

        from src.tools.perp.check_can_cancel import perp_check_can_cancel_impl
        result = perp_check_can_cancel_impl(
            address="0x123",
        )

        assert result["ok"] is True
        assert len(result["matching_orders"]) == 2

    @patch("src.tools.perp.check_can_cancel.perp_get_open_orders_impl")
    def test_empty_orders(self, mock_get_orders):
        """测试没有挂单"""
        mock_get_orders.return_value = MOCK_ORDERS_EMPTY_RESPONSE

        from src.tools.perp.check_can_cancel import perp_check_can_cancel_impl
        result = perp_check_can_cancel_impl(
            address="0x123",
        )

        assert result["ok"] is False
        assert len(result["matching_orders"]) == 0
