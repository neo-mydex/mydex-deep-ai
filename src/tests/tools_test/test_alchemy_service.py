"""
测试 Alchemy 链上资产查询服务

验证 get_wallet_portfolio 和 get_native_balance 的返回结构
"""

import pytest
from unittest.mock import patch, MagicMock

from src.services.alchemy.service import (
    get_wallet_portfolio,
    get_native_balance,
)


class TestGetWalletPortfolio:
    """测试 get_wallet_portfolio 返回结构"""

    @patch("src.services.alchemy.service.post_json")
    @patch("src.services.alchemy.service._fetch_wallet_assets")
    def test_returns_correct_structure_with_empty_assets(
        self,
        mock_fetch,
        mock_post,
    ):
        """无资产时返回正确的空结构"""
        mock_fetch.return_value = ([], None)

        result = get_wallet_portfolio(
            address="0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
            networks=["eth"],
        )

        assert result["ok"] is True
        assert result["address"] == "0x802f71cBf691D4623374E8ec37e32e26d5f74d87"
        assert result["networks"] == ["eth-mainnet"]
        assert result["total_value_usd"] == 0.0
        assert result["asset_count"] == 0
        assert result["assets"] == []
        assert result["breakdown"] == {}

    @patch("src.services.alchemy.service._fetch_wallet_assets")
    def test_returns_correct_structure_with_assets(self, mock_fetch):
        """有资产时返回正确的结构"""
        mock_fetch.return_value = (
            [
                {
                    "network": "Eth",
                    "tokenAddress": None,
                    "tokenMetadata": {"symbol": "ETH", "name": "Ethereum", "decimals": 18},
                    "tokenBalance": "1000000000000000000",
                    "tokenPrices": [{"currency": "USD", "value": "2000"}],
                },
            ],
            None,
        )

        result = get_wallet_portfolio(
            address="0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
            networks=["eth"],
        )

        assert result["ok"] is True
        assert result["address"] == "0x802f71cBf691D4623374E8ec37e32e26d5f74d87"
        assert "networks" in result
        assert "total_value_usd" in result
        assert "asset_count" in result
        assert "assets" in result
        assert "breakdown" in result
        assert isinstance(result["assets"], list)

    @patch("src.services.alchemy.service._fetch_wallet_assets")
    def test_handles_exception(self, mock_fetch):
        """异常时返回 ok=False"""
        mock_fetch.side_effect = Exception("Network error")

        result = get_wallet_portfolio(
            address="0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
            networks=["eth"],
        )

        assert result["ok"] is False
        assert "error" in result


class TestGetNativeBalance:
    """测试 get_native_balance 返回结构"""

    @patch("src.services.alchemy.service.post_json")
    def test_returns_correct_structure(self, mock_post):
        """返回正确的结构"""
        mock_post.return_value = {
            "data": {
                "0x802f71cBf691D4623374E8ec37e32e26d5f74d87": {
                    "native_balance": {"balance": "0xde0b6b3a7640000"}  # 1 ETH in hex
                }
            }
        }

        result = get_native_balance(
            address="0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
            network="eth",
        )

        assert result["ok"] is True
        assert result["address"] == "0x802f71cBf691D4623374E8ec37e32e26d5f74d87"
        assert result["network"] == "eth-mainnet"
        assert result["symbol"] == "ETH"
        assert result["balance"] == 1.0
        assert result["value_usd"] is None

    @patch("src.services.alchemy.service.post_json")
    def test_handles_missing_balance(self, mock_post):
        """余额不存在时返回 ok=False"""
        mock_post.return_value = {
            "data": {
                "0x802f71cBf691D4623374E8ec37e32e26d5f74d87": {
                    "native_balance": {}
                }
            }
        }

        result = get_native_balance(
            address="0x802f71cBf691D4623374E8ec37e32e26d5f74d87",
            network="eth",
        )

        assert result["ok"] is False
        assert result["balance"] == 0.0
        assert "error" in result


class TestCliModuleImport:
    """测试 cli 模块可以正常导入"""

    def test_cli_module_imports_without_error(self):
        """cli 模块可以正常导入"""
        from src.services.alchemy import cli
        assert hasattr(cli, "main")

    def test_service_module_imports_without_error(self):
        """service 模块可以正常导入"""
        from src.services.alchemy import service
        assert hasattr(service, "get_wallet_portfolio")
        assert hasattr(service, "get_native_balance")
