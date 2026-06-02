"""进程内事件总线（EventBus）。

对应架构图里的"业务 EventBus"。作用：把编排引擎内部发生的状态变化
（节点就绪/派发/运行/成功/失败……）以事件的形式广播出去，让任意数量的
订阅者（这里主要是 WebSocket 连接）实时收到。

实现要点（异步编排里非常常用的模式）：
- 每个订阅者拿到一个自己的 asyncio.Queue。
- publish() 把事件 put 到所有订阅者的队列里（非阻塞，满了就丢弃最旧的，避免慢消费者拖垮发布方）。
- 订阅者通过 async generator 持续 await 自己的队列，实现"推送"。

这是「一对多扇出（fan-out）」的典型异步实现，比 callback 列表更安全（天然背压、易取消）。
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator

from app.models import OrchestrationEvent


class EventBus:
    def __init__(self, per_subscriber_buffer: int = 256) -> None:
        self._subscribers: set[asyncio.Queue[OrchestrationEvent]] = set()
        self._buffer = per_subscriber_buffer
        self._lock = asyncio.Lock()

    async def publish(self, event: OrchestrationEvent) -> None:
        """向所有订阅者广播一个事件。"""
        async with self._lock:
            subscribers = list(self._subscribers)
        for q in subscribers:
            # 慢消费者保护：队列满了就先丢弃最旧的一条，保证发布方永不阻塞。
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def subscribe(self) -> AsyncIterator[OrchestrationEvent]:
        """订阅事件流。用法： async for ev in bus.subscribe(): ..."""
        q: asyncio.Queue[OrchestrationEvent] = asyncio.Queue(maxsize=self._buffer)
        async with self._lock:
            self._subscribers.add(q)
        try:
            while True:
                yield await q.get()
        finally:
            # 订阅者断开（如 WebSocket 关闭）时务必清理，避免内存泄漏。
            async with self._lock:
                self._subscribers.discard(q)

    async def subscriber_count(self) -> int:
        async with self._lock:
            return len(self._subscribers)


# 全局单例：整个进程共享一个 EventBus。
event_bus = EventBus()
