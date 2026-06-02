"""API 路由（对应架构图的"外部 API / 内部 API"）。

- 外部 API（/api/*）：供前端业务侧调用 —— 提交 DAG、查询状态、列出运行、看示例、看指标/trace。
- 内部 API（/internal/*）：供 worker 回调 —— 通知"节点开始执行"。
- WebSocket（/ws/events）：把 EventBus 的事件实时推送给前端。

提交流程串起了整条链路：
  请求 -> (网关中间件已做认证/限流) -> dag_parser 校验 -> orchestrator.submit 派发 -> 返回 dag_run_id
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.api.examples import EXAMPLES
from app.core import dag_parser
from app.core.dag_executor import orchestrator
from app.core.eventbus import event_bus
from app.core.store import store
from app.models import DagSpec
from app.observability.logger import get_logger
from app.observability.metrics import metrics
from app.observability.trace import tracer

logger = get_logger("api")
router = APIRouter()


class SubmitResponse(BaseModel):
    dag_run_id: str
    summary: dict


# --------------------------------------------------------------------------- #
# 外部 API
# --------------------------------------------------------------------------- #
@router.post("/api/dags", response_model=SubmitResponse, tags=["external"])
async def submit_dag(spec: DagSpec) -> SubmitResponse:
    """提交一张 DAG 开始编排执行。"""
    try:
        run = dag_parser.parse(spec)  # 校验 + 环检测 + 构建运行态
    except dag_parser.DagValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await orchestrator.submit(run)
    return SubmitResponse(dag_run_id=run.id, summary=run.summary())


@router.get("/api/dags", tags=["external"])
async def list_dags() -> list[dict]:
    """列出所有 DAG 运行的汇总。"""
    return await store.list_summaries()


@router.get("/api/dags/{dag_run_id}", tags=["external"])
async def get_dag(dag_run_id: str) -> dict:
    """查询某个 DAG 运行的完整状态（含每个节点）。"""
    run = await store.get(dag_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="dag run 不存在")
    return run.model_dump(mode="json")


@router.get("/api/examples", tags=["external"])
async def list_examples() -> dict:
    """返回内置示例 DAG，供前端一键提交。"""
    return EXAMPLES


@router.get("/api/metrics", tags=["observability"])
async def get_metrics() -> dict:
    """返回指标快照（counters / gauges / timings）。"""
    return metrics.snapshot()


@router.get("/api/trace/{trace_id}", tags=["observability"])
async def get_trace(trace_id: str) -> dict:
    """返回某条 trace 的 span 列表（trace_id 即 dag_run_id）。"""
    return {"trace_id": trace_id, "spans": tracer.get_trace(trace_id)}


# --------------------------------------------------------------------------- #
# 内部 API（worker 回调）
# --------------------------------------------------------------------------- #
class NodeRunningPayload(BaseModel):
    dag_run_id: str
    node_id: str
    worker_id: str


@router.post("/internal/node-running", tags=["internal"])
async def node_running(p: NodeRunningPayload) -> dict:
    await orchestrator.mark_running(p.dag_run_id, p.node_id, p.worker_id)
    return {"ok": True}


# --------------------------------------------------------------------------- #
# WebSocket：实时事件推送
# --------------------------------------------------------------------------- #
@router.websocket("/ws/events")
async def ws_events(ws: WebSocket) -> None:
    """前端连上后，持续把编排事件推送过去。"""
    await ws.accept()
    logger.info("websocket client connected")
    try:
        async for event in event_bus.subscribe():
            await ws.send_json(event.model_dump(mode="json"))
    except WebSocketDisconnect:
        logger.info("websocket client disconnected")
    except Exception as e:  # noqa: BLE001
        logger.warning("websocket error: %s", e)
