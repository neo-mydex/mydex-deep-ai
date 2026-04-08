"""
CoinGecko HTTP 客户端

处理 API 请求，支持 Pro API Key 和降级方案
"""

import os
import json
from typing import Any
from dotenv import load_dotenv
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

load_dotenv()

# API 配置
COINGECKO_PRO_API_KEY = os.environ.get("COINGECKO_PRO_API_KEY")
COINGECKO_API_BASE = (
    "https://pro-api.coingecko.com/api/v3"
    if COINGECKO_PRO_API_KEY
    else "https://api.coingecko.com/api/v3"
)
COINGECKO_ONCHAIN_API_BASE = COINGECKO_API_BASE

DEFAULT_TIMEOUT = 15.0


def fetch_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """
    发起 CoinGecko API 请求

    参数:
        url: 请求 URL
        timeout: 超时时间

    返回:
        API 响应数据

    异常:
        RuntimeError: 请求失败时抛出
    """
    headers = {
        "accept": "application/json",
        "user-agent": "mydex-deep-tool/1.0",
    }
    if COINGECKO_PRO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_PRO_API_KEY

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"CoinGecko HTTP {exc.code}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"CoinGecko request failed: {exc.reason}") from exc


def build_url(endpoint: str, params: dict[str, Any] | None = None) -> str:
    """
    构建 API URL

    参数:
        endpoint: API 端点
        params: 查询参数

    返回:
        完整的 URL
    """
    from urllib.parse import quote

    url = f"{COINGECKO_API_BASE}{endpoint}"
    if params:
        query_parts = []
        for key, value in params.items():
            if value is not None:
                query_parts.append(f"{quote(str(key))}={quote(str(value))}")
        if query_parts:
            url += "?" + "&".join(query_parts)
    return url
