# -*- coding: utf-8 -*-
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings

# 使用 psycopg (asyncpg 也可以)
# 确保 DATABASE_URL 格式正确，例如: postgresql+psycopg://user:password@host:port/dbname
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # echo=True 打印SQL
    future=True
)

# 创建异步 Session 工厂
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,  # expire_on_commit=False 允许在提交后访问对象属性，对于 FastAPI 依赖项很方便
    class_=AsyncSession
)
