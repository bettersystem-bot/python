"""全局配置。

集中管理：服务监听地址、Redis 连接、队列名、消费组、并发上限等。
所有可调参数都从环境变量读取，方便在 docker-compose 里覆盖。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    # ---- HTTP 服务 ----
    host: str = field(default_factory=lambda: _env("APP_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("APP_PORT", 8000))

    # ---- Redis ----
    redis_url: str = field(default_factory=lambda: _env("REDIS_URL", "redis://localhost:6379/0"))

    # ---- 消息队列 ----
    # 架构图里的"队列A/B/C"在本项目用"节点类型"来路由：
    # 不同 node.type 会被投递到不同的 stream，模拟不同算力池/服务的拉取消费。
    # stream 名形如:  orch:queue:cpu / orch:queue:io / orch:queue:gpu
    queue_prefix: str = field(default_factory=lambda: _env("QUEUE_PREFIX", "orch:queue"))
    consumer_group: str = field(default_factory=lambda: _env("CONSUMER_GROUP", "workers"))

    # 结果回传队列：worker 执行完把结果写回这里，调度器消费它来推进 DAG。
    result_stream: str = field(default_factory=lambda: _env("RESULT_STREAM", "orch:results"))

    # ---- 编排引擎 ----
    # 单个 DAG 内允许同时"在途"（已派发未完成）的节点上限，体现并发调度的背压控制。
    max_inflight_per_dag: int = field(default_factory=lambda: _env_int("MAX_INFLIGHT_PER_DAG", 8))
    # 节点执行超时（秒），超时则判定失败并按策略处理。
    node_timeout_seconds: int = field(default_factory=lambda: _env_int("NODE_TIMEOUT_SECONDS", 30))
    # 节点失败重试次数。
    node_max_retries: int = field(default_factory=lambda: _env_int("NODE_MAX_RETRIES", 2))

    # ---- worker ----
    # 单个 worker 进程内并发执行的协程数（从队列一次最多拉取多少条同时处理）。
    worker_concurrency: int = field(default_factory=lambda: _env_int("WORKER_CONCURRENCY", 4))
    # 这个 worker 负责消费哪些队列（逗号分隔的 node 类型）。空表示消费全部。
    worker_queues: str = field(default_factory=lambda: _env("WORKER_QUEUES", ""))

    def queue_name(self, node_type: str) -> str:
        """根据节点类型得到它应被投递到的 stream 名。"""
        return f"{self.queue_prefix}:{node_type}"


settings = Settings()
