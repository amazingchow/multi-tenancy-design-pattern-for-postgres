# -*- coding: utf-8 -*-
import logging

from models.public import Tenant

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.tenant import TenantCreate, TenantUpdate

logger = logging.getLogger(__name__)


async def get_tenant_by_id(db: AsyncSession, tenant_id: int) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


async def get_tenant_by_schema_name(db: AsyncSession, schema_name: str) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.schema_name == schema_name))
    return result.scalar_one_or_none()


async def get_tenant_by_subdomain(db: AsyncSession, subdomain: str) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.subdomain == subdomain))
    return result.scalar_one_or_none()


async def create_tenant(db: AsyncSession, tenant_in: TenantCreate) -> Tenant:
    if not tenant_in.schema_name:
        raise ValueError("Schema name must be provided or generated before creating tenant object")

    # 1. 创建数据库 Schema (如果不存在)
    try:
        # 使用 text 防止 ORM 尝试解释为表名
        # 重要: 确保 schema_name 经过了严格验证，防止 SQL 注入
        await db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{tenant_in.schema_name}";'))
        logger.info(f"Schema '{tenant_in.schema_name}' created or already exists.")
    except Exception as e:
        logger.error(f"Failed to create schema '{tenant_in.schema_name}': {e}")
        # 可能需要根据错误类型决定是否继续。如果 schema 已存在可能没问题。
        # 如果是权限问题等，则应抛出异常。
        # 这里假设 schema 已存在是可接受的，但创建失败是严重错误
        if "already exists" not in str(e).lower():
            raise HTTPException(status_code=500, detail=f"Database schema creation failed for {tenant_in.schema_name}") from e

    # 2. 在 public.tenants 表中创建记录
    db_tenant = Tenant(
        name=tenant_in.name,
        schema_name=tenant_in.schema_name,
        subdomain=tenant_in.subdomain,
        is_active=True  # 通常新租户是活跃的
    )
    db.add(db_tenant)
    await db.flush()  # 刷新以获取 ID 或处理唯一约束冲突
    await db.refresh(db_tenant)
    logger.info(f"Tenant record created for {db_tenant.name} with schema {db_tenant.schema_name}")

    # 3. **关键**: 运行 Alembic 迁移以在新 Schema 中创建表
    #    这一步通常在 API 请求之外异步执行，或者通过独立的管理脚本完成
    #    因为运行迁移可能耗时较长，不适合放在 API 请求处理中
    #    这里只是注释说明需要这一步
    #    run_alembic_migration_for_schema(tenant_in.schema_name)
    logger.warning(f"ACTION REQUIRED: Run migrations for new schema '{tenant_in.schema_name}' using Alembic.")

    return db_tenant


async def update_tenant(db: AsyncSession, db_tenant: Tenant, tenant_in: TenantUpdate) -> Tenant:
    update_data = tenant_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tenant, key, value)
    db.add(db_tenant)
    await db.flush()
    await db.refresh(db_tenant)
    return db_tenant


async def get_tenants(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Tenant]:
    result = await db.execute(select(Tenant).offset(skip).limit(limit))
    return result.scalars().all()
