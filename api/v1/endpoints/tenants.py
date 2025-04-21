# -*- coding: utf-8 -*-
import logging
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api import deps
from crud import crud_tenant
from schemas.tenant import TenantCreate, TenantInDB, TenantUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=TenantInDB, status_code=status.HTTP_201_CREATED, dependencies=[Depends(deps.verify_admin_key)])
async def create_new_tenant(
    tenant_in: TenantCreate = Body(...),
    db: AsyncSession = Depends(deps.get_public_db)
):
    """
    创建新租户 (包括 schema 和 public 表记录)。
    需要 Admin API Key。
    **注意:** 此端点完成后，需要手动或通过后台任务为新 schema 运行数据库迁移。
    """
    # 检查 subdomain 和 schema_name 是否已存在
    existing_subdomain = await crud_tenant.get_tenant_by_subdomain(db, tenant_in.subdomain)
    if existing_subdomain:
        raise HTTPException(status_code=400, detail=f"Subdomain '{tenant_in.subdomain}' already registered.")

    # 确保 schema_name 在 Pydantic 模型中已生成或验证
    if not tenant_in.schema_name:
        tenant_in = TenantCreate(**tenant_in.model_dump())  # 重新构建以触发 validator 生成 schema_name

    existing_schema = await crud_tenant.get_tenant_by_schema_name(db, tenant_in.schema_name)
    if existing_schema:
        raise HTTPException(status_code=400, detail=f"Schema name '{tenant_in.schema_name}' already exists or is planned.")

    try:
        tenant = await crud_tenant.create_tenant(db, tenant_in=tenant_in)
        # 此处应该触发后台任务运行迁移: trigger_migration_task(tenant.schema_name)
        return tenant
    except HTTPException as http_exc:
        raise http_exc
    except ValueError as ve:  # Pydantic 或 CRUD 中的验证错误
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to create tenant '{tenant_in.name}': {e}", exc_info=True)
        # 回滚可能已在 get_public_db 的 finally 块中处理，但这里提供详细错误
        raise HTTPException(status_code=500, detail=f"Internal server error during tenant creation: {e}")


@router.get("/", response_model=List[TenantInDB], dependencies=[Depends(deps.verify_admin_key)])
async def read_tenants(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_public_db)
):
    """获取租户列表 (需要 Admin Key)"""
    tenants = await crud_tenant.get_tenants(db, skip=skip, limit=limit)
    return tenants


@router.patch("/{tenant_id}", response_model=TenantInDB, dependencies=[Depends(deps.verify_admin_key)])
async def update_existing_tenant(
    tenant_id: int,
    tenant_in: TenantUpdate,
    db: AsyncSession = Depends(deps.get_public_db)
):
    """更新租户信息 (需要 Admin Key)"""
    db_tenant = await crud_tenant.get_tenant_by_id(db, tenant_id)
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    updated_tenant = await crud_tenant.update_tenant(db=db, db_tenant=db_tenant, tenant_in=tenant_in)
    return updated_tenant
