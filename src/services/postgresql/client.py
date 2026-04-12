"""
Database 通用查询客户端（asyncpg）

提供 fetchrow / fetch / execute 三个基础方法，
业务 SQL 放在 service.py。
"""

import os
import asyncpg


# =============================================================================
# 全局连接池
# =============================================================================

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    """初始化连接池。环境变量缺失则抛 KeyError。"""
    global _pool
    if _pool is not None:
        return _pool

    host = os.environ["PG_HOST"]
    port = int(os.environ["PG_PORT"])
    database = os.environ["PG_DATABASE"]
    user = os.environ["PG_USER"]
    password = os.environ.get("PG_PASSWORD") or None

    _pool = await asyncpg.create_pool(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        min_size=1,
        max_size=10,
    )
    return _pool


async def close_pool() -> None:
    """关闭连接池。"""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    """获取连接池，未初始化则自动初始化。"""
    if _pool is None:
        await init_pool()
    return _pool  # type: ignore


# =============================================================================
# 通用查询方法
# =============================================================================

async def fetchrow(query: str, *args) -> dict | None:
    """查询单行，返回 dict 或 None。"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row is not None else None


async def fetch(query: str, *args) -> list[dict]:
    """查询多行，返回 list[dict]。"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(r) for r in rows]


async def execute(query: str, *args) -> str:
    """执行写操作（INSERT/UPDATE/DELETE），返回状态字符串。"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)
