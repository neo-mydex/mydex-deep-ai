"""解析 Privy JWT token，提取用户信息"""
import json
import os
import sys
from argparse import ArgumentParser
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

PRIVY_APP_ID = os.getenv("PRIVY_APP_ID")
JWKS_URL = f"https://auth.privy.io/api/v1/apps/{PRIVY_APP_ID}/jwks.json"
DEFAULT_TIMEOUT_SECONDS = 20

# 缓存 JWKS
_JWKS_CACHE: dict[str, dict] = {}


class PrivyTokenInput(BaseModel):
    token: str


class PrivyUserData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="userId")
    email: str | None = None
    wallet_address: str | None = Field(default=None, alias="walletAddress")
    google_subject: str | None = Field(default=None, alias="googleSubject")
    discord_id: str | None = Field(default=None, alias="discordId")
    twitter_id: str | None = Field(default=None, alias="twitterId")


class PrivyTokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    user_id: str | None = Field(default=None, alias="userId")
    email: str | None = None
    wallet_address: str | None = Field(default=None, alias="walletAddress")
    expire: str | None = None
    raw_payload: dict | None = Field(default=None, alias="rawPayload")
    error: str | None = None


def parse_args(argv: list[str]) -> PrivyTokenInput:
    parser = ArgumentParser(description="解析 Privy JWT token，提取用户信息")
    parser.add_argument(
        "-t",
        "--token",
        dest="token",
        required=True,
        help="Privy JWT token",
    )
    args = parser.parse_args(argv)
    return PrivyTokenInput(token=args.token.strip())


def fetch_jwks() -> dict:
    """获取 JWKS 公钥"""
    if _JWKS_CACHE:
        return _JWKS_CACHE

    request = Request(
        JWKS_URL,
        headers={
            "accept": "application/json",
            "user-agent": "mydex-deep-cli-privy/1.0",
        },
    )
    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
            for key in data.get("keys", []):
                if key.get("kid"):
                    _JWKS_CACHE[key["kid"]] = key
            return _JWKS_CACHE
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Privy JWKS HTTP {exc.code}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Privy JWKS request failed: {exc.reason}") from exc


def decode_jwt_payload(token: str) -> dict:
    """解码 JWT payload（不验证签名）"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        # 解码 payload (第二部分)
        payload_b64 = parts[1]
        # 添加 padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        import base64
        payload_json = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_json)
    except Exception as e:
        raise ValueError(f"Failed to decode JWT: {e}")


def extract_user_info(payload: dict) -> PrivyTokenResponse:
    """从 JWT payload 提取用户信息"""
    user_id = payload.get("sub")
    if not user_id:
        return PrivyTokenResponse(
            success=False,
            error="No user ID (sub) found in token",
        )

    # Privy token 可能包含的用户信息
    email = None
    wallet_address = None

    # 检查 linked_accounts 或其他字段
    linked_accounts = payload.get("linked_accounts", [])
    for account in linked_accounts:
        account_type = account.get("type")
        if account_type == "email":
            email = account.get("email")
        elif account_type == "wallet":
            wallet_address = account.get("address")

    # 也可以从顶层字段获取
    if not email:
        email = payload.get("email")
    if not wallet_address:
        wallet_address = payload.get("wallet_address")

    # 计算过期时间
    expire_str = None
    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        try:
            expire_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            expire_str = expire_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (TypeError, ValueError):
            pass

    return PrivyTokenResponse(
        success=True,
        userId=user_id,
        email=email,
        walletAddress=wallet_address,
        expire=expire_str,
        rawPayload=payload,
    )


def verify_token(token: str) -> PrivyTokenResponse:
    """验证并解析 Privy token"""
    if not PRIVY_APP_ID:
        return PrivyTokenResponse(
            success=False,
            error="PRIVY_APP_ID not set in environment",
        )

    try:
        # 获取 JWKS
        jwks = fetch_jwks()

        # 解码 header 获取 kid
        import base64
        parts = token.split(".")
        header_b64 = parts[0]
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        header = json.loads(base64.urlsafe_b64decode(header_b64))

        kid = header.get("kid")
        if not kid:
            return PrivyTokenResponse(
                success=False,
                error="No KID found in token header",
            )

        # 找到对应的公钥
        jwk = jwks.get(kid)
        if not jwk:
            return PrivyTokenResponse(
                success=False,
                error=f"No matching key found for KID: {kid}",
            )

        # 解码 payload（简化版：不验证签名，仅提取信息）
        payload = decode_jwt_payload(token)

        # 验证 audience 和 issuer
        if payload.get("aud") != PRIVY_APP_ID:
            return PrivyTokenResponse(
                success=False,
                error=f"Invalid audience: expected {PRIVY_APP_ID}",
            )

        issuer = payload.get("iss", "")
        if "privy.io" not in issuer:
            return PrivyTokenResponse(
                success=False,
                error=f"Invalid issuer: {issuer}",
            )

        return extract_user_info(payload)

    except Exception as e:
        return PrivyTokenResponse(
            success=False,
            error=str(e),
        )


def main() -> int:
    token_input = parse_args(sys.argv[1:])
    result = verify_token(token_input.token)
    print(result.model_dump_json(by_alias=True, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
