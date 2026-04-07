"""
测试 hyperliquid service 层 (cli.py 中的业务函数)

直接测试 service 层的纯业务逻辑函数，使用 mock 隔离网络依赖。
"""

import pytest
from unittest.mock import patch, MagicMock

from src.services.hyperliquid.cli import (
    get_market_price,
    get_coin_info,
    get_user_positions,
    get_account_balance,
    get_user_open_orders,
)


class TestGetMarketPrice:
    """get_market_price 测试"""

    @patch("src.services.hyperliquid.cli.get_all_mids")
    def test_returns_correct_structure(self, mock_get_all_mids):
        """测试返回结构包含必要字段"""
        mock_get_all_mids.return_value = {"BTC": "50000.5"}

        result = get_market_price(coin="BTC", network="mainnet")

        assert "ok" in result
        assert "network" in result
        assert "coin" in result
        assert "mark_price" in result
        assert "mark_price_raw" in result
        assert "is_listed" in result
        assert result["coin"] == "BTC"
        assert result["network"] == "mainnet"
        assert result["ok"] is True
        assert result["mark_price"] == 50000.5

    @patch("src.services.hyperliquid.cli.get_all_mids")
    def test_returns_false_for_unlisted_coin(self, mock_get_all_mids):
        """测试不存在的币返回 ok=False"""
        mock_get_all_mids.return_value = {}

        result = get_market_price(coin="INVALID", network="mainnet")

        assert result["ok"] is False
        assert result["mark_price"] is None
        assert result["is_listed"] is False


class TestGetCoinInfo:
    """get_coin_info 测试"""

    @patch("src.services.hyperliquid.cli.get_perp_market_info")
    def test_returns_correct_structure(self, mock_get_perp_market_info):
        """测试返回结构包含必要字段"""
        mock_get_perp_market_info.return_value = {
            "coin": "BTC",
            "listed": True,
            "max_leverage": 50,
            "sz_decimals": 8,
            "is_delisted": False,
            "only_isolated": False,
            "margin_table_id": 1,
        }

        result = get_coin_info(coin="BTC", network="mainnet")

        assert "ok" in result
        assert "coin" in result
        assert "network" in result
        assert "is_listed" in result
        assert "max_leverage" in result
        assert "only_isolated" in result
        assert "sz_decimals" in result
        assert result["ok"] is True
        assert result["coin"] == "BTC"
        assert result["is_listed"] is True
        assert result["max_leverage"] == 50

    @patch("src.services.hyperliquid.cli.get_perp_market_info")
    def test_returns_false_for_unlisted_coin(self, mock_get_perp_market_info):
        """测试不存在的币返回 ok=False"""
        mock_get_perp_market_info.return_value = None

        result = get_coin_info(coin="INVALID", network="mainnet")

        assert result["ok"] is False
        assert result["is_listed"] is False


class TestGetAccountBalance:
    """get_account_balance 测试"""

    @patch("src.services.hyperliquid.cli.user_state")
    def test_returns_correct_structure(self, mock_user_state):
        """测试返回结构包含必要字段"""
        mock_user_state.return_value = {
            "withdrawable": "1000.5",
            "marginSummary": {
                "accountValue": "5000.0",
                "totalMarginUsed": "100.0",
            },
        }

        result = get_account_balance(address="0x123", network="mainnet")

        assert "ok" in result
        assert "address" in result
        assert "network" in result
        assert "withdrawable" in result
        assert "account_value" in result
        assert "total_margin_used" in result
        assert result["ok"] is True
        assert result["address"] == "0x123"
        assert result["withdrawable"] == 1000.5
        assert result["account_value"] == 5000.0
        assert result["total_margin_used"] == 100.0

    @patch("src.services.hyperliquid.cli.user_state")
    def test_handles_invalid_numeric_values(self, mock_user_state):
        """测试处理无效数值"""
        mock_user_state.return_value = {
            "withdrawable": "invalid",
            "marginSummary": {
                "accountValue": None,
                "totalMarginUsed": "invalid",
            },
        }

        result = get_account_balance(address="0x123", network="mainnet")

        assert result["ok"] is True
        assert result["withdrawable"] == 0.0
        assert result["account_value"] is None
        assert result["total_margin_used"] is None


