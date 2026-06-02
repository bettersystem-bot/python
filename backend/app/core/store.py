"""运行态存储（State Store）。

保存所有 DagRun 的实时状态，供 API 查询、引擎读写。
教学项目用进程内字典 + asyncio.Lock；真实系统会换成 Redis/DB。

注意并发：编排引擎在事件循环里会频繁更新节点状态，API 协程会并发读取，
因此用 asyncio.Lock 保护对同一 DagRun 的"读-改-写"，避免并发更新丢失。
"""
from __future__ import annotations

import asyncio
from typing import Optional

from app.models import DagRun


class DagRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, DagRun] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock_for(self, dag_run_id: str) -> asyncio.Lock:
        lock = self._locks.get(dag_run_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[dag_run_id] = lock
        return lock

    async def put(self, run: DagRun) -> None:
        self._runs[run.id] = run

    async def get(self, dag_run_id: str) -> Optional[DagRun]:
        return self._runs.get(dag_run_id)

    async def list_summaries(self) -> list[dict]:
        # 最新创建的排前面。
        runs = sorted(self._runs.values(), key=lambda r: r.created_at, reverse=True)
        return [r.summary() for r in runs]

    def lock(self, dag_run_id: str) -> asyncio.Lock:
        """获取某个 DagRun 的更新锁，用于 async with 保护读-改-写。"""
        return self._lock_for(dag_run_id)


store = DagRunStore()
