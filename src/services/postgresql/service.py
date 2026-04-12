"""
Database 业务逻辑层

每个业务函数对应一张表或一类查询。
"""

from typing import Any

from .client import fetchrow, fetch


def get_processed_content_by_id(content_id: str) -> dict[str, Any]:
    """按 ID 查询 AI 处理后的内容（ai_processed_content 表）。

    参数:
        content_id: 内容 ID

    Returns:
        {
            "ok": bool,
            "data": dict | None,
            "error": str | None,
        }
    """
    row = fetchrow(
        "SELECT * FROM ai_processed_content WHERE id = %s",
        content_id,
    )
    if row is None:
        return {
            "ok": False,
            "data": None,
            "error": f"ai_processed_content {content_id} not found",
        }
    return {
        "ok": True,
        "data": dict(row),
        "error": None,
    }


def get_processed_content_by_coin(
    coin: str,
    limit: int = 10,
) -> dict[str, Any]:
    """按 coin 查询相关内容（ai_processed_content 表）。

    suggested_tokens JSONB 数组中匹配 symbol 或 name，按 published_at 倒序。

    参数:
        coin: 代币名称或符号（如 BTC、BTC.omft.near）
        limit: 最大返回条数，默认 10

    Returns:
        {
            "ok": bool,
            "data": list[dict] | None,
            "error": str | None,
        }
    """
    rows = fetch(
        """
        SELECT * FROM ai_processed_content
        WHERE EXISTS (
            SELECT 1 FROM jsonb_array_elements(suggested_tokens) AS token
            WHERE token->>'symbol' = %s OR token->>'name' = %s
        )
        ORDER BY published_at DESC
        LIMIT %s
        """,
        coin.upper(),
        coin.upper(),
        limit,
    )
    return {
        "ok": True,
        "data": [dict(r) for r in rows],
        "error": None,
    }


def get_hottest_daily_contents(coin: str | None = None, limit: int = 10) -> dict[str, Any]:
    """查询 24 小时内的热门内容（ai_processed_content 表）。

    按 hotness_score 倒序返回。若指定 coin，则在 suggested_tokens 中匹配。

    参数:
        coin: 可选，代币名称或符号（如 BTC）
        limit: 最大返回条数，默认 10

    Returns:
        {
            "ok": bool,
            "data": list[dict] | None,
            "error": str | None,
        }
    """
    if coin:
        rows = fetch(
            """
            SELECT * FROM ai_processed_content
            WHERE published_at >= now() - INTERVAL '24 hours'
              AND EXISTS (
                  SELECT 1 FROM jsonb_array_elements(suggested_tokens) AS token
                  WHERE token->>'symbol' = %s OR token->>'name' = %s
              )
            ORDER BY hotness_score DESC
            LIMIT %s
            """,
            coin.upper(),
            coin.upper(),
            limit,
        )
    else:
        rows = fetch(
            """
            SELECT * FROM ai_processed_content
            WHERE published_at >= now() - INTERVAL '24 hours'
            ORDER BY hotness_score DESC
            LIMIT %s
            """,
            limit,
        )
    return {
        "ok": True,
        "data": [dict(r) for r in rows],
        "error": None,
    }


def get_user_info_by_id(user_id: str) -> dict[str, Any]:
    """按 ID 查询用户画像（ai_user_profiles 表）。

    参数:
        user_id: 用户 ID

    Returns:
        {
            "ok": bool,
            "data": dict | None,
            "error": str | None,
        }
    """
    row = fetchrow(
        "SELECT * FROM ai_user_profiles WHERE user_id = %s",
        user_id,
    )
    if row is None:
        return {
            "ok": False,
            "data": None,
            "error": f"ai_user_profiles {user_id} not found",
        }
    return {
        "ok": True,
        "data": dict(row),
        "error": None,
    }


if __name__ == "__main__":
    from rich import print
    print("get_processed_content_by_id signature OK")
    print("PG env vars required: PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD")
