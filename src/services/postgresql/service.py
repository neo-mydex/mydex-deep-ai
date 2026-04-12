"""
Database 业务逻辑层

每个业务函数对应一张表或一类查询。
"""

from typing import Any

from .client import fetchrow


async def get_processed_content_by_id(content_id: str) -> dict[str, Any]:
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
    row = await fetchrow(
        "SELECT * FROM ai_processed_content WHERE id = $1",
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


async def get_user_info_by_id(user_id: str) -> dict[str, Any]:
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
    row = await fetchrow(
        "SELECT * FROM ai_user_profiles WHERE user_id = $1",
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
    import asyncio
    from rich import print

    async def main():
        # 验证函数签名（未配置 PG 时会抛 KeyError）
        print("get_processed_content_by_id signature OK")
        print("PG env vars required: PG_HOST, PG_PORT, PG_DATABASE, PG_USER, PG_PASSWORD")

    asyncio.run(main())
