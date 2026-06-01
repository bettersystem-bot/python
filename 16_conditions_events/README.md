# 16 Event、Condition 与 Queue

## 这一章学什么

锁负责“互斥”，但并发程序还经常需要“等待某个条件发生”。

这一章会讲三个工具：

- `Event`：一个简单的开关信号
- `Condition`：等待更复杂的状态条件
- `queue.Queue`：线程间安全传递任务

## Event

`Event` 像一个开关灯。

- `wait()`：等灯亮
- `set()`：把灯打开
- `clear()`：把灯关掉

## Condition

`Condition` 像一个带通知机制的等候室。

线程可以在条件不满足时等待，另一个线程改变状态后通知它们继续检查。

## Queue

`Queue` 是线程并发里最推荐的通信方式之一。

因为它能减少共享状态，让线程通过“传消息”协作。

## 运行方式

```bash
python3.10 16_conditions_events/thread_coordination.py
```
