"""消息队列封装（基于 Redis Streams）。

对应架构图里的"消息队列（队列A/B/C）"。这是本项目实现"调度解耦"的关键：
编排引擎只负责把"就绪节点"作为消息投递进队列，worker 自己从队列拉取消费。
两者通过队列解耦，worker 可以任意水平扩展。

为什么用 Redis Streams 而不是 List？
- Streams 自带 **消费组（consumer group）**：多个 worker 加入同一个组，消息只会被组内一个 worker 拿到（竞争消费），天然实现负载均衡。
- 拉取的消息进入 **PEL（Pending Entries List）**，必须显式 XACK 才算处理完成。
  worker 崩溃没 ACK 的消息可被 XAUTOCLAIM 重新认领，实现 **at-least-once** 投递与故障重试。
- XREADGROUP 的 BLOCK 参数支持长轮询阻塞读，配合 redis.asyncio 完全非阻塞，契合 asyncio。

核心命令对照：
  XADD        生产消息
  XGROUP CREATE  创建消费组
  XREADGROUP  消费组阻塞读（拉取 + 进入 PEL）
  XACK        确认处理完成（移出 PEL）
  XAUTOCLAIM  认领超时未 ACK 的消息（故障转移）
"""
from __future__ import annotations

import asyncio
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings
from app.models import ResultMessage, TaskMessage
from app.observability.logger import get_logger

logger = get_logger("queue")

# 消息体放在 stream 字段 "data" 里，存 JSON 字符串。
_FIELD = "data"


class RedisStreamQueue:
    """对 Redis Streams 的薄封装，提供任务队列与结果队列两类操作。"""

    def __init__(self, redis_url: Optional[str] = None) -> None:
        self._url = redis_url or settings.redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._ensured_groups: set[str] = set()

    async def connect(self) -> None:
        if self._redis is None:
            self._redis = aioredis.from_url(self._url, decode_responses=True)
            await self._redis.ping()
            logger.info("connected to redis: %s", self._url)

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    @property
    def redis(self) -> aioredis.Redis:
        if self._redis is None:
            raise RuntimeError("queue not connected; call connect() first")
        return self._redis

    # ------------------------------------------------------------------ #
    # 消费组管理
    # ------------------------------------------------------------------ #
    async def ensure_group(self, stream: str, group: Optional[str] = None) -> None:
        """幂等地创建消费组。已存在则忽略 BUSYGROUP 错误。

        mkstream=True：stream 不存在时一并创建，避免 worker 先于生产者启动时报错。
        id="0"：从头开始消费（演示更直观）；生产中常用 "$" 表示只消费新消息。
        """
        group = group or settings.consumer_group
        key = f"{stream}:{group}"
        if key in self._ensured_groups:
            return
        try:
            await self.redis.xgroup_create(name=stream, groupname=group, id="0", mkstream=True)
            logger.info("created consumer group %s on stream %s", group, stream)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
        self._ensured_groups.add(key)

    # ------------------------------------------------------------------ #
    # 生产：投递任务 / 回传结果
    # ------------------------------------------------------------------ #
    async def enqueue_task(self, task: TaskMessage) -> str:
        """把一个任务投递到它对应类型的队列（XADD）。"""
        stream = settings.queue_name(task.node_type.value)
        msg_id = await self.redis.xadd(stream, {_FIELD: task.model_dump_json()})
        logger.debug("enqueued task node=%s -> %s id=%s", task.node_id, stream, msg_id)
        return msg_id

    async def publish_result(self, result: ResultMessage) -> str:
        """worker 把执行结果回传到结果队列（XADD）。"""
        return await self.redis.xadd(settings.result_stream, {_FIELD: result.model_dump_json()})

    # ------------------------------------------------------------------ #
    # 消费：worker 拉取任务 / 调度器拉取结果
    # ------------------------------------------------------------------ #
    async def consume_tasks(
        self,
        streams: list[str],
        consumer: str,
        count: int,
        block_ms: int = 2000,
        group: Optional[str] = None,
    ) -> list[tuple[str, str, TaskMessage]]:
        """worker 用：从多个任务队列里阻塞拉取一批任务。

        返回 (stream, message_id, TaskMessage) 列表；message_id 用于之后 XACK。
        """
        group = group or settings.consumer_group
        for s in streams:
            await self.ensure_group(s, group)
        # ">" 表示只读还没分给本消费者的新消息。
        stream_keys = {s: ">" for s in streams}
        resp = await self.redis.xreadgroup(
            groupname=group, consumername=consumer,
            streams=stream_keys, count=count, block=block_ms,
        )
        out: list[tuple[str, str, TaskMessage]] = []
        for stream, entries in resp or []:
            for msg_id, fields in entries:
                task = TaskMessage.model_validate_json(fields[_FIELD])
                out.append((stream, msg_id, task))
        return out

    async def ack_task(self, stream: str, msg_id: str, group: Optional[str] = None) -> None:
        """确认任务处理完成，移出 PEL。"""
        group = group or settings.consumer_group
        await self.redis.xack(stream, group, msg_id)

    async def consume_results(
        self,
        consumer: str,
        count: int,
        block_ms: int = 2000,
        group: Optional[str] = None,
    ) -> list[tuple[str, ResultMessage]]:
        """调度器用：从结果队列拉取 worker 回传的结果，用于推进 DAG。"""
        group = group or settings.consumer_group
        await self.ensure_group(settings.result_stream, group)
        resp = await self.redis.xreadgroup(
            groupname=group, consumername=consumer,
            streams={settings.result_stream: ">"}, count=count, block=block_ms,
        )
        out: list[tuple[str, ResultMessage]] = []
        for _stream, entries in resp or []:
            for msg_id, fields in entries:
                out.append((msg_id, ResultMessage.model_validate_json(fields[_FIELD])))
        return out

    async def ack_result(self, msg_id: str, group: Optional[str] = None) -> None:
        group = group or settings.consumer_group
        await self.redis.xack(settings.result_stream, group, msg_id)

    # ------------------------------------------------------------------ #
    # 故障恢复：认领超时未 ACK 的消息（演示 at-least-once）
    # ------------------------------------------------------------------ #
    async def claim_stale_tasks(
        self,
        stream: str,
        consumer: str,
        min_idle_ms: int,
        count: int = 16,
        group: Optional[str] = None,
    ) -> list[tuple[str, str, TaskMessage]]:
        """认领 PEL 中空闲超过 min_idle_ms 的消息（原属于已崩溃 worker）。"""
        group = group or settings.consumer_group
        await self.ensure_group(stream, group)
        _next, entries, _deleted = await self.redis.xautoclaim(
            name=stream, groupname=group, consumername=consumer,
            min_idle_time=min_idle_ms, start_id="0-0", count=count,
        )
        out: list[tuple[str, str, TaskMessage]] = []
        for msg_id, fields in entries:
            if fields and _FIELD in fields:
                out.append((stream, msg_id, TaskMessage.model_validate_json(fields[_FIELD])))
        return out


# 全局单例。
queue = RedisStreamQueue()
