"""获取用户钱包地址（从 context 获取，无需 JWT）。"""

from langchain.tools import ToolRuntime
from langchain_core.tools import tool
from pydantic import BaseModel


class UserIdResponse(BaseModel):
    """user_get_userid 返回格式"""
    user_id: str
    expire_at_utc: str
    is_expired: bool


class WalletAddressResponse(BaseModel):
    """user_get_wallet_address 返回格式"""
    ok: bool
    evm_address: str | None = None
    sol_address: str | None = None
    error: str | None = None


def user_get_wallet_address_impl(jwt: str) -> dict:
    """获取钱包地址（调用后端 API），用于测试。"""
    from src.services.privy import get_user_profile as privy_get_user_profile
    return privy_get_user_profile(jwt)


@tool
def user_get_wallet_address(runtime: ToolRuntime) -> WalletAddressResponse:
    """获取用户钱包地址（EVM 和 Solana）。

    直接从 context 获取，无需传入 JWT。
    """
    ctx = runtime.context
    if not ctx:
        return WalletAddressResponse(
            ok=False,
            error="无法获取 context",
        ).model_dump()
    return WalletAddressResponse(
        ok=True,
        evm_address=ctx.evm_address or None,
        sol_address=ctx.sol_address or None,
    ).model_dump()


if __name__ == "__main__":
    from rich import print
    jwt="eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjVnRG9ZY3J4elFqanNkVVdUaGVQd2FVUlJHTnZtaGlraEl0SnNQdUFmVUEifQ.eyJzaWQiOiJjbW5mdHZnemcwMGVqMGNrc3ljbzk4cGM0IiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NzU2MzE2MzQsImF1ZCI6ImNtbHVidWxkaTAyZ3MwYmxhbWgwcWV3aXQiLCJzdWIiOiJkaWQ6cHJpdnk6Y21tc2w2dDI0MDIwMjBjbDJycGVyYzVtMSIsImV4cCI6MTc3NTcxODAzNH0.PLpAp7mZQtWKCwOHb-NpsYv-CjYQWtYeagN0svrkKt0zAmBxGLyjtNGovoR6BTdJafAkBJD5ND9BRimXTjytZA"
    print(user_get_wallet_address_impl(jwt))
