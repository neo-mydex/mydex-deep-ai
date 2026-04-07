"""
Privy 用户信息业务逻辑

调用后端 /ai-api/users/ 接口，根据 JWT 获取用户资料（含钱包地址）
"""

import base64
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from .client import AI_API_USERS_URL, get_json


class UserIdResponse(BaseModel):
    """user_get_userid 返回格式"""
    user_id: str
    expire_at_utc: str
    is_expired: bool


def user_get_userid_impl(jwt: str) -> dict:
    """解析 JWT 获取用户 ID 和过期时间（纯函数）"""
    payload = _decode_jwt_payload(jwt)

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("No valid user id found in JWT `sub` claim")

    exp = payload.get("exp")
    if exp is None:
        raise ValueError("No `exp` claim found in JWT payload")

    try:
        exp_timestamp = int(exp)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid `exp` claim: {exc}") from exc

    expire_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
    return UserIdResponse(
        user_id=user_id,
        expire_at_utc=expire_dt.isoformat(),
        is_expired=expire_dt <= datetime.now(timezone.utc),
    ).model_dump()


def get_user_profile(jwt: str) -> dict[str, Any]:
    """
    根据 JWT 获取用户资料

    同时解析 JWT 获取 user_id 和过期时间，
    并调用后端 API 获取钱包地址。

    参数:
        jwt: Privy JWT Bearer token

    返回结构:
    {
        "ok": bool,
        "user_id": str,
        "evm_address": str | None,
        "sol_address": str | None,
        "expire_at_utc": str | None,  # ISO format
        "is_expired": bool,
        "error": str | None,
    }
    """
    # 1. 解析 JWT 获取 user_id 和过期时间
    try:
        payload = _decode_jwt_payload(jwt)
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            return _error_result("No valid user id in JWT 'sub' claim")

        exp = payload.get("exp")
        expire_dt = None
        is_expired = False
        if exp is not None:
            try:
                exp_timestamp = int(exp)
                expire_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                is_expired = expire_dt <= datetime.now(timezone.utc)
            except (TypeError, ValueError):
                pass  # ignore invalid exp

    except Exception as e:
        return _error_result(f"JWT decode error: {e}")

    # 2. 调用后端 API 获取钱包地址
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {jwt}",
        "user-agent": "mydex-deep/1.0",
    }

    try:
        resp = get_json(AI_API_USERS_URL, headers)
        data = resp.get("data", {})
    except Exception as e:
        return _error_result(f"API request failed: {e}")

    return {
        "ok": True,
        "user_id": data.get("user_id", user_id),
        "evm_address": data.get("evm_address"),
        "sol_address": data.get("sol_address"),
        "expire_at_utc": expire_dt.isoformat() if expire_dt else None,
        "is_expired": is_expired,
        "error": None,
    }


def _decode_jwt_payload(jwt: str) -> dict[str, Any]:
    """解析 JWT payload（纯本地，不验证签名）"""
    parts = jwt.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")

    payload_b64 = parts[1]
    padding = 4 - (len(payload_b64) % 4)
    if padding != 4:
        payload_b64 += "=" * padding

    payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
    return json.loads(payload_bytes.decode("utf-8"))


def _error_result(message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "user_id": "",
        "evm_address": None,
        "sol_address": None,
        "expire_at_utc": None,
        "is_expired": False,
        "error": message,
    }
