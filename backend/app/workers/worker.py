"""Worker（对应架构图的 hamlet worker / 训推下游常驻服务）。

worker 是一个**独立常驻进程**，它的生命周期就是一个消费循环：

    while True:
        tasks = 从队列拉取一批 (XREADGROUP, 阻塞)
        for task in tasks:
            并发执行 handler
            把结果回传给结果队列 (XADD)
            自定义后处理 (callback)
            XACK 确认

设计要点（这些是"调度系统的 worker 该怎么写"的关键）：
1. **竞争消费**：多个 worker 加入同一消费组，同一条消息只会被一个 worker 拿到，
   天然负载均衡，水平扩展只需多起几个进程。
2. **并发执行**：一个 worker 进程内用 asyncio.Semaphore 限制同时执行的任务数
   （worker_concurrency），既能并发又不过载。
3. **at-least-once**：先执行、回传，再 XACK。若 worker 在 ACK 前崩溃，消息留在 PEL，
   会被其它 worker 的 XAUTOCLAIM 重新认领执行 —— 保证任务不丢（但可能重复，需幂等）。
4. **背压**：BLOCK 阻塞读 + Semaphore，让 worker 在忙时自然放慢拉取节奏。
5. **优雅退出**：收到停止信号后停止拉取新任务，等在途任务做完再退出。

通过 RESULT 回传 + 引擎消费结果推进 DAG，worker 完全不需要知道 DAG 的存在，
它只认识"一个个独立任务"。编排与执行彻底解耦 —— 这是本项目最想让你体会的点。
"""
from __future__ import annotations

import asyncio
import os
import socket
import time
from typing import Optional

import httpx

from app.config import settings
from app.core.queue import queue
from app.models import NodeType, ResultMessage, TaskMessage
from app.observability.logger import get_logger
from app.observability.metrics import metrics
from app.observability.trace import tracer
from app.workers import callback, handlers

logger = get_logger("worker")


