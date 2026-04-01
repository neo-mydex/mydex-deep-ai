from pydantic import BaseModel, Field, model_validator

from src.tools.user.decode_jwt import get_userid_and_expired_time


class ChatContext(BaseModel):
    jwt: str = Field(default="", description="已登录用户 token（Privy JWT）")
    other: str = Field(default="", description="其他重要上下文信息")

    # 核心身份字段（最小集）
    user_id: str = Field(default="guest", description="登录用户 id；游客固定为 guest")
    is_authenticated: bool = Field(default=False, description="是否为有效登录用户")
    jwt_error: str = Field(default="", description="jwt 解析错误信息")

    @model_validator(mode="after")
    def _resolve_identity(self) -> "ChatContext":
        self.user_id = "guest"
        self.jwt_error = ""
        self.is_authenticated = False

        jwt = self.jwt.strip()
        if not jwt:
            return self

        try:
            decoded = get_userid_and_expired_time(jwt=jwt)
            jwt_user_id = str(decoded.get("user_id", "") or "")
            jwt_is_expired = bool(decoded.get("is_expired", False))
            if jwt_user_id and not jwt_is_expired:
                self.user_id = jwt_user_id
                self.is_authenticated = True
        except Exception as exc:
            self.jwt_error = str(exc)

        return self

if __name__ == "__main__":
    jwt = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjVnRG9ZY3J4elFqanNkVVdUaGVQd2FVUlJHTnZtaGlraEl0SnNQdUFmVUEifQ.eyJzaWQiOiJjbW40MnBlMzIwMDBiMGJsY2xsbjMyNHlwIiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NzQzMjQwMTIsImF1ZCI6ImNtbHVidWxkaTAyZ3MwYmxhbWgwcWV3aXQiLCJzdWIiOiJkaWQ6cHJpdnk6Y21tc2w2dDI0MDIwMjBjbDJycGVyYzVtMSIsImV4cCI6MTc3NDQxMDQxMn0.ie-GWh5tlqLOA-3SD1gpJLvOkcg4oVlEJZqylBmYwy4O_FyEOUOheDtnHd-t7CBsy9VqMIYJRv94Do2qTGSvhg"
    cc = ChatContext(jwt=jwt, context="demo")
    print(cc)

    # uv run python -m src.config.context
