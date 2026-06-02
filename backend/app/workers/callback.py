"""回调服务（对应架构图的 callback service —— 允许自定义后处理）。

worker 每完成一个节点，除了把结果回传给编排引擎，还会调用这里的钩子做
"自定义后处理"：比如把结果发到业务 EventBus / RPC、写审计日志、触发外部通知等。

教学项目里，我们把它实现成一组可插拔的异步回调，默认实现是记录日志 +
打点。你可以在 register() 注册自己的回调来扩展，而无需改动 worker 主流程。
这正是 callback service "允许自定义后处理"的设计意图：把业务侧逻辑与调度核心解耦。
"""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from app.models import ResultMessage
from app.observability.logger import get_logger
from app.observability.metrics import metrics

logger = get_logger("callback")

# 回调签名：接收 ResultMessage，做任意异步后处理。
Callback = Callable[[ResultMessage], Awaitable[None]]

_callbacks: list[Callback] = []


def register(cb: Callback) -> None:
    _callbacks.append(cb)


async def _default_log_callback(result: ResultMessage) -> None:
    status = "OK" if result.success else "FAIL"
    logger.info("callback dag=%s node=%s %s by=%s %.1fms",
                result.dag_run_id, result.node_id, status,
                result.worker_id, result.duration_ms)
    metrics.incr("callback.invoked")


# 注册默认回调。
register(_default_log_callback)


async def run_callbacks(result: ResultMessage) -> None:
    """并发执行所有已注册回调；单个回调异常不影响其它回调与主流程。"""
    if not _callbacks:
        return
    results = await asyncio.gather(
        *(cb(result) for cb in _callbacks), return_exceptions=True
    )
    for r in results:
        if isinstance(r, Exception):
            logger.warning("callback raised: %s", r)
            metrics.incr("callback.error")
