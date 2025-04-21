# -*- coding: utf-8 -*-
from typing import List

from models.public import Tenant

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api import deps
from crud import crud_user
from schemas.user import ProductCreate, ProductInDB

router = APIRouter()


@router.post("/", response_model=ProductInDB, status_code=status.HTTP_201_CREATED)
async def create_tenant_item(
    item_in: ProductCreate,
    db: AsyncSession = Depends(deps.get_db),  # 获取设置了 search_path 的 session
    current_tenant: Tenant | None = Depends(deps.get_tenant_info)  # 获取当前租户信息
):
    """
    在当前租户的 schema 中创建一个新的 Item。
    """
    if not current_tenant:  # 理论上 get_db 会先失败，但加层保险
        raise HTTPException(status_code=400, detail="Tenant context not available.")
    return await crud_user.create_item(db=db, item=item_in)


@router.get("/", response_model=List[ProductInDB])
async def read_tenant_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_tenant: Tenant | None = Depends(deps.get_tenant_info)
):
    """
    获取当前租户的 Item 列表。
    """
    if not current_tenant:
        raise HTTPException(status_code=400, detail="Tenant context not available.")
    items = await crud_user.get_items(db=db, skip=skip, limit=limit)
    return items


@router.get("/{item_id}", response_model=ProductInDB)
async def read_tenant_item(
    item_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_tenant: Tenant | None = Depends(deps.get_tenant_info)
):
    """获取当前租户的指定 Item"""
    if not current_tenant:
        raise HTTPException(status_code=400, detail="Tenant context not available.")
    db_item = await crud_user.get_item(db=db, item_id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
