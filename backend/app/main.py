"""FastAPI 应用入口（core service）。

负责：
- 用 lifespan 在启动时拉起编排引擎（连接 Redis、启动结果消费循环），关闭时优雅停止。
- 挂载网关中间件（认证/限流）、CORS、API 路由。
- 提供健康检查。

运行：
    uvicorn app.main:app --host 0.0.0.0 --port 8000
worker 单独进程运行：
    python -m app.workers.worker
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.dag_executor import orchestrator
from app.gateway import GatewayMiddleware
from app.observability.logger import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：连接 Redis + 启动结果消费循环。
    await orchestrator.start()
    logger.info("core service ready")
    yield
    # 关闭：优雅停止后台任务。
    await orchestrator.stop()


app = FastAPI(
    title="Async Orchestrator（异步编排调度系统）",
    description="FastAPI + Redis Streams + React 的 DAG 异步编排调度教学项目",
    version="1.0.0",
    lifespan=lifespan,
)

# 网关：认证 / 限流。
app.add_middleware(GatewayMiddleware)

# 允许前端跨域访问。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
