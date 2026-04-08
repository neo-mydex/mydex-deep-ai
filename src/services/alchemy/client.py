"""
Alchemy API 客户端配置
"""

import os
import json
from typing import Any
from dotenv import load_dotenv
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

load_dotenv()

ALCHEMY_API_KEY = os.environ.get("ALCHEMY_API_KEY")
ALCHEMY_DATA_API_BASE = f"https://api.g.alchemy.com/data/v1/{ALCHEMY_API_KEY}" if ALCHEMY_API_KEY else f"https://api.g.alchemy.com/data/v1/docs-demo"

DEFAULT_TIMEOUT_SECONDS = 20


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    发起 POST 请求

    参数:
        url: 请求 URL
        payload: 请求体

    返回:
        响应 JSON

    异常:
        RuntimeError: 请求失败时抛出
    """
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "mydex-deep-tool/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Alchemy HTTP {exc.code}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Alchemy request failed: {exc.reason}") from exc
