# -*- coding: utf-8 -*-
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from starlette.responses import JSONResponse

from api.v1.api import api_router
from middlewares.tenant import TenantMiddleware

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# --- 生命周期事件 (可选) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    yield
    logger.info("Application shutdown...")

# --- FastAPI 实例 ---
app = FastAPI(
    title="Multi-Tenant App",
    description="Example FastAPI application with PostgreSQL Schema-per-Tenant Multi-Tenancy",
    version="0.1.0",
    lifespan=lifespan
)
# --- 路由 ---
app.include_router(api_router, prefix="/api/v1")
# --- 中间件 ---
# TenantMiddleware 必须放在需要租户上下文的路由之前
app.add_middleware(TenantMiddleware)


# --- 全局异常处理 (可选) ---
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # 避免覆盖 FastAPI 的 HTTPException 处理
    if isinstance(exc, HTTPException):
        raise exc
    # 对于其他未捕获的异常，记录并返回 500
    logger.error(f"Unhandled exception for request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {type(exc).__name__}"},
    )
