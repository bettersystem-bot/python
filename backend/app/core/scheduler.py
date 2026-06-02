"""调度器（对应架构图里"提交/拉取消费队列"的投递侧）。

职责很纯粹：拿到一个"就绪节点"，把它打包成 TaskMessage 投递到对应类型的队列，
并更新状态、埋点、发事件。它**不决定**哪个节点该跑（那是编排引擎的事），
只负责"派发"这一个动作。这种"决策"与"派发"分离，是调度系统清晰的关键。

数据流动：派发时会把所有上游节点的 output 收集进 upstream_outputs，
作为本节点的输入上下文 —— 这就是"数据在 DAG 上流动"的实现。
"""
from __future__ import annotations

from app.config import settings
from app.core.eventbus import event_bus
from app.core.queue import queue
from app.models import (
    DagRun, EventType, NodeRun, NodeStatus, OrchestrationEvent, TaskMessage,
)
from app.observability.logger import get_logger
from app.observability.metrics import metrics

logger = get_logger("scheduler")


async def dispatch_node(run: DagRun, node: NodeRun) -> None:
    """把一个就绪节点派发到消息队列。"""
    # 收集上游产出作为输入上下文。
    upstream_outputs = {
        dep: run.nodes[dep].output
        for dep in node.depends_on
        if dep in run.nodes and run.nodes[dep].output is not None
    }
    node.attempt += 1
    task = TaskMessage(
        dag_run_id=run.id,
        node_id=node.id,
        node_type=node.type,
        name=node.name,
        params=node.params,
        upstream_outputs=upstream_outputs,
        attempt=node.attempt,
    )
    await queue.enqueue_task(task)

    node.status = NodeStatus.DISPATCHED
    metrics.incr("scheduler.dispatched")
    metrics.incr(f"scheduler.dispatched.{node.type.value}")
    logger.info(
        "dispatch dag=%s node=%s type=%s attempt=%d -> %s",
        run.id, node.id, node.type.value, node.attempt, settings.queue_name(node.type.value),
    )
    await event_bus.publish(OrchestrationEvent(
        type=EventType.NODE_DISPATCHED,
        dag_run_id=run.id,
        node_id=node.id,
        payload={"type": node.type.value, "attempt": node.attempt},
    ))
