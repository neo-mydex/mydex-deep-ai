"""
测试 check_can_close.py
"""

import pytest
from pydantic import ValidationError
from src.services.hyperliquid.service import check_can_close


class TestServiceCheckCanClose:
    """check_can_close service 层测试（service 层不做三选一校验）"""

    def test_no_position_returns_issue(self):
        """测试没有仓位时返回 issue"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="ETH",
            network="mainnet",
        )
        assert "issues" in result
        has_no_position_issue = any(
            issue.get("code") == "no_position" for issue in result["issues"]
        )
        assert has_no_position_issue

    def test_returns_flat_position_fields(self):
        """测试返回扁平化的仓位信息（无嵌套）"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="INVALID_COIN",
            network="mainnet",
        )
        assert "position_info" not in result
        assert "has_position" in result
        assert "position_side" in result

    def test_returns_checks_top_level(self):
        """返回结构无 checks 嵌套"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="INVALID_COIN",
            network="mainnet",
        )
        assert "checks" not in result

    def test_close_size_in_usdc_single_input(self):
        """只有 close_size_in_usdc 时，close_size 由 mark_price 换算得出"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_size_in_usdc=5000,
            network="mainnet",
        )
        assert result["close_size_in_usdc"] == 5000
        assert result["close_size"] is not None

    def test_close_ratio_single_input(self):
        """只有 close_ratio 时，基于持仓量计算"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_ratio=0.3,
            network="mainnet",
        )
        assert result["close_ratio"] == 0.3
        assert result["close_size"] is not None

    def test_close_size_clamped_goes_to_corrections(self):
        """平仓量超限裁剪进入 corrections 而非 issues"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_size=999,
            network="mainnet",
        )
        if not result["has_position"]:
            assert "裁剪为全平" not in str(result.get("corrections", []))
        else:
            correction_texts = result.get("corrections", [])
            has_clamped = any("裁剪为全平" in c for c in correction_texts)
            assert has_clamped

    def test_no_checks_nested(self):
        """返回结构无 checks 嵌套"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_size=0.01,
            network="mainnet",
        )
        assert "checks" not in result

    def test_flat_fields(self):
        """返回结构为顶层字段，无 position_info 嵌套"""
        result = check_can_close(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_size=0.01,
            network="mainnet",
        )
        assert "position_info" not in result
        assert "has_position" in result
        assert "position_side" in result
        assert "close_size" in result
        assert "close_size_in_usdc" in result
        assert "close_ratio" in result
        assert "corrections" in result


from src.tools.perp.check_can_close import perp_check_can_close_impl, CanCloseInput


class TestToolCheckCanClose:
    """perp_check_can_close tool 层测试"""

    def test_tool_accepts_close_size_in_usdc(self):
        """tool 层支持 close_size_in_usdc 参数，值在 matching_positions 里"""
        result = perp_check_can_close_impl(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_size_in_usdc=5000,
        )
        # 单币模式返回 1 条，空仓位时 matching_positions 为空但 ok=False
        assert result["ok"] is False
        assert result["matching_positions"] == []

    def test_tool_accepts_close_ratio(self):
        """tool 层支持 close_ratio 参数，值在 matching_positions 里"""
        result = perp_check_can_close_impl(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_ratio=0.5,
        )
        # 单币模式返回 1 条，空仓位时 matching_positions 为空但 ok=False
        assert result["ok"] is False
        assert result["matching_positions"] == []

    def test_response_has_matching_positions_structure(self):
        """响应结构为 ok + matching_positions + corrections + issues"""
        result = perp_check_can_close_impl(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_size=0.01,
        )
        assert "matching_positions" in result
        assert "corrections" in result
        assert "issues" in result
        assert "ok" in result

    def test_can_close_input_rejects_multiple_inputs(self):
        """CanCloseInput 拒绝多个输入同时指定"""
        with pytest.raises(ValidationError) as exc_info:
            CanCloseInput(
                address="0x0000000000000000000000000000000000000000",
                coin="BTC",
                close_size=0.5,
                close_size_in_usdc=1000,
            )
        assert "不可同时指定" in str(exc_info.value)

    def test_can_close_input_defaults_to_full_close(self):
        """CanCloseInput 不传任何参数时默认 close_ratio=1（全平）"""
        inp = CanCloseInput(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
        )
        assert inp.close_ratio == 1.0

    def test_can_close_input_clamps_invalid_ratio(self):
        """close_ratio 超出 (0, 1] 范围时自动纠正为 1.0，不报错"""
        # ratio > 1：自动纠正为 1.0
        inp = CanCloseInput(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_ratio=1.5,
        )
        assert inp.close_ratio == 1.0

        # ratio <= 0：也自动纠正为 1.0
        inp2 = CanCloseInput(
            address="0x0000000000000000000000000000000000000000",
            coin="BTC",
            close_ratio=-1,
        )
        assert inp2.close_ratio == 1.0
