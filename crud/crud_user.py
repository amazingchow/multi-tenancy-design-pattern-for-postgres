# -*- coding: utf-8 -*-
from models.tenant import Product  # 导入租户模型

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.user import ProductCreate


async def create_item(db: AsyncSession, item: ProductCreate) -> Product:
    db_item = Product(**item.model_dump())
    db.add(db_item)
    await db.flush()
    await db.refresh(db_item)
    return db_item


async def get_items(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Product]:
    result = await db.execute(select(Product).offset(skip).limit(limit))
    return result.scalars().all()


async def get_item(db: AsyncSession, item_id: int) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == item_id))
    return result.scalar_one_or_none()
