"""
PostgreSQL 通用服务

提供 PostgreSQL 连接池和通用查询接口，业务函数放在 service.py。

模块结构:
- client.py: 连接池（init_pool / close_pool / fetchrow / fetch / execute）
- service.py: 业务函数（get_processed_content_by_id, get_user_info_by_id）

使用方式:
    from src.services.postgresql import get_processed_content_by_id, get_user_info_by_id
    result = await get_processed_content_by_id("social_2041546291302306032")
    result = await get_user_info_by_id("user123")
"""

from dotenv import load_dotenv

load_dotenv()

from .service import get_processed_content_by_id, get_user_info_by_id

__all__ = ["get_processed_content_by_id", "get_user_info_by_id"]
