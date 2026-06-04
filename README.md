# Python 3.10 异步编程学习路线

这个仓库是一套从零开始、按步骤推进的 `asyncio` 学习材料，目标版本固定为 `Python 3.10`。

## 学习目标

不直接堆高级概念，而是按照“先理解最小单位，再理解调度，再理解协作，再理解工程模式”的顺序学习。

每个阶段都包含两部分：

- `README.md`：详细讲解核心概念、使用场景、观察重点、练习建议
- `.py` 示例：可以直接运行，帮助你把概念和输出行为对应起来

## 学习顺序

1. `01_coroutines`：理解 `async def`、`await`、协程对象和事件循环
2. `02_tasks`：理解任务调度、顺序执行与并发执行的区别
3. `03_coordination`：掌握 `gather`、`wait`、`as_completed`
4. `04_control_flow`：掌握取消、超时、清理逻辑
5. `05_patterns`：学习 `Queue` 和 `Semaphore` 这些常见异步模式
6. `06_advanced`：学习异步迭代器、异步生成器、异步上下文管理器
7. `07_bridge`：学习异步代码和阻塞代码之间如何衔接
8. `08_project`：用一个小型项目把前面的知识串起来
9. `09_exceptions`：学习并发任务中的异常传播、失败收集和关键任务保护
10. `10_event_loop`：从事件循环视角理解卡顿、任务状态和调试方法
11. `11_streams`：学习异步 TCP 流式 I/O、`StreamReader`、`StreamWriter` 和背压
12. `12_testing`：学习如何用标准库测试异步函数、异常和超时

## 为什么固定 Python 3.10

这套材料明确以 `Python 3.10` 为准，原因有三个：

- 保证讲解和示例使用的是同一套语义
- 避免混入 `Python 3.11+` 的新特性，导致学习边界不清晰
- 真实工作里经常需要按指定版本开发，提前建立版本意识很重要

例如，这里不会使用 `asyncio.TaskGroup`，因为它是 `Python 3.11` 才引入的。

## 推荐使用方式

建议每一章都按这个顺序来：

1. 先读目录下的 `README.md`
2. 猜一下程序会怎么执行
3. 再运行示例代码
4. 修改几个参数继续观察
5. 自己写一个变体加深理解

## 推荐节奏

- 第 1 天：`01_coroutines` + `02_tasks`
- 第 2 天：`03_coordination`
- 第 3 天：`04_control_flow`
- 第 4 天：`05_patterns`
- 第 5 天：`06_advanced`
- 第 6 天：`07_bridge`
- 第 7 天：`08_project`
- 第 8 天：`09_exceptions`
- 第 9 天：`10_event_loop`
- 第 10 天：`11_streams`
- 第 11 天：`12_testing`

## 运行示例

如果你本机已经安装 `Python 3.10`，建议直接这样运行：

```bash
python3.10 01_coroutines/basic_coroutines.py
python3.10 02_tasks/tasks_lifecycle.py
python3.10 03_coordination/gather_wait_as_completed.py
python3.10 04_control_flow/cancel_timeout.py
python3.10 05_patterns/queue_pipeline.py
python3.10 06_advanced/async_iterators_context.py
python3.10 07_bridge/to_thread_bridge.py
python3.10 08_project/mini_crawler.py
python3.10 09_exceptions/exception_strategies.py
python3.10 10_event_loop/event_loop_debugging.py
python3.10 11_streams/stream_echo_demo.py
python3.10 -m unittest 12_testing/test_async_service.py
```

## 知识地图

如果把异步编程想象成开一家高效餐厅：

- `Coroutine` 是一张可以暂停和恢复的订单
- `Task` 是已经交给大厅经理排队执行的订单
- `Event Loop` 是大厅经理，决定谁现在继续推进
- `await` 是订单主动让出服务员，等待后厨、外卖员或收银台返回
- `gather` / `wait` / `as_completed` 是不同的取餐策略
- `Queue` 是待处理订单池
- `Semaphore` 是厨房同时能处理的炉灶数量
- `Timeout` 和 `Cancellation` 是超时退单和主动取消
- `Stream` 是源源不断流入流出的水管
- `Testing` 是开店前的试营业，提前验证慢请求、失败请求和边界情况

## 学习异步时最重要的三个问题

每次看异步代码，都主动问自己：

- 现在是谁在运行？
- 现在是谁在等待？
- 等待结束以后，谁会把这个协程继续调度回来？

如果你越来越能清楚回答这三个问题，说明你对异步编程的理解正在变扎实。

## 延伸学习：Go Kitex 框架

如果你已经完成 Python 异步编程路线，想继续学习 Go 微服务 RPC，可以阅读新增的 Kitex 教学材料：

- [`go-kitex/README.md`](go-kitex/README.md)：Kitex 学习路线总览
- [`go-kitex/examples/hello_thrift/echo.thrift`](go-kitex/examples/hello_thrift/echo.thrift)：最小 Thrift IDL 示例

这部分材料重点讲清楚 `IDL → 代码生成 → Server Handler → Client 调用 → 服务治理 → 排障` 的完整链路。
