# -*- coding: utf-8 -*-
import logging
from typing import AsyncGenerator, Optional

from models.public import Tenant

from fastapi import Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from core.config import settings
from core.db import AsyncSessionFactory

logger = logging.getLogger(__name__)


async def get_tenant_info(request: Request) -> Optional[Tenant]:
    """获取存储在请求状态中的租户信息对象 (如果存在)"""
    return getattr(request.state, "tenant_info", None)


# --- 用于租户 API 的依赖项 ---
async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖项，用于获取设置了正确 search_path 的数据库会话。"""
    tenant_schema = getattr(request.state, "tenant_schema", None)
    if not tenant_schema:
        # 如果中间件未能设置 schema（例如访问了公共路径或出错）
        # 根据策略决定是抛出错误还是提供一个默认连接 (可能只连 public)
        # 这里我们选择抛出错误，因为预期访问租户数据的API必须有租户上下文
        logger.error("Tenant schema not found in request state.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine tenant context for this request."
        )

    session: AsyncSession = AsyncSessionFactory()
    try:
        # --- 关键: 设置当前会话/事务的 search_path ---
        # 使用 f-string 可能有注入风险，但 schema_name 来自我们数据库且经过验证，风险较低
        # 更好的做法是使用参数绑定，但 SET search_path 不直接支持
        # 确保 schema_name 是合法的标识符（例如，只允许字母、数字、下划线）
        # 这里的 schema_name 是从数据库查出来的，相对安全
        # 总是包含 'public' 作为备选，这样可以访问共享表和函数
        await session.execute(text(f"SET LOCAL search_path = '{tenant_schema}', public;"))
        yield session  # 提供 session 给 API 函数
        await session.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        await session.rollback()
        raise  # 将异常重新抛出，FastAPI 会处理成 500 错误
    finally:
        await session.close()


# --- 用于管理接口的依赖项 ---
async def get_public_db() -> AsyncGenerator[AsyncSession, None]:
    """获取一个只访问 public schema 的数据库会话（用于租户管理等）"""
    session: AsyncSession = AsyncSessionFactory()
    try:
        await session.execute(text("SET LOCAL search_path = public;"))
        yield session  # 提供 session 给 API 函数
        await session.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        await session.rollback()
        raise  # 将异常重新抛出，FastAPI 会处理成 500 错误
    finally:
        await session.close()


async def verify_admin_key(x_admin_key: str = Header(...)) -> None:
    """简单的 API Key 验证，用于保护管理接口"""
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin API Key",
        )
