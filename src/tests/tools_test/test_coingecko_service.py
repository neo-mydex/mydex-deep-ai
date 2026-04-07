"""
测试 coingecko service 层 (cli.py 中的业务函数)

直接测试 service 层的纯业务逻辑函数，使用 mock 隔离网络依赖。
"""

import pytest
from unittest.mock import patch, MagicMock

from src.services.coingecko.cli import (
    get_coin_price,
    get_coin_info,
    search_coins,
    get_trending_coins,
)


class TestGetCoinPrice:
    """get_coin_price 测试"""

    @patch("src.services.coingecko.cli.build_url")
    @patch("src.services.coingecko.cli.fetch_json")
    @patch("src.services.coingecko.cli._resolve_coin_input")
    def test_returns_correct_structure(self, mock_resolve, mock_fetch_json, mock_build_url):
        """测试返回结构包含必要字段"""
        mock_resolve.return_value = {
            "coin_id": "bitcoin",
            "input_type": "symbol",
            "network": None,
            "original": "BTC",
        }
        mock_build_url.return_value = "https://api.coingecko.com/v3/simple/price"
        mock_fetch_json.return_value = {
            "bitcoin": {"usd": 50000.0, "usd_24h_change": 2.5}
        }

        result = get_coin_price(coin="BTC", vs="usd")

        assert "ok" in result
        assert "coin" in result
        assert "coin_id" in result
        assert "vs" in result
        assert "price" in result
        assert "change_24h" in result
        assert "source" in result
        assert result["ok"] is True
        assert result["coin"] == "BTC"
        assert result["coin_id"] == "bitcoin"
        assert result["vs"] == "usd"
        assert result["price"] == 50000.0
        assert result["change_24h"] == 2.5
        assert result["source"] == "coingecko"

    @patch("src.services.coingecko.cli._resolve_coin_input")
    def test_returns_false_for_unknown_coin(self, mock_resolve):
        """测试不存在的币返回 ok=False"""
        mock_resolve.return_value = {
            "coin_id": None,
            "input_type": None,
            "network": None,
            "original": "INVALID",
        }

        result = get_coin_price(coin="INVALID", vs="usd")

        assert result["ok"] is False
        assert result["coin"] == "INVALID"
        assert result["coin_id"] is None
        assert result["price"] is None
        assert "error" in result


class TestGetCoinInfo:
    """get_coin_info 测试"""

    @patch("src.services.coingecko.cli.build_url")
    @patch("src.services.coingecko.cli.fetch_json")
    @patch("src.services.coingecko.cli._resolve_coin_input")
    def test_returns_correct_structure(self, mock_resolve, mock_fetch_json, mock_build_url):
        """测试返回结构包含必要字段"""
        mock_resolve.return_value = {
            "coin_id": "bitcoin",
            "input_type": "symbol",
            "network": None,
            "original": "BTC",
        }
        mock_build_url.return_value = "https://api.coingecko.com/v3/coins/bitcoin"
        mock_fetch_json.return_value = {
            "id": "bitcoin",
            "name": "Bitcoin",
            "symbol": "btc",
            "market_cap_rank": 1,
            "market_data": {
                "current_price": {"usd": 50000.0},
                "price_change_percentage_24h": 2.5,
                "market_cap": {"usd": 1000000000000},
            },
            "platforms": {"ethereum": "0x123"},
        }

        result = get_coin_info(coin="BTC", vs="usd")

        assert "ok" in result
        assert "coin" in result
        assert "coin_id" in result
        assert "name" in result
        assert "symbol" in result
        assert "price" in result
        assert "change_24h" in result
        assert "market_cap" in result
        assert "rank" in result
        assert "contract_address" in result
        assert "networks" in result
        assert "source" in result
        assert result["ok"] is True
        assert result["coin"] == "BTC"
        assert result["coin_id"] == "bitcoin"
        assert result["name"] == "Bitcoin"
        assert result["symbol"] == "BTC"
        assert result["price"] == 50000.0
        assert result["rank"] == 1

    @patch("src.services.coingecko.cli._resolve_coin_input")
    def test_returns_false_for_unknown_coin(self, mock_resolve):
        """测试不存在的币返回 ok=False"""
        mock_resolve.return_value = {
            "coin_id": None,
            "input_type": None,
            "network": None,
            "original": "INVALID",
        }

        result = get_coin_info(coin="INVALID", vs="usd")

        assert result["ok"] is False
        assert result["coin"] == "INVALID"
        assert result["coin_id"] is None
        assert result["name"] is None
        assert "error" in result


class TestSearchCoins:
    """search_coins 测试"""

    @patch("src.services.coingecko.cli.build_url")
    @patch("src.services.coingecko.cli.fetch_json")
    @patch("src.services.coingecko.cli.is_contract_address")
    def test_returns_correct_structure(self, mock_is_contract, mock_fetch_json, mock_build_url):
        """测试返回结构包含必要字段"""
        mock_is_contract.return_value = False
        mock_build_url.return_value = "https://api.coingecko.com/v3/search"
        mock_fetch_json.return_value = {
            "coins": [
                {
                    "id": "bitcoin",
                    "name": "Bitcoin",
                    "symbol": "btc",
                    "market_cap_rank": 1,
                },
                {
                    "id": "ethereum",
                    "name": "Ethereum",
                    "symbol": "eth",
                    "market_cap_rank": 2,
                },
            ]
        }

        result = search_coins(query="bitcoin", limit=5)

        assert "ok" in result
        assert "query" in result
        assert "candidates" in result
        assert "source" in result
        assert result["ok"] is True
        assert result["query"] == "bitcoin"
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["id"] == "bitcoin"
        assert result["candidates"][0]["symbol"] == "BTC"

    @patch("src.services.coingecko.cli.is_contract_address")
    def test_rejects_contract_address(self, mock_is_contract):
        """测试拒绝合约地址查询"""
        mock_is_contract.return_value = True

        result = search_coins(query="0x1234567890abcdef")

        assert result["ok"] is False
        assert result["candidates"] == []
        assert "error" in result
        assert "合约地址" in result["error"]


class TestGetTrendingCoins:
    """get_trending_coins 测试"""

    @patch("src.services.coingecko.cli.build_url")
    @patch("src.services.coingecko.cli.fetch_json")
    def test_returns_correct_structure(self, mock_fetch_json, mock_build_url):
        """测试返回结构包含必要字段"""
        mock_build_url.return_value = "https://api.coingecko.com/v3/search/trending"
        mock_fetch_json.return_value = {
            "coins": [
                {"item": {"id": "bitcoin", "name": "Bitcoin", "symbol": "btc"}},
                {"item": {"id": "ethereum", "name": "Ethereum", "symbol": "eth"}},
            ]
        }

        result = get_trending_coins()

        assert "ok" in result
        assert "coins" in result
        assert "source" in result
        assert result["ok"] is True
        assert len(result["coins"]) == 2
        assert result["source"] == "coingecko"

    @patch("src.services.coingecko.cli.build_url")
    @patch("src.services.coingecko.cli.fetch_json")
    def test_handles_api_error(self, mock_fetch_json, mock_build_url):
        """测试处理 API 错误"""
        mock_build_url.return_value = "https://api.coingecko.com/v3/search/trending"
        mock_fetch_json.side_effect = Exception("API Error")

        result = get_trending_coins()

        assert result["ok"] is False
        assert result["coins"] == []
        assert "error" in result


class TestCliMainImport:
    """测试 CLI 入口可以被导入"""

    def test_cli_main_can_be_imported(self):
        """验证 __main__ 模块可以被正常导入"""
        from src.services.coingecko import __main__

        assert hasattr(__main__, "main")
        assert callable(__main__.main)