class Worker:
    def __init__(self, worker_id: Optional[str] = None, queues: Optional[list[str]] = None) -> None:
        self.worker_id = worker_id or f"{socket.gethostname()}-{os.getpid()}"
        # 该 worker 负责消费哪些 node 类型对应的 stream。
        types = queues or self._parse_queue_types()
        self.streams = [settings.queue_name(t) for t in types]
        self.semaphore = asyncio.Semaphore(settings.worker_concurrency)
        self._running = False
        self._inflight = 0
        # worker 在独立进程时无法直接调用引擎，需通过内部 API 通知"节点开始执行"。
        self._api_base = os.environ.get("CORE_API_BASE", f"http://localhost:{settings.port}")
        self._http: Optional[httpx.AsyncClient] = None

    @staticmethod
    def _parse_queue_types() -> list[str]:
        raw = settings.worker_queues.strip()
        if raw:
            return [t.strip() for t in raw.split(",") if t.strip()]
        # 默认消费全部类型。
        return [t.value for t in NodeType]

    async def start(self) -> None:
        await queue.connect()
        self._http = httpx.AsyncClient(timeout=5.0)
        for s in self.streams:
            await queue.ensure_group(s)
        self._running = True
        logger.info("worker %s consuming streams=%s concurrency=%d",
                    self.worker_id, self.streams, settings.worker_concurrency)
        await self._loop()

    async def stop(self) -> None:
        self._running = False

    async def _loop(self) -> None:
        """主消费循环。"""
        # 后台并行跑一个"认领僵尸消息"的协程，演示故障转移。
        reclaimer = asyncio.create_task(self._reclaim_loop())
        try:
            while self._running:
                try:
                    batch = await queue.consume_tasks(
                        streams=self.streams, consumer=self.worker_id,
                        count=settings.worker_concurrency, block_ms=2000,
                    )
                except Exception as e:  # noqa: BLE001
                    logger.exception("consume error: %s", e)
                    await asyncio.sleep(0.5)
                    continue

                if not batch:
                    continue
                # 并发处理这一批，每个任务受 Semaphore 限流。
                await asyncio.gather(*(self._process(s, mid, t) for s, mid, t in batch))
        finally:
            reclaimer.cancel()
            if self._http:
                await self._http.aclose()

    async def _process(self, stream: str, msg_id: str, task: TaskMessage) -> None:
        async with self.semaphore:
            self._inflight += 1
            metrics.gauge(f"worker.{self.worker_id}.inflight", self._inflight)
            tracer.new_trace(task.dag_run_id)
            try:
                await self._notify_running(task)
                with tracer.span("execute", node=task.node_id, type=task.node_type.value):
                    result = await self._execute_with_timeout(task)
                await queue.publish_result(result)
                await callback.run_callbacks(result)
            finally:
                # 无论成功失败都 ACK：失败结果已回传，引擎会按重试策略重新派发新消息。
                # （若想让未 ACK 的消息靠 XAUTOCLAIM 重试，可改为仅成功才 ACK。本项目用显式重试更直观。）
                await queue.ack_task(stream, msg_id)
                self._inflight -= 1
                metrics.gauge(f"worker.{self.worker_id}.inflight", self._inflight)

    async def _execute_with_timeout(self, task: TaskMessage) -> ResultMessage:
        """执行任务，套上超时保护（asyncio.wait_for）。"""
        start = time.time()
        try:
            output, duration_ms = await asyncio.wait_for(
                handlers.execute(task), timeout=settings.node_timeout_seconds,
            )
            metrics.incr("worker.executed.ok")
            return ResultMessage(
                dag_run_id=task.dag_run_id, node_id=task.node_id, success=True,
                output=output, worker_id=self.worker_id, attempt=task.attempt,
                duration_ms=round(duration_ms, 2),
            )
        except asyncio.TimeoutError:
            metrics.incr("worker.executed.timeout")
            return ResultMessage(
                dag_run_id=task.dag_run_id, node_id=task.node_id, success=False,
                error=f"执行超时（>{settings.node_timeout_seconds}s）",
                worker_id=self.worker_id, attempt=task.attempt,
                duration_ms=round((time.time() - start) * 1000, 2),
            )
        except Exception as e:  # noqa: BLE001
            metrics.incr("worker.executed.error")
            return ResultMessage(
                dag_run_id=task.dag_run_id, node_id=task.node_id, success=False,
                error=str(e), worker_id=self.worker_id, attempt=task.attempt,
                duration_ms=round((time.time() - start) * 1000, 2),
            )

    async def _notify_running(self, task: TaskMessage) -> None:
        """通过内部 API 告诉引擎"我开始跑这个节点了"，用于前端实时展示 RUNNING。"""
        if not self._http:
            return
        try:
            await self._http.post(
                f"{self._api_base}/internal/node-running",
                json={"dag_run_id": task.dag_run_id, "node_id": task.node_id,
                      "worker_id": self.worker_id},
            )
        except Exception:  # noqa: BLE001  通知失败不影响执行，仅影响实时展示。
            pass

    async def _reclaim_loop(self) -> None:
        """周期性认领其它 worker 遗留在 PEL 的僵尸消息（演示 at-least-once 故障转移）。"""
        while self._running:
            await asyncio.sleep(15)
            for s in self.streams:
                try:
                    stale = await queue.claim_stale_tasks(
                        stream=s, consumer=self.worker_id,
                        min_idle_ms=settings.node_timeout_seconds * 1000 * 2,
                    )
                    for stream, mid, task in stale:
                        logger.warning("reclaimed stale task node=%s, reprocessing", task.node_id)
                        metrics.incr("worker.reclaimed")
                        await self._process(stream, mid, task)
                except Exception:  # noqa: BLE001
                    pass


async def main() -> None:
    worker = Worker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(main())
