# 异步编排调度系统（Async Orchestrator）

> 一个用 **FastAPI + React + Redis Streams** 搭建的、可运行的「DAG 异步任务编排与调度」教学项目。
> 目标：学完之后真正掌握 Python 在 **异步编排（orchestration）** 与 **调度（scheduling）** 上的核心能力。

本项目对照了一张「后训练推理系统」架构图，把其中每一个框都落成了真实可运行的代码模块。
你可以一边读架构、一边读代码、一边在浏览器里点按钮提交 DAG，实时看到任务在多个 worker 之间被调度、执行、回传。

---

## 1. 这个项目到底在教什么？

很多人学 `asyncio` 停留在 `await asyncio.sleep()`、`gather` 这一层。
但真实系统里，异步的价值体现在 **编排（谁先谁后、谁依赖谁）** 和 **调度（把任务分发给谁、并发多少、失败怎么办）**。

本项目用一个完整的「DAG 任务编排平台」把这两件事讲透：

- **编排（Orchestration）**：一个任务由多个节点（Node）组成有向无环图（DAG）。
  节点之间有依赖关系（A 完成后 B、C 才能开始）。引擎负责按依赖拓扑、最大并发地把节点推进到完成。
- **调度（Scheduling）**：就绪的节点不会在引擎里直接执行，而是被投递到 **消息队列**（Redis Streams）。
  多个 **worker** 进程/协程从队列里拉取、执行、回传结果。引擎据此推进 DAG。

这正是「生产者-消费者 + 拓扑推进 + 消息队列解耦」的经典异步架构。

---

## 2. 架构总览（对照架构图）

```
                            ┌─────────────────────── core service (FastAPI) ───────────────────────┐
 业务侧            智创网关  │   外部 API / 内部 API                                                  │
 (前端 React) ──提交任务──▶ │  ┌──────────┐     ┌──────────────┐      ┌────────────────────────┐   │
                认证/限流   │  │dag parser│────▶│ dag executor │◀────▶│ callback service       │   │
                            │  │(校验/拓扑)│     │ (异步编排引擎)│      │ (允许自定义后处理)      │   │
                            │  └──────────┘     └──────┬───────┘      └────────────────────────┘   │
                            └────────────────────────┬─┴───────────────────────────────────────────┘
                                                     │ 把"就绪节点"作为消息投递
                              ┌──────────────────────▼───────────────────────┐
                              │   Redis Streams 消息队列 (队列A / B / C ...)   │   ← 按节点类型路由
                              └───┬───────────────┬───────────────┬──────────┘
                       拉取消费A  │      拉取消费B │      拉取消费C │
                              ┌───▼───┐       ┌───▼───┐       ┌───▼───┐
                              │worker1│       │worker2│       │worker3│   ← 训推下游(常驻)
                              └───┬───┘       └───┬───┘       └───┬───┘
                                  └───────────────┴────回传结果───┘
                                                     │
                              ┌──────────────────────▼──────────────────┐
                              │  EventBus → WebSocket 实时推送给前端       │
                              │  log / metrics / trace 可观测性           │
                              └──────────────────────────────────────────┘
```

| 架构图里的框        | 本项目对应模块                                   |
| ------------------- | ------------------------------------------------ |
| 业务侧              | `frontend/`（React 控制台）                      |
| 智创网关 认证/限流  | `backend/app/gateway/`                           |
| 外部/内部 API       | `backend/app/api/routes.py`                      |
| dag parser          | `backend/app/core/dag_parser.py`                 |
| dag executor        | `backend/app/core/dag_executor.py`（**核心**）   |
| 调度分发            | `backend/app/core/scheduler.py`                  |
| 消息队列(队列A/B/C) | `backend/app/core/queue.py`（Redis Streams 封装）|
| hamlet worker       | `backend/app/workers/worker.py`                  |
| callback service    | `backend/app/workers/callback.py`                |
| 业务 EventBus       | `backend/app/core/eventbus.py` + WebSocket       |
| log / metrics / trace | `backend/app/observability/`                   |

---

## 3. 一键运行（推荐 Docker）

```bash
# 在仓库根目录
docker compose up --build
```

启动后：

- 前端控制台： http://localhost:5173
- 后端 API 文档（Swagger）： http://localhost:8000/docs
- Redis： localhost:6379

在前端点击「提交示例 DAG」，即可看到任务被拆成多个节点、按依赖被调度到不同 worker、实时回传状态。

> 不想用 Docker？见 `backend/README.md` 与 `frontend/README.md` 的本地启动说明。

---

## 4. 推荐学习路线

按顺序读，每一步都能跑、能看到现象：

1. **模型层**：`backend/app/models/` —— 先搞清楚 DAG / Node / TaskRun / 事件 的数据结构。
2. **队列封装**：`backend/app/core/queue.py` —— Redis Streams 的消费组、ACK、重试是怎么回事。
3. **解析器**：`backend/app/core/dag_parser.py` —— 拓扑排序与环检测。
4. **编排引擎**：`backend/app/core/dag_executor.py` —— **本项目最核心**，反复读。
5. **调度器**：`backend/app/core/scheduler.py` —— 就绪节点如何路由进队列。
6. **worker**：`backend/app/workers/worker.py` —— 拉取-执行-ACK-回传的消费循环。
7. **可观测性**：`backend/app/observability/` —— 如何给异步系统加 log/metrics/trace。
8. **前端**：`frontend/src/` —— 如何用 WebSocket 把异步状态实时画出来。

每个模块的 README/注释都用中文写清了「为什么这么设计」「容易踩的坑」。

---

## 5. 你将真正掌握的异步编排能力

- 用 `asyncio` 构建 **拓扑驱动** 的执行引擎（in-degree 推进，而非简单 gather）
- 用 **消息队列** 解耦「编排」与「执行」，实现可水平扩展的 worker 调度
- **并发上限**（Semaphore）、**超时**（wait_for）、**取消**（cancel）、**重试** 的工程化处理
- 失败策略：fail-fast vs continue-on-error
- 用 **事件流 + WebSocket** 把异步系统的内部状态实时可视化
- 给异步系统加 **log / metrics / trace** 三件套
