import os
from pydantic import BaseModel, Field
from src.services.privy import get_user_profile, user_get_userid_impl


class ChatContext(BaseModel):
    user_id: str = Field(default="guest", description="登录用户 id；游客固定为 guest")
    is_expired: bool = Field(default=False, description="JWT 是否过期")
    evm_address: str = Field(default="", description="用户 EVM 链钱包地址（ETH、Base、BSC、ARB、Polygon 等）")
    sol_address: str = Field(default="", description="用户 Solana 钱包地址")

    @classmethod
    def from_jwt(cls, jwt: str) -> "ChatContext":
        """从 JWT 派生 context，不在模型中保留 JWT 原文。"""
        token = (jwt or "").strip()
        if not token:
            return cls()

        try:
            decoded = user_get_userid_impl(jwt=token)
            user_id = str(decoded.get("user_id", "") or "")
            is_expired = bool(decoded.get("is_expired", False))
            if not user_id:
                return cls()
            if is_expired:
                return cls(user_id=user_id, is_expired=True)

            evm_address = ""
            sol_address = ""
            try:
                profile = get_user_profile(token)
                if profile.get("ok"):
                    evm_address = str(profile.get("evm_address") or "")
                    sol_address = str(profile.get("sol_address") or "")
            except Exception:
                # 获取钱包地址失败时保持身份信息
                pass

            return cls(
                user_id=user_id,
                is_expired=False,
                evm_address=evm_address,
                sol_address=sol_address,
            )
        except Exception:
            return cls()


if __name__ == "__main__":
    from rich import print
    
    c = ChatContext()
    print("default: ")
    print(c.model_dump())

    jwt = os.environ.get("JWT", "")
    if jwt:
        print("\nfrom_jwt:")
        print(ChatContext.from_jwt(jwt).model_dump())
    else:
        print("\nJWT env not set; skip from_jwt demo.")
