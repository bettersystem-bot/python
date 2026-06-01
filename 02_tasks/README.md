# 02 任务调度

## 这一章学什么

协程只是“可以被调度的异步工作单元”。
真正让它独立运行、并发推进的，是 `Task`。

这一章会讲清楚：

- 为什么 `asyncio.create_task()` 很关键
- 顺序执行和并发执行的区别到底在哪里
- 事件循环是如何调度多个任务的
- 任务名和任务状态为什么对调试很有帮助

## 顺序执行 vs 并发执行

顺序执行：

```python
await job_a()
await job_b()
```

这里 `job_a()` 没结束之前，`job_b()` 根本不会开始。

并发执行：

```python
task_a = asyncio.create_task(job_a())
task_b = asyncio.create_task(job_b())
await task_a
await task_b
```

这里两个任务会都被交给事件循环调度，只要其中一个在等待，另一个就有机会继续推进。

## `create_task()` 的作用

`await some_coroutine()` 的意思是：“我就在这里等它执行完。”

`asyncio.create_task(some_coroutine())` 的意思是：“把这段协程包装成一个事件循环可以独立调度的任务。”

这是从“异步调用”迈向“异步并发”的关键一步。

## 运行方式

```bash
python3.10 02_tasks/tasks_lifecycle.py
```

## 观察重点

这个示例分成两段：

- 第一段是顺序执行
- 第二段是并发执行

你要重点比较：

- 总耗时有没有变化
- 输出顺序有没有交错
- 为什么任务创建后 `done()` 一开始通常是 `False`

## 练习建议

- 再增加一个任务
- 把一个任务改得特别慢
- 在等待前后打印任务状态
- 给任务起更有业务意义的名字
