# 18 asyncio 中的锁机制

## 这一章学什么

线程有线程锁，协程也有协程锁。

这一章会讲：

- `asyncio.Lock`
- `asyncio.Semaphore`
- 为什么协程虽然是单线程，也仍然可能有竞态条件

## 为什么单线程协程也需要锁

因为竞态不一定来自多线程，也可能来自“多个协程在 await 处分段交错”。

如果一个协程读到旧值后 `await` 暂停，另一个协程也读到同样的旧值，最后就可能出现丢失更新。

## asyncio 锁和 threading 锁不能混用

重要原则：

- 协程里用 `asyncio.Lock`
- 线程里用 `threading.Lock`
- 不要在事件循环里用阻塞锁长时间卡住线程

## 运行方式

```bash
python3.10 18_async_locks/async_lock_tools.py
```
