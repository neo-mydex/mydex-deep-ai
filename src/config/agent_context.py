import os
from datetime import datetime, timezone
from enum import Enum                              # 1. 枚举类型
from typing import Literal

from pydantic import BaseModel, Field             # 2. Pydantic 数据校验
from src.services.privy import decode_jwt_payload, resolve_wallet_addresses  # 3. JWT 解析服务


# 4. 用户角色枚举
class UserRole(str, Enum):
    """用户角色枚举。"""
    GUEST = "guest"    # 游客：受限工具集
    USER = "user"      # 普通用户：全量工具集
    ADMIN = "admin"    # 管理员：全量工具集


# 5. 交互模式枚举
class InteractMode(str, Enum):
    """交互模式枚举。"""
    FRONTEND = "frontend"   # 前端 confirm card
    WEBAPI = "webapi"      # API 摘要
    CLI = "cli"            # 终端富文本


class ChatContext(BaseModel):
    # 1. 交互模式
    interact_mode: InteractMode = Field(
        default=InteractMode.FRONTEND,
        description="交互模式：frontend（前端 confirm card）、webapi（API 摘要）、cli（终端富文本）",
    )
    # 2. 用户 ID
    user_id: str = Field(default="guest", description="登录用户 id；游客固定为 guest")
    # 3. 是否过期
    is_expired: bool = Field(default=False, description="JWT 是否过期")
    # 4. 用户角色
    role: UserRole = Field(
        default=UserRole.GUEST,
        description="用户角色：guest（游客）、user（普通用户）、admin（管理员）",
    )
    # 5. EVM 钱包地址
    evm_address: str = Field(default="", description="用户 EVM 链钱包地址（ETH、Base、BSC、ARB、Polygon 等）")
    # 6. Solana 钱包地址
    sol_address: str = Field(default="", description="用户 Solana 钱包地址")

    @classmethod
    def from_jwt(cls, jwt: str) -> "ChatContext":
        """从 JWT 派生 context。"""
        # 第一步：JWT 为空 → 游客身份，所有字段保持默认值
        token = (jwt or "").strip()
        if not token:
            return cls()

        # 第二步：解析 JWT payload
        payload = decode_jwt_payload(token)

        # 第三步：从 payload 取 user_id；无 user_id → 游客身份
        user_id = str(payload.get("sub") or "")
        if not user_id:
            return cls()

        # 第四步：检查 token 是否过期；已过期 → 保留身份，降级为游客
        exp = payload.get("exp")
        is_expired = False
        if exp is not None:
            try:
                exp_dt = datetime.fromtimestamp(int(exp), tz=timezone.utc)
                is_expired = exp_dt <= datetime.now(timezone.utc)
            except Exception:
                pass
        if is_expired:
            return cls(user_id=user_id, is_expired=True)

        # 第五步：JWT 有效 → 解析角色（非白名单 → 默认 user）
        role_raw = payload.get("role", "user")
        role = UserRole(role_raw) if role_raw in UserRole._value2member_map_ else UserRole.USER

        # 第六步：解析钱包地址
        addresses = resolve_wallet_addresses(token)
        return cls(
            user_id=user_id,
            is_expired=False,
            role=role,
            evm_address=addresses["evm_address"],
            sol_address=addresses["sol_address"],
        )


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
