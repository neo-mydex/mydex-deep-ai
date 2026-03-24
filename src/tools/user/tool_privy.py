"""Privy JWT helpers: extract user id and expiry from token payload."""

import base64
import json
from datetime import datetime, timezone
from typing import Any


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


def get_userid(jwt: str) -> str:
    """Return user id from JWT `sub` claim."""
    payload = _decode_jwt_payload(jwt)
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("No valid user id found in JWT `sub` claim")
    return user_id


def get_jwt_expired_time(jwt: str) -> datetime:
    """Return JWT expiration time in UTC from `exp` claim."""
    payload = _decode_jwt_payload(jwt)
    exp = payload.get("exp")
    if exp is None:
        raise ValueError("No `exp` claim found in JWT payload")

    try:
        exp_timestamp = int(exp)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid `exp` claim, expected unix timestamp") from exc

    return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)


def get_userid_and_expired_time(jwt: str) -> dict[str, Any]:
    """Convenience helper for agent/tool orchestration."""
    expire_dt = get_jwt_expired_time(jwt)
    return {
        "user_id": get_userid(jwt),
        "expire_at_utc": expire_dt.isoformat(),
        "is_expired": expire_dt <= datetime.now(timezone.utc),
    }

if __name__ == "__main__":
    jwt = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjVnRG9ZY3J4elFqanNkVVdUaGVQd2FVUlJHTnZtaGlraEl0SnNQdUFmVUEifQ.eyJzaWQiOiJjbW40MnBlMzIwMDBiMGJsY2xsbjMyNHlwIiwiaXNzIjoicHJpdnkuaW8iLCJpYXQiOjE3NzQzMjQwMTIsImF1ZCI6ImNtbHVidWxkaTAyZ3MwYmxhbWgwcWV3aXQiLCJzdWIiOiJkaWQ6cHJpdnk6Y21tc2w2dDI0MDIwMjBjbDJycGVyYzVtMSIsImV4cCI6MTc3NDQxMDQxMn0.ie-GWh5tlqLOA-3SD1gpJLvOkcg4oVlEJZqylBmYwy4O_FyEOUOheDtnHd-t7CBsy9VqMIYJRv94Do2qTGSvhg"
    print(get_userid_and_expired_time(jwt=jwt)) # {'user_id': 'did:privy:cmmsl6t2402020cl2rperc5m1', 'expire_at_utc': '2026-03-25T03:46:52+00:00', 'is_expired': False}