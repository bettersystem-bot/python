# Python 并发机制与锁机制学习总览

这个专题接在异步编程专题之后，目标是把 Python 中常见的并发模型和同步工具讲清楚。

## 先区分三个词

很多人会把并发、并行、异步混在一起，但它们不是一回事。

- 并发：同时处理多件事，但不一定真的同一时刻执行
- 并行：多件事真的在同一时刻运行，通常依赖多个 CPU 核心
- 异步：遇到等待时主动让出执行权，让别的任务先推进

一个形象比喻：

- 并发像一个厨师同时照看三口锅，来回切换
- 并行像三个厨师各自负责一口锅
- 异步像厨师把菜放进烤箱后，不傻等，先去切菜

## Python 里主要有四类并发方案

1. `threading`：线程并发，适合 I/O 密集型任务
2. `multiprocessing`：多进程并行，适合 CPU 密集型任务
3. `asyncio`：协作式异步并发，适合大量 I/O 等待
4. `concurrent.futures`：线程池和进程池的统一抽象

## 为什么需要锁

并发程序的核心风险是：多个执行单元同时读写同一份共享状态。

如果没有保护，可能出现：

- 计数器少加了
- 列表状态不一致
- 两个任务同时修改同一个资源
- 一个线程看到另一个线程改到一半的数据

锁的目标不是让程序更快，而是让共享状态保持正确。

## 学习顺序

1. `13_concurrency_overview`：建立并发、并行、异步、GIL 的整体地图
2. `14_threads_and_gil`：理解线程并发、GIL、竞态条件
3. `15_thread_locks`：学习 `Lock`、`RLock`、`Semaphore`
4. `16_conditions_events`：学习 `Event`、`Condition`、`Queue`
5. `17_processes`：学习多进程并行和进程间通信
6. `18_async_locks`：学习 `asyncio.Lock`、`asyncio.Semaphore` 与协程同步

## 最重要的判断方法

遇到一个并发问题，先问这几个问题：

- 任务主要是在等 I/O，还是在算 CPU？
- 有没有共享可变状态？
- 共享状态是否必须被多个线程或协程同时修改？
- 能不能用队列传递消息，避免共享状态？
- 如果必须共享，应该用哪种锁或同步工具？

## 一个实用选择表

| 场景 | 推荐方案 |
| --- | --- |
| 大量网络请求 | `asyncio` 或线程池 |
| 阻塞 I/O 库 | `threading` 或 `asyncio.to_thread` |
| CPU 密集计算 | `multiprocessing` 或进程池 |
| 多线程共享计数器 | `threading.Lock` |
| 同一线程需要重复进入同一把锁 | `threading.RLock` |
| 限制并发数量 | `Semaphore` |
| 等待某个状态发生 | `Event` 或 `Condition` |
| 生产者消费者 | `queue.Queue` 或 `asyncio.Queue` |
| 协程共享状态 | `asyncio.Lock` |
