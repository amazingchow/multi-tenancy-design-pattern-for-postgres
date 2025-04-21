# -*- coding: utf-8 -*-
from typing import Optional

from models.base import Base

import sqlalchemy
import sqlalchemy.orm as sqlalchemy_orm


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}

    id: sqlalchemy_orm.Mapped[int] = sqlalchemy_orm.mapped_column(sqlalchemy.Integer, primary_key=True, index=True)
    name: sqlalchemy_orm.Mapped[str] = sqlalchemy_orm.mapped_column(sqlalchemy.String(100), nullable=False, unique=True)
    schema_name: sqlalchemy_orm.Mapped[str] = sqlalchemy_orm.mapped_column(sqlalchemy.String(63), nullable=False, unique=True, index=True)
    subdomain: sqlalchemy_orm.Mapped[Optional[str]] = sqlalchemy_orm.mapped_column(sqlalchemy.String(100), unique=True, index=True)
    is_active: sqlalchemy_orm.Mapped[bool] = sqlalchemy_orm.mapped_column(sqlalchemy.Boolean, default=True)
    created_at: sqlalchemy_orm.Mapped[sqlalchemy.DateTime] = sqlalchemy_orm.mapped_column(sqlalchemy.DateTime(timezone=True), server_default=sqlalchemy.func.now())

    def __repr__(self):
        return f"<Tenant(id={self.id}, name='{self.name}', schema='{self.schema_name}')>"
