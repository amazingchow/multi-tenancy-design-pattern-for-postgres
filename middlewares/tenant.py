# -*- coding: utf-8 -*-
import logging

from models.public import Tenant

from fastapi import Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from core.db import AsyncSessionFactory

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 对于特殊路径（如管理API、静态文件、根路径等）可能不需要租户上下文
        # 这里简化处理，所有路径都需要有效租户，除了根路径或特定管理路径
        path = request.url.path
        if path.startswith("/api/v1/admin/tenants") or path == "/" or path == "/docs" or path == "/openapi.json":
            # 管理接口或公共接口，不需要租户 schema，或者使用默认public
            request.state.tenant_schema = "public"
            request.state.tenant_info = None
            response = await call_next(request)
            return response

        tenant_id = request.headers.get("X-Tenant-ID", None)
        if not tenant_id:
            # 如果没有提供租户 ID，返回 403 Forbidden
            return Response("Forbidden: Missing X-Tenant-ID header", status_code=status.HTTP_403_FORBIDDEN)
        tenant_id = int(tenant_id)

        tenant: Tenant | None = None
        # 使用独立的 Session 查询 public.tenants，避免 search_path 干扰
        session: AsyncSession = AsyncSessionFactory()
        try:
            stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.is_active == True)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error querying tenant<id:{tenant_id}>: {e}")
            return Response(f"Internal Server Error: Could not query tenant<id:{tenant_id}>", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            await session.close()

        if tenant:
            request.state.tenant_schema = tenant.schema_name
            request.state.tenant_info = tenant  # 存储整个对象供后续使用
            response = await call_next(request)
            return response
        else:
            logger.warning(f"Tenant<id:{tenant_id}> not found")
            # 如果没有匹配的、活跃的租户，返回 404 或 403
            # 这里返回 404 更符合资源未找到的语义
            return Response(f"Tenant<id:{tenant_id}> not found", status_code=status.HTTP_404_NOT_FOUND)
