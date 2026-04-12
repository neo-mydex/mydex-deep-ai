"""
测试 confirm_set_tpsl.py
"""

import pytest
from pydantic import ValidationError

from src.tools.action.confirm_perp_set_tpsl import confirm_perp_set_tpsl_impl, ConfirmSetTpslInput


def test_reject_non_positive_position_size():
    with pytest.raises(ValueError, match="position_size"):
        confirm_perp_set_tpsl_impl(coin="BTC", position_size=0, tp_price=80000)


def test_reject_non_positive_tp_price():
    with pytest.raises(ValueError, match="tp_price"):
        confirm_perp_set_tpsl_impl(coin="BTC", position_size=0.2, tp_price=0)


def test_reject_non_positive_sl_price():
    with pytest.raises(ValueError, match="sl_price"):
        confirm_perp_set_tpsl_impl(coin="BTC", position_size=0.2, sl_price=-1)


def test_reject_out_of_range_tp_ratio():
    with pytest.raises(ValueError, match="tp_ratio"):
        confirm_perp_set_tpsl_impl(coin="BTC", position_size=0.2, tp_ratio=1.2)


def test_reject_out_of_range_sl_ratio():
    with pytest.raises(ValueError, match="sl_ratio"):
        confirm_perp_set_tpsl_impl(coin="BTC", position_size=0.2, sl_ratio=0)


def test_reject_negative_existing_oid():
    with pytest.raises(ValueError, match="existing_tp_oid"):
        confirm_perp_set_tpsl_impl(
            coin="BTC",
            position_size=0.2,
            tp_price=80000,
            existing_tp_oid=-1,
        )


def test_args_schema_rejects_missing_both_tp_and_sl():
    with pytest.raises(ValidationError):
        ConfirmSetTpslInput(
            coin="BTC",
            position_size=0.2,
        )
