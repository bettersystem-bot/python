"""极简分布式追踪（对应架构图右侧的 trace）。

演示 trace 的核心概念：一次 DAG 执行是一条 trace，每个节点的执行是一个 span，
span 之间通过 parent 关系串成树/链。这样就能回答"这次编排里时间花在哪了"。

真实系统用 OpenTelemetry / BytedTrace。这里用进程内字典记录 span，
通过 contextvars 传递当前 trace 上下文（asyncio 中跨 await 传递上下文的标准做法）。
"""
from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator, Optional

# contextvars 在 asyncio 中能正确地随协程切换而隔离，是传递 trace 上下文的正道。
_current_trace: ContextVar[Optional[str]] = ContextVar("current_trace", default=None)
_current_span: ContextVar[Optional[str]] = ContextVar("current_span", default=None)


class Tracer:
    def __init__(self) -> None:
        # trace_id -> span 列表
        self._traces: dict[str, list[dict[str, Any]]] = {}

    def new_trace(self, trace_id: Optional[str] = None) -> str:
        trace_id = trace_id or uuid.uuid4().hex[:12]
        self._traces.setdefault(trace_id, [])
        _current_trace.set(trace_id)
        return trace_id

    @contextmanager
    def span(self, name: str, **attrs: Any) -> Iterator[dict[str, Any]]:
        """开启一个 span，with 块结束自动记录耗时。"""
        trace_id = _current_trace.get() or self.new_trace()
        span_id = uuid.uuid4().hex[:8]
        parent = _current_span.get()
        record = {
            "span_id": span_id, "parent": parent, "name": name,
            "attrs": attrs, "start": time.time(), "end": None, "duration_ms": 0.0,
        }
        token = _current_span.set(span_id)
        self._traces.setdefault(trace_id, []).append(record)
        try:
            yield record
        finally:
            record["end"] = time.time()
            record["duration_ms"] = round((record["end"] - record["start"]) * 1000, 2)
            _current_span.reset(token)

    def get_trace(self, trace_id: str) -> list[dict[str, Any]]:
        return self._traces.get(trace_id, [])


tracer = Tracer()
