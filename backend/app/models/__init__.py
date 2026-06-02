"""数据模型层。

这里定义贯穿整个系统的核心结构，建议**最先阅读本文件**：

- NodeType / NodeStatus / DagStatus：枚举，定义节点种类与状态机。
- NodeSpec：用户提交的"一个节点的定义"（做什么、依赖谁、参数）。
- DagSpec：用户提交的"一整张图"（节点列表）。
- TaskMessage：编排引擎投递给消息队列、worker 拉取消费的"任务消息"。
- ResultMessage：worker 执行完回传给引擎的"结果消息"。
- NodeRun / DagRun：运行态对象，记录每个节点/整张图的实时状态。
- OrchestrationEvent：内部事件，经 EventBus 推送到前端做实时可视化。

设计要点：
1. "Spec"（用户输入，静态）与 "Run"（运行态，动态）严格分离。
2. 节点之间用 `depends_on` 表达依赖，引擎据此做拓扑推进。
3. 节点的产出 `output` 会作为下游节点的输入上下文，体现"数据在 DAG 上流动"。
"""
from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------- #
# 枚举
# --------------------------------------------------------------------------- #
class NodeType(str, Enum):
    """节点类型 —— 同时决定它被路由到哪个消费队列（架构图的队列A/B/C）。

    这里用三种典型负载来演示"不同任务派发给不同算力池"：
    - CPU: 计算密集型（模拟特征处理）
    - IO:  IO 密集型（模拟下载/读写）
    - GPU: 推理型（模拟模型推理，耗时较长）
    """
    CPU = "cpu"
    IO = "io"
    GPU = "gpu"


class NodeStatus(str, Enum):
    PENDING = "pending"        # 还有上游未完成，未就绪
    READY = "ready"            # 依赖已满足，等待被调度
    DISPATCHED = "dispatched"  # 已投递到消息队列，等待 worker 拉取
    RUNNING = "running"        # worker 正在执行
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"        # 因上游失败而被跳过（fail-fast 之外的节点）


class DagStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class FailurePolicy(str, Enum):
    """整张图的失败策略。"""
    FAIL_FAST = "fail_fast"            # 任一节点失败立即终止其余调度
    CONTINUE = "continue_on_error"     # 失败节点的下游跳过，其余分支继续


# --------------------------------------------------------------------------- #
# Spec：用户提交的静态定义
# --------------------------------------------------------------------------- #
class NodeSpec(BaseModel):
    id: str = Field(..., description="节点在图内唯一 id")
    name: str = Field("", description="可读名称")
    type: NodeType = Field(NodeType.CPU, description="节点类型，决定路由队列")
    depends_on: list[str] = Field(default_factory=list, description="依赖的上游节点 id 列表")
    # params 是给 handler 的业务参数；演示里我们用 work_ms 控制模拟耗时、fail 控制是否故意失败。
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def default_name(cls, v: str, info: Any) -> str:
        return v or info.data.get("id", "")


class DagSpec(BaseModel):
    name: str = Field("untitled-dag", description="DAG 名称")
    failure_policy: FailurePolicy = Field(FailurePolicy.FAIL_FAST)
    nodes: list[NodeSpec] = Field(..., min_length=1)


# --------------------------------------------------------------------------- #
# 消息：在引擎 <-> 队列 <-> worker 之间流转
# --------------------------------------------------------------------------- #
class TaskMessage(BaseModel):
    """引擎投递给消息队列、worker 拉取消费的任务消息。"""
    dag_run_id: str
    node_id: str
    node_type: NodeType
    name: str
    params: dict[str, Any] = Field(default_factory=dict)
    # 上游节点的产出汇总，作为本节点的输入上下文。
    upstream_outputs: dict[str, Any] = Field(default_factory=dict)
    attempt: int = 1
    enqueued_at: float = Field(default_factory=time.time)


class ResultMessage(BaseModel):
    """worker 执行完回传给引擎的结果消息。"""
    dag_run_id: str
    node_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    worker_id: str = ""
    attempt: int = 1
    duration_ms: float = 0.0
    finished_at: float = Field(default_factory=time.time)


# --------------------------------------------------------------------------- #
# Run：运行态
# --------------------------------------------------------------------------- #
class NodeRun(BaseModel):
    id: str
    name: str
    type: NodeType
    depends_on: list[str]
    params: dict[str, Any] = Field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    attempt: int = 0
    output: Any = None
    error: Optional[str] = None
    worker_id: str = ""
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


class DagRun(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "untitled-dag"
    failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST
    status: DagStatus = DagStatus.PENDING
    nodes: dict[str, NodeRun] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    finished_at: Optional[float] = None

    def summary(self) -> dict[str, Any]:
        """给前端用的轻量汇总。"""
        counts: dict[str, int] = {}
        for n in self.nodes.values():
            counts[n.status.value] = counts.get(n.status.value, 0) + 1
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "total": len(self.nodes),
            "counts": counts,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }


# --------------------------------------------------------------------------- #
# 事件：经 EventBus 实时推送到前端
# --------------------------------------------------------------------------- #
class EventType(str, Enum):
    DAG_CREATED = "dag_created"
    DAG_FINISHED = "dag_finished"
    NODE_READY = "node_ready"
    NODE_DISPATCHED = "node_dispatched"
    NODE_RUNNING = "node_running"
    NODE_SUCCEEDED = "node_succeeded"
    NODE_FAILED = "node_failed"
    NODE_SKIPPED = "node_skipped"
    NODE_RETRY = "node_retry"


class OrchestrationEvent(BaseModel):
    type: EventType
    dag_run_id: str
    node_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)
    ts: float = Field(default_factory=time.time)
