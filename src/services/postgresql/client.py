"""
Database 通用查询客户端（psycopg2）

提供 fetchrow / fetch / execute 三个基础方法，
业务 SQL 放在 service.py。
psycopg2 使用 %s 占位符（非 $1）。
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor


# =============================================================================
# 全局连接
# =============================================================================

_conn: psycopg2.extensions.connection | None = None


def _get_conn() -> psycopg2.extensions.connection:
    """获取数据库连接，未初始化则创建。"""
    global _conn
    if _conn is None:
        host = os.environ["PG_HOST"]
        port = int(os.environ["PG_PORT"])
        database = os.environ["PG_DATABASE"]
        user = os.environ["PG_USER"]
        password = os.environ.get("PG_PASSWORD") or None

        _conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
    return _conn


def close_pool() -> None:
    """关闭连接。"""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


# =============================================================================
# 通用查询方法
# =============================================================================

def fetchrow(query: str, *args) -> dict | None:
    """查询单行，返回 dict 或 None。"""
    conn = _get_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, args)
        row = cur.fetchone()
        return dict(row) if row is not None else None


def fetch(query: str, *args) -> list[dict]:
    """查询多行，返回 list[dict]。"""
    conn = _get_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, args)
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def execute(query: str, *args) -> str:
    """执行写操作（INSERT/UPDATE/DELETE），返回状态字符串。"""
    conn = _get_conn()
    with conn.cursor() as cur:
        return cur.execute(query, args)
