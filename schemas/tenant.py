# -*- coding: utf-8 -*-
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TenantBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    schema_name: str = Field(..., min_length=3, max_length=63)
    subdomain: Optional[str] = Field(None, min_length=3, max_length=100)

    @field_validator('schema_name')
    def schema_name_format(cls, v):
        # 验证 schema_name 格式 (PostgreSQL 标识符规则)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Schema name must start with a letter or underscore, followed by letters, numbers, or underscores')
        if len(v) > 63:  # PostgreSQL 标识符长度限制
            raise ValueError('Schema name cannot exceed 63 characters')
        return v.lower()

    @field_validator('subdomain')
    def subdomain_alphanumeric(cls, v):
        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', v):
            raise ValueError('Subdomain must be lowercase alphanumeric with optional hyphens')
        return v


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    is_active: Optional[bool] = None


class TenantInDB(TenantBase):
    id: int
    is_active: bool
    schema_name: str  # InDB 时 schema_name 必须存在

    class Config:
        from_attributes = True  # Pydantic V2 (旧版 orm_mode = True)
