"""
Privy API HTTP 客户端
"""

import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


MYDEX_API_BASE = os.environ["MYDEX_API_BASE"]
AI_API_USERS_URL = f"{MYDEX_API_BASE}/ai-api/users/"
DEFAULT_TIMEOUT_SECONDS = 15


def get_json(url: str, headers: dict[str, str]) -> dict:
    """
    发起 GET 请求

    参数:
        url: 请求 URL
        headers: 请求头

    返回:
        响应 JSON

    异常:
        RuntimeError: 请求失败时抛出
    """
    request = Request(
        url,
        headers=headers,
        method="GET",
    )
    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc
