"""
测试 ChatContext 的身份解析逻辑
"""

from src.config.context import ChatContext


def test_guest_context_defaults():
    ctx = ChatContext()
    assert ctx.is_authenticated is False
    assert ctx.user_id == "guest"


def test_invalid_jwt_fallback_guest():
    ctx = ChatContext(jwt="invalid.jwt")
    assert ctx.is_authenticated is False
    assert ctx.user_id == "guest"
    assert ctx.jwt_error != ""
