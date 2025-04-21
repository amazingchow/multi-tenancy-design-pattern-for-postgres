from fastapi import APIRouter

from api.v1.endpoints import tenants, users

api_router = APIRouter()
# 租户数据路由 (需要租户上下文)
api_router.include_router(users.router, prefix="/users", tags=["Users"])
# 管理路由 (通常不需要租户上下文或使用 public 上下文)
api_router.include_router(tenants.router, prefix="/admin/tenants", tags=["Admin - Tenants"])
