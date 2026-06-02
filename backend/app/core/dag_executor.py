"""DAG 编排引擎（对应架构图的 dag executor）—— 本项目最核心的模块。

它做的事，就是"异步编排调度"的本质：

  1. 提交：解析 DagSpec -> DagRun，找出最初就绪的节点（无依赖的根节点）。
  2. 派发：在并发上限（max_inflight）内，把就绪节点交给 scheduler 投递进消息队列。
     —— 注意：引擎**不亲自执行**节点！它只决策"现在该让谁就绪、派发谁"。
  3. 推进：一个后台协程持续从结果队列消费 worker 回传的结果，
     每收到一个成功结果，就把它的下游节点的"未满足依赖数"减一；
     当某下游节点的依赖全部满足，它变就绪，再被派发。
     这就是经典的 **入度推进（in-degree driven）拓扑执行**。
  4. 失败：节点失败 -> 在重试上限内重新派发；超过上限 -> 按失败策略处理
     （FAIL_FAST：终止整图并跳过其余；CONTINUE：只跳过失败节点的后代）。
  5. 结束：当没有任何节点处于 进行中/待派发 状态时，整图结束。

为什么用"入度推进 + 消息队列"而不是简单的 asyncio.gather？
- gather 适合"一把并发、互相独立"的任务；但 DAG 节点有依赖先后，需要按拓扑推进。
- 把执行放进消息队列，意味着真正干活的 worker 可以是另外的进程/机器，可水平扩展，
  且引擎与执行解耦、互不阻塞 —— 这才是生产级"调度"的样子。

并发要点：
- 引擎运行在事件循环里，对每个 DagRun 的"读-改-写"用 store 的锁保护，
  避免结果推进与新派发并发修改同一张图造成状态错乱。
- 派发受 max_inflight_per_dag 限制，形成 **背压（backpressure）**，防止一次性灌爆队列。
"""
from __future__ import annotations

import asyncio
from typing import Optional

from app.config import settings
from app.core.eventbus import event_bus
from app.core.queue import queue
from app.core.scheduler import dispatch_node
from app.core.store import store
from app.models import (
    DagRun, DagStatus, EventType, NodeStatus, OrchestrationEvent, ResultMessage,
)
from app.observability.logger import get_logger
from app.observability.metrics import metrics

logger = get_logger("executor")

# 进行中/未完成的状态集合。
_ACTIVE = {NodeStatus.PENDING, NodeStatus.READY, NodeStatus.DISPATCHED, NodeStatus.RUNNING}


