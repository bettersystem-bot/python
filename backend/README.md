# Backend —— core service + worker

后端基于 **FastAPI + Redis Streams**，包含两个可独立运行的进程：

- **core service**：HTTP/WebSocket 服务 + 编排引擎（dag parser / executor / scheduler）。
- **worker**：常驻消费进程，从消息队列拉取任务并执行。

## 目录结构

```
backend/app/
├── main.py                 # FastAPI 入口（core service），lifespan 拉起引擎
├── config.py               # 全局配置（环境变量）
├── models/__init__.py      # 核心数据模型（DAG/Node/Task/Result/Event）★先读
├── gateway/__init__.py     # 智创网关中间件：认证 / 限流
├── api/
│   ├── routes.py           # 外部/内部 API + WebSocket
│   └── examples.py         # 内置示例 DAG
├── core/
│   ├── dag_parser.py       # 校验 + 拓扑/环检测
│   ├── dag_executor.py     # ★编排引擎（入度推进 + 消息队列解耦）
│   ├── scheduler.py        # 就绪节点 -> 投递队列
│   ├── queue.py            # Redis Streams 封装（消费组/ACK/认领）
│   ├── eventbus.py         # 进程内事件总线（fan-out 给 WebSocket）
│   └── store.py            # 运行态存储
├── workers/
│   ├── worker.py           # ★消费循环：拉取-执行-回传-ACK
│   ├── handlers.py         # 各节点类型的执行逻辑
│   └── callback.py         # callback service：可插拔后处理
└── observability/
    ├── logger.py / metrics.py / trace.py
```

## 本地运行（不使用 Docker）

需要本机有 Redis 与 Python 3.10+：

```bash
# 1) 启动 Redis（任选其一）
redis-server                 # 直接装的 redis
# 或： docker run -p 6379:6379 redis:7

# 2) 安装依赖
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3) 启动 core service
uvicorn app.main:app --reload --port 8000

# 4) 另开终端，启动 1~N 个 worker
python -m app.workers.worker
# 想让某 worker 只消费特定队列：
WORKER_QUEUES=gpu python -m app.workers.worker
```

打开 http://localhost:8000/docs 调 `POST /api/dags` 提交一张 DAG，或直接用前端。

## 关键环境变量

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |
| `MAX_INFLIGHT_PER_DAG` | `8` | 单图并发上限（背压） |
| `NODE_TIMEOUT_SECONDS` | `30` | 节点执行超时 |
| `NODE_MAX_RETRIES` | `2` | 节点失败重试次数 |
| `WORKER_CONCURRENCY` | `4` | 单 worker 并发任务数 |
| `WORKER_QUEUES` | 空(全部) | 该 worker 消费的节点类型，逗号分隔 |
| `CORE_API_BASE` | `http://localhost:8000` | worker 回调 core 的地址 |
| `ALLOW_ANONYMOUS` | `true` | 是否免认证（学习默认开） |
| `RATE_LIMIT_PER_MIN` | `120` | 网关限流阈值 |
