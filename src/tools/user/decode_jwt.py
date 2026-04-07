"""Privy JWT helpers: extract user id and expiry from token payload."""

import base64
import json
from datetime import datetime, timezone
from typing import Any
from langchain_core.tools import tool
from pydantic import BaseModel


def _decode_jwt_payload(jwt: str) -> dict[str, Any]:
    parts = jwt.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format, expected 3 dot-separated parts")

    payload_b64 = parts[1]
    padding = 4 - (len(payload_b64) % 4)
    if padding != 4:
        payload_b64 += "=" * padding

    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to decode JWT payload: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Invalid JWT payload, expected a JSON object")
    return payload


class UserIdResponse(BaseModel):
    """get_userid 返回格式"""
    user_id: str


class JwtExpiredTimeResponse(BaseModel):
    """get_jwt_expired_time 返回格式"""
    expire_at_utc: datetime


class UserIdAndExpiredTimeResponse(BaseModel):
    """get_userid_and_expired_time 返回格式"""
    user_id: str
    expire_at_utc: str
    is_expired: bool


def get_userid_impl(jwt: str) -> dict:
    """获取用户 ID（纯函数，可直接测试）"""
    payload = _decode_jwt_payload(jwt)
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("No valid user id found in JWT `sub` claim")
    return UserIdResponse(user_id=user_id).model_dump()


def get_jwt_expired_time_impl(jwt: str) -> dict:
    """获取 JWT 过期时间（纯函数，可直接测试）"""
    payload = _decode_jwt_payload(jwt)
    exp = payload.get("exp")
    if exp is None:
        raise ValueError("No `exp` claim found in JWT payload")

    try:
        exp_timestamp = int(exp)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid `exp` claim, expected unix timestamp") from exc

    expire_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    return JwtExpiredTimeResponse(expire_at_utc=expire_dt).model_dump()


def get_userid_and_expired_time_impl(jwt: str) -> dict:
    """获取用户 ID 和过期时间（纯函数，可直接测试）"""
    payload = _decode_jwt_payload(jwt)

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("No valid user id found in JWT `sub` claim")

    exp = payload.get("exp")
    if exp is None:
        raise ValueError("No `exp` claim found in JWT payload")
    exp_timestamp = int(exp)
    expire_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

    return UserIdAndExpiredTimeResponse(
        user_id=user_id,
        expire_at_utc=expire_dt.isoformat(),
        is_expired=expire_dt <= datetime.now(timezone.utc),
    ).model_dump()


@tool
def get_userid(jwt: str) -> UserIdResponse:
    """Return user id from JWT `sub` claim."""
    return get_userid_impl(jwt)


@tool
def get_jwt_expired_time(jwt: str) -> JwtExpiredTimeResponse:
    """Return JWT expiration time in UTC from `exp` claim."""
    return get_jwt_expired_time_impl(jwt)


@tool
def get_userid_and_expired_time(jwt: str) -> UserIdAndExpiredTimeResponse:
    """Convenience helper for agent/tool orchestration."""
    return get_userid_and_expired_time_impl(jwt)


if __name__ == "__main__":
    from pprint import pprint
    jwt = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjVnRG9ZY3J4elFqanNkVVdUaGVQd2FVUlJHTnZtaGlraEl0SnNQdUFmVUEifQ.eyJzaWQiOiJjbW5mdHZnemcwMGVqMGNrc3ljbzk4cGM0IiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NzU1NDUyNDQsImF1ZCI6ImNtbHVidWxkaTAyZ3MwYmxhbWgwcWV3aXQiLCJzdWIiOiJkaWQ6cHJpdnk6Y21tc2w2dDI0MDIwMjBjbDJycGVyYzVtMSIsImV4cCI6MTc3NTYzMTY0NH0.b90pPcMwQHTjEOx6dZpOG6I7z_vX_2_TyaqmOUL-fCzM3i1Ukt7tKChxEf5bGSfMqfP8QmVSbtdhs9UUQyl1_Q"
    pprint(get_userid_impl(jwt))
    pprint(get_jwt_expired_time_impl(jwt))