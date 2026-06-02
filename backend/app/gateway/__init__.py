"""智创网关（对应架构图的"智创网关：认证 / 限流"）。

在 FastAPI 里用中间件实现网关的两个核心职责：
1. 认证（Authentication）：校验请求头里的 API Key（演示用，固定 token）。
2. 限流（Rate Limiting）：用滑动/固定窗口计数器限制每个客户端的提交频率，
   保护后端编排引擎不被瞬时洪峰打垮 —— 这本身也是"调度"思想的一部分（入口削峰）。

注意：限流计数器是进程内的 asyncio 友好实现；多实例部署时应换成 Redis 计数。
为方便本地学习，认证默认放行（ALLOW_ANONYMOUS=true）。
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.logger import get_logger
from app.observability.metrics import metrics

logger = get_logger("gateway")

# 演示用配置。
_API_KEY = os.environ.get("API_KEY", "demo-key")
_ALLOW_ANON = os.environ.get("ALLOW_ANONYMOUS", "true").lower() == "true"
_RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_MIN", "120"))  # 每客户端每分钟最大请求数
_WINDOW = 60.0

# 只对"写操作"（提交任务）做认证与限流；读接口、文档、WebSocket 放行。
_PROTECTED_PREFIXES = ("/api/dags",)
_PROTECTED_METHODS = {"POST"}


class GatewayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        # client_id -> 最近请求时间戳队列
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _needs_guard(self, request: Request) -> bool:
        if request.method not in _PROTECTED_METHODS:
            return False
        return any(request.url.path.startswith(p) for p in _PROTECTED_PREFIXES)

    def _authenticate(self, request: Request) -> bool:
        if _ALLOW_ANON:
            return True
        return request.headers.get("X-API-Key") == _API_KEY

    def _rate_ok(self, client_id: str) -> bool:
        now = time.time()
        dq = self._hits[client_id]
        # 滑动窗口：弹出窗口外的旧记录。
        while dq and now - dq[0] > _WINDOW:
            dq.popleft()
        if len(dq) >= _RATE_LIMIT:
            return False
        dq.append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        if self._needs_guard(request):
            if not self._authenticate(request):
                metrics.incr("gateway.rejected.auth")
                return JSONResponse(status_code=401, content={"detail": "认证失败：缺少或错误的 X-API-Key"})
            client_id = request.headers.get("X-Client-Id") or (request.client.host if request.client else "anon")
            if not self._rate_ok(client_id):
                metrics.incr("gateway.rejected.ratelimit")
                logger.warning("rate limited client=%s", client_id)
                return JSONResponse(status_code=429, content={"detail": "请求过于频繁，已被限流"})
            metrics.incr("gateway.passed")
        return await call_next(request)
