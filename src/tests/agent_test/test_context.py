"""
测试 ChatContext 的身份解析逻辑
"""

from src.config.agent_context import ChatContext


def test_guest_context_defaults():
    ctx = ChatContext()
    assert ctx.user_id == "guest"
    assert ctx.is_expired is False
    assert ctx.evm_address == ""
    assert ctx.sol_address == ""


def test_custom_context_fields():
    ctx = ChatContext(
        user_id="did:privy:abc",
        is_expired=True,
        evm_address="0x123",
        sol_address="So11111111111111111111111111111111111111112",
    )
    assert ctx.user_id == "did:privy:abc"
    assert ctx.is_expired is True
    assert ctx.evm_address == "0x123"
    assert ctx.sol_address == "So11111111111111111111111111111111111111112"


def test_from_jwt_invalid_fallback_guest():
    ctx = ChatContext.from_jwt("invalid.jwt")
    assert ctx.user_id == "guest"
    assert ctx.is_expired is False
    assert ctx.evm_address == ""
    assert ctx.sol_address == ""
