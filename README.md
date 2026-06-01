# Python 3.10 异步编程学习路线

这个仓库是一套从零开始、按步骤推进的 `asyncio` 学习材料，目标版本固定为 `Python 3.10`。

## 学习目标

不直接堆高级概念，而是按照“先理解最小单位，再理解调度，再理解协作，再理解工程模式”的顺序学习。

每个阶段都包含两部分：

- `README.md`：详细讲解核心概念、使用场景、观察重点、练习建议
- `.py` 示例：可以直接运行，帮助你把概念和输出行为对应起来

## 专题入口

- `01` 到 `12`：Python 3.10 异步编程学习路线
- `13` 到 `18`：Python 并发机制与锁机制学习路线
- `CONCURRENCY_LOCKS_GUIDE.md`：并发与锁专题总览
- `19` 到 `26`：Python 网络编程学习路线
- `NETWORK_PROGRAMMING_GUIDE.md`：网络编程专题总览

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
13. `13_concurrency_overview`：建立并发、并行、异步、线程、进程、协程的全局地图
14. `14_threads_and_gil`：理解线程、GIL、竞态条件，以及为什么 GIL 不等于线程安全
15. `15_thread_locks`：学习 `Lock`、`RLock`、`Semaphore`
16. `16_conditions_events`：学习 `Event`、`Condition`、`Queue`
17. `17_processes`：学习多进程并行和进程间通信
18. `18_async_locks`：学习 `asyncio.Lock`、`asyncio.Semaphore` 和协程同步
19. `19_network_overview`：理解 IP、端口、协议、socket、DNS 和字节编码
20. `20_tcp_socket`：用原生 socket 编写 TCP echo server/client
21. `21_udp_socket`：理解 UDP 无连接通信和数据报
22. `22_http_basics`：用标准库理解 HTTP 请求、响应和本地 HTTP 服务
23. `23_framing_timeouts`：理解 TCP 粘包/拆包、消息边界和超时
24. `24_concurrent_servers`：学习并发 TCP 服务端和 `socketserver`
25. `25_selectors_nonblocking`：学习非阻塞 I/O、`selectors` 和事件驱动
26. `26_asyncio_networking`：用 `asyncio` 编写异步 TCP 网络程序

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
python3.10 13_concurrency_overview/concurrency_map.py
python3.10 14_threads_and_gil/thread_race_demo.py
python3.10 15_thread_locks/thread_lock_tools.py
python3.10 16_conditions_events/thread_coordination.py
python3.10 17_processes/multiprocessing_basics.py
python3.10 18_async_locks/async_lock_tools.py
python3.10 19_network_overview/network_lookup.py
python3.10 20_tcp_socket/tcp_echo_demo.py
python3.10 21_udp_socket/udp_echo_demo.py
python3.10 22_http_basics/http_server_client_demo.py
python3.10 23_framing_timeouts/length_prefixed_protocol.py
python3.10 24_concurrent_servers/threading_tcp_server.py
python3.10 25_selectors_nonblocking/selectors_demo.py
python3.10 26_asyncio_networking/asyncio_tcp_chat.py
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
