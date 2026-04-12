import pytest
from src.tools.action.confirm_perp_cancel_open_orders import (
    confirm_perp_cancel_open_orders_impl,
    CancelItem,
)


class TestConfirmCancelOpenOrdersImpl:
    """confirm_perp_cancel_open_orders_impl 测试"""

    def test_cancel_single_order(self):
        """测试取消单个订单"""
        orders = [
            CancelItem(
                oid=123456,
                coin="BTC",
                size="0.02",
                order_type="limit",
                direction="long",
                limit_price="67000",
                trigger_price=None,
                reduce_only=False,
                timestamp=1712000000000,
            )
        ]
        result = confirm_perp_cancel_open_orders_impl(
            orders=orders,
            source_text="取消 BTC 限价单",
        )

        assert result["action"] == "CANCEL_OPEN_ORDER"
        assert len(result["execution_plan"]) == 1
        intent = result["execution_plan"][0]
        assert intent["intent"] == "CANCEL_OPEN_ORDER"
        assert intent["oid"] == "123456"
        assert intent["coin"] == "BTC"
        assert intent["direction"] == "long"
        assert intent["type"] == "limit"
        assert intent["size"] == "0.02"
        assert intent["limitPrice"] == "67000"

    def test_cancel_multiple_orders(self):
        """测试批量取消多个订单"""
        orders = [
            CancelItem(
                oid=123456,
                coin="BTC",
                size="0.02",
                order_type="limit",
                direction="long",
                limit_price="67000",
                trigger_price=None,
                reduce_only=False,
                timestamp=1712000000000,
            ),
            CancelItem(
                oid=789012,
                coin="ETH",
                size="1.0",
                order_type="tp",
                direction="short",
                limit_price=None,
                trigger_price="3500",
                reduce_only=True,
                timestamp=1712000001000,
            ),
        ]
        result = confirm_perp_cancel_open_orders_impl(
            orders=orders,
            source_text="取消 BTC 限价单和 ETH 止盈单",
        )

        assert result["action"] == "CANCEL_OPEN_ORDER"
        assert len(result["execution_plan"]) == 2
        assert result["execution_plan"][0]["oid"] == "123456"
        assert result["execution_plan"][1]["oid"] == "789012"

    def test_cancel_no_orders(self):
        """测试没有订单时返回空结构+error"""
        result = confirm_perp_cancel_open_orders_impl(
            orders=[],
            source_text="取消所有挂单",
        )

        assert result["action"] == "CANCEL_OPEN_ORDER"
        assert len(result["execution_plan"]) == 0
        assert "error" in result["meta"]
