"""轻量指标采集（对应架构图右侧的 metrics）。

真实系统会用 Prometheus / 字节 Metrics SDK 打点。教学项目用一个进程内的
线程/协程安全计数器与直方图来演示"该在异步系统的哪些位置埋点"：

- counter: 单调递增计数（如 任务派发数、成功数、失败数、重试数）。
- gauge:   瞬时值（如 当前在途任务数、活跃 DAG 数）。
- timing:  耗时样本，用于算 p50/p95（如 节点执行耗时）。

注意：asyncio 单线程事件循环内对普通 dict 的 += 是安全的（无抢占点），
但 worker 可能在独立进程，故指标本身是"每进程局部"的，前端展示的是聚合视图。
"""
from __future__ import annotations

import threading
from typing import Any


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._timings: dict[str, list[float]] = {}

    def incr(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0.0) + value

    def gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def observe(self, name: str, value_ms: float) -> None:
        with self._lock:
            buf = self._timings.setdefault(name, [])
            buf.append(value_ms)
            # 只保留最近 1000 个样本，避免无限增长。
            if len(buf) > 1000:
                del buf[: len(buf) - 1000]

    @staticmethod
    def _percentile(samples: list[float], pct: float) -> float:
        if not samples:
            return 0.0
        ordered = sorted(samples)
        k = int(round((pct / 100.0) * (len(ordered) - 1)))
        return round(ordered[k], 2)

    def snapshot(self) -> dict[str, Any]:
        """导出当前所有指标，供 /metrics 接口返回。"""
        with self._lock:
            timings = {
                name: {
                    "count": len(samples),
                    "p50": self._percentile(samples, 50),
                    "p95": self._percentile(samples, 95),
                    "max": round(max(samples), 2) if samples else 0.0,
                }
                for name, samples in self._timings.items()
            }
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timings": timings,
            }


metrics = Metrics()