class TestGetUserPositions:
    """get_user_positions 测试"""

    @patch("src.services.hyperliquid.cli.get_all_mids")
    @patch("src.services.hyperliquid.cli.user_state")
    def test_returns_correct_structure(self, mock_user_state, mock_get_all_mids):
        """测试返回结构包含必要字段"""
        mock_user_state.return_value = {
            "assetPositions": [
                {
                    "position": {
                        "coin": "BTC",
                        "szi": "1.5",
                        "entryPx": "45000.0",
                        "liquidationPx": "40000.0",
                        "positionValue": "75000.0",
                        "unrealizedPnl": "500.0",
                        "leverage": {"value": 10, "type": "cross"},
                    }
                }
            ],
            "marginSummary": {
                "accountValue": "50000.0",
                "totalMarginUsed": "10000.0",
            },
            "withdrawable": "1000.0",
        }
        mock_get_all_mids.return_value = {"BTC": "50000.0"}

        result = get_user_positions(address="0x123", network="mainnet")

        assert "ok" in result
        assert "address" in result
        assert "network" in result
        assert "account_value" in result
        assert "withdrawable" in result
        assert "positions" in result
        assert result["ok"] is True
        assert result["address"] == "0x123"
        assert len(result["positions"]) == 1
        assert result["positions"][0]["coin"] == "BTC"
        assert result["positions"][0]["side"] == "long"
        assert result["positions"][0]["size"] == 1.5

    @patch("src.services.hyperliquid.cli.get_all_mids")
    @patch("src.services.hyperliquid.cli.user_state")
    def test_empty_positions(self, mock_user_state, mock_get_all_mids):
        """测试空仓位"""
        mock_user_state.return_value = {
            "assetPositions": [],
            "marginSummary": {},
            "withdrawable": "1000.0",
        }
        mock_get_all_mids.return_value = {}

        result = get_user_positions(address="0x123", network="mainnet")

        assert result["ok"] is True
        assert result["positions"] == []


class TestGetUserOpenOrders:
    """get_user_open_orders 测试"""

    @patch("src.services.hyperliquid.cli.frontend_open_orders")
    def test_returns_correct_structure(self, mock_frontend_open_orders):
        """测试返回结构包含必要字段"""
        mock_frontend_open_orders.return_value = [
            {"coin": "BTC", "orderType": "Limit", "isPositionTpsl": False}
        ]

        result = get_user_open_orders(address="0x123", network="mainnet")

        assert "ok" in result
        assert "address" in result
        assert "network" in result
        assert "coin" in result
        assert "has_open_orders" in result
        assert "open_order_count" in result
        assert "has_tpsl_orders" in result
        assert "tpsl_order_count" in result
        assert "orders" in result
        assert result["ok"] is True
        assert result["has_open_orders"] is True
        assert result["open_order_count"] == 1

    @patch("src.services.hyperliquid.cli.frontend_open_orders")
    def test_filters_by_coin(self, mock_frontend_open_orders):
        """测试按 coin 过滤"""
        mock_frontend_open_orders.return_value = [
            {"coin": "BTC", "orderType": "Limit"},
            {"coin": "ETH", "orderType": "Limit"},
        ]

        result = get_user_open_orders(address="0x123", coin="BTC", network="mainnet")

        assert result["open_order_count"] == 1
        assert result["orders"][0]["coin"] == "BTC"


class TestCliMainImport:
    """测试 CLI 入口可以被导入"""

    def test_cli_main_can_be_imported(self):
        """验证 cli_main 模块可以被正常导入"""
        from src.services.hyperliquid import cli_main

        assert hasattr(cli_main, "main")
        assert callable(cli_main.main)