class Orchestrator:
    """全局编排引擎，管理所有 DagRun 的推进。"""

    def __init__(self) -> None:
        self._result_task: Optional[asyncio.Task] = None
        self._running = False

    # ------------------------------------------------------------------ #
    # 生命周期
    # ------------------------------------------------------------------ #
    async def start(self) -> None:
        """启动后台结果消费循环。由 FastAPI 的 lifespan 调用。"""
        if self._running:
            return
        await queue.connect()
        self._running = True
        self._result_task = asyncio.create_task(self._consume_results_loop(), name="result-consumer")
        logger.info("orchestrator started")

    async def stop(self) -> None:
        self._running = False
        if self._result_task:
            self._result_task.cancel()
            try:
                await self._result_task
            except asyncio.CancelledError:
                pass
        logger.info("orchestrator stopped")

    # ------------------------------------------------------------------ #
    # 提交一张图
    # ------------------------------------------------------------------ #
    async def submit(self, run: DagRun) -> DagRun:
        """登记一张已解析的 DagRun 并启动它（派发初始就绪节点）。"""
        await store.put(run)
        metrics.incr("dag.submitted")
        metrics.gauge("dag.active", await self._active_dag_count())
        await event_bus.publish(OrchestrationEvent(
            type=EventType.DAG_CREATED, dag_run_id=run.id,
            payload=run.summary(),
        ))
        async with store.lock(run.id):
            run.status = DagStatus.RUNNING
            await self._advance(run)
        return run

    # ------------------------------------------------------------------ #
    # 核心：推进一张图（在锁内调用）
    # ------------------------------------------------------------------ #
    async def _advance(self, run: DagRun) -> None:
        """计算当前就绪节点，并在并发上限内派发。

        这是引擎每次"想往前走一步"时调用的方法。它会：
        - 把所有依赖已满足的 PENDING 节点标记为 READY；
        - 在 max_inflight 限制内，把 READY 节点派发到队列。
        """
        # 1) 标记新就绪节点（依赖全部成功）。
        for node in run.nodes.values():
            if node.status != NodeStatus.PENDING:
                continue
            if all(run.nodes[d].status == NodeStatus.SUCCEEDED for d in node.depends_on):
                node.status = NodeStatus.READY
                await event_bus.publish(OrchestrationEvent(
                    type=EventType.NODE_READY, dag_run_id=run.id, node_id=node.id,
                ))

        # 2) 计算当前在途数，受背压限制派发就绪节点。
        inflight = sum(1 for n in run.nodes.values()
                       if n.status in (NodeStatus.DISPATCHED, NodeStatus.RUNNING))
        ready = [n for n in run.nodes.values() if n.status == NodeStatus.READY]
        for node in ready:
            if inflight >= settings.max_inflight_per_dag:
                break  # 留到下一轮推进再派发，形成背压。
            await dispatch_node(run, node)
            inflight += 1

        # 3) 检查整图是否已结束。
        await self._maybe_finish(run)

    async def _maybe_finish(self, run: DagRun) -> None:
        if run.status not in (DagStatus.RUNNING, DagStatus.PENDING):
            return
        if any(n.status in _ACTIVE for n in run.nodes.values()):
            return  # 还有活儿没干完。
        # 没有任何进行中的节点了 -> 收尾。
        failed = any(n.status == NodeStatus.FAILED for n in run.nodes.values())
        run.status = DagStatus.FAILED if failed else DagStatus.SUCCEEDED
        import time
        run.finished_at = time.time()
        metrics.incr(f"dag.{run.status.value}")
        metrics.gauge("dag.active", await self._active_dag_count())
        logger.info("dag %s finished: %s", run.id, run.status.value)
        await event_bus.publish(OrchestrationEvent(
            type=EventType.DAG_FINISHED, dag_run_id=run.id, payload=run.summary(),
        ))

    # ------------------------------------------------------------------ #
    # 结果消费循环：DAG 推进的"心跳"
    # ------------------------------------------------------------------ #
    async def _consume_results_loop(self) -> None:
        """持续从结果队列拉取 worker 回传的结果并推进对应 DAG。"""
        consumer = "orchestrator-result-consumer"
        while self._running:
            try:
                results = await queue.consume_results(consumer=consumer, count=32, block_ms=2000)
                for msg_id, result in results:
                    await self._handle_result(result)
                    await queue.ack_result(msg_id)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001  教学项目：循环要足够健壮，不能因单条异常退出。
                logger.exception("result loop error: %s", e)
                await asyncio.sleep(0.5)

    async def _handle_result(self, result: ResultMessage) -> None:
        run = await store.get(result.dag_run_id)
        if run is None:
            logger.warning("result for unknown dag %s, ignored", result.dag_run_id)
            return
        async with store.lock(run.id):
            node = run.nodes.get(result.node_id)
            if node is None or node.status not in (NodeStatus.DISPATCHED, NodeStatus.RUNNING):
                return  # 重复结果或状态不符，幂等忽略。

            if result.success:
                node.status = NodeStatus.SUCCEEDED
                node.output = result.output
                node.worker_id = result.worker_id
                node.finished_at = result.finished_at
                metrics.incr("node.succeeded")
                metrics.observe("node.duration_ms", result.duration_ms)
                await event_bus.publish(OrchestrationEvent(
                    type=EventType.NODE_SUCCEEDED, dag_run_id=run.id, node_id=node.id,
                    payload={"output": result.output, "worker": result.worker_id,
                             "duration_ms": result.duration_ms},
                ))
            else:
                await self._handle_failure(run, node, result)

            # 无论成功失败，都尝试推进图（可能解锁下游，或触发收尾）。
            await self._advance(run)

    async def _handle_failure(self, run: DagRun, node, result: ResultMessage) -> None:
        node.error = result.error
        node.worker_id = result.worker_id
        metrics.incr("node.failed")

        # 还能重试？放回 PENDING，让 _advance 重新就绪并派发。
        if node.attempt <= settings.node_max_retries:
            metrics.incr("node.retry")
            logger.warning("node %s failed (attempt %d), will retry: %s",
                           node.id, node.attempt, result.error)
            node.status = NodeStatus.PENDING
            await event_bus.publish(OrchestrationEvent(
                type=EventType.NODE_RETRY, dag_run_id=run.id, node_id=node.id,
                payload={"attempt": node.attempt, "error": result.error},
            ))
            return

        # 超过重试上限：判定失败。
        node.status = NodeStatus.FAILED
        node.finished_at = result.finished_at
        logger.error("node %s FAILED permanently: %s", node.id, result.error)
        await event_bus.publish(OrchestrationEvent(
            type=EventType.NODE_FAILED, dag_run_id=run.id, node_id=node.id,
            payload={"error": result.error, "worker": result.worker_id},
        ))
        await self._apply_failure_policy(run, node.id)

    async def _apply_failure_policy(self, run: DagRun, failed_node_id: str) -> None:
        """根据失败策略，跳过相应的未完成节点。"""
        from app.models import FailurePolicy

        if run.failure_policy == FailurePolicy.FAIL_FAST:
            # 终止：把所有还没干的节点全部跳过。
            for n in run.nodes.values():
                if n.status in (NodeStatus.PENDING, NodeStatus.READY):
                    await self._skip(run, n.id)
        else:
            # CONTINUE：只跳过失败节点的所有后代（传递闭包）。
            descendants = self._descendants(run, failed_node_id)
            for nid in descendants:
                n = run.nodes[nid]
                if n.status in (NodeStatus.PENDING, NodeStatus.READY):
                    await self._skip(run, nid)

    async def _skip(self, run: DagRun, node_id: str) -> None:
        node = run.nodes[node_id]
        node.status = NodeStatus.SKIPPED
        metrics.incr("node.skipped")
        await event_bus.publish(OrchestrationEvent(
            type=EventType.NODE_SKIPPED, dag_run_id=run.id, node_id=node_id,
        ))

    @staticmethod
    def _descendants(run: DagRun, node_id: str) -> set[str]:
        """求 node_id 的所有后代（依赖它、或间接依赖它的节点）。"""
        children: dict[str, list[str]] = {nid: [] for nid in run.nodes}
        for nid, n in run.nodes.items():
            for dep in n.depends_on:
                children[dep].append(nid)
        seen: set[str] = set()
        stack = list(children[node_id])
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(children[cur])
        return seen

    async def _active_dag_count(self) -> int:
        summaries = await store.list_summaries()
        return sum(1 for s in summaries if s["status"] in ("running", "pending"))

    async def mark_running(self, dag_run_id: str, node_id: str, worker_id: str) -> None:
        """worker 开始执行某节点时回调（经 API），把节点标记为 RUNNING。"""
        run = await store.get(dag_run_id)
        if run is None:
            return
        async with store.lock(run.id):
            node = run.nodes.get(node_id)
            if node and node.status == NodeStatus.DISPATCHED:
                import time
                node.status = NodeStatus.RUNNING
                node.started_at = time.time()
                node.worker_id = worker_id
                await event_bus.publish(OrchestrationEvent(
                    type=EventType.NODE_RUNNING, dag_run_id=run.id, node_id=node_id,
                    payload={"worker": worker_id},
                ))


orchestrator = Orchestrator()
