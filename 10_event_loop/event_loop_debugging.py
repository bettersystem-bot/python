import asyncio
import time


async def heartbeat(label: str, ticks: int = 5) -> None:
    # heartbeat 就像“心跳灯”：如果它能稳定闪烁，说明事件循环还在正常运转。
    for index in range(ticks):
        print(f"{label}: heartbeat {index}")
        await asyncio.sleep(0.2)


async def inspect_tasks(stage: str) -> None:
    # current_task() 可以知道当前正在运行的是哪个 Task。
    current = asyncio.current_task()
    print(f"\n[{stage}] 当前任务: {current.get_name() if current else 'unknown'}")

    # all_tasks() 能看到当前事件循环里还没完成的任务。
    tasks = asyncio.all_tasks()
    for task in tasks:
        print(f"[{stage}] 存活任务: name={task.get_name()}, done={task.done()}")


async def blocking_mistake() -> None:
    print("\n=== 错误示范：在协程里直接阻塞 ===")
    print("即将 time.sleep(0.8)，这期间事件循环会被整个卡住")

    # 这是异步代码里的典型错误：time.sleep 会阻塞当前线程，也就是阻塞事件循环。
    time.sleep(0.8)

    print("阻塞结束，事件循环才有机会继续调度其他协程")


async def non_blocking_fix() -> None:
    print("\n=== 正确示范：把阻塞调用丢到线程 ===")

    # to_thread 会把阻塞函数放到线程中执行，让事件循环保持响应。
    await asyncio.to_thread(time.sleep, 0.8)
    print("阻塞工作在线程中结束，事件循环没有被长时间卡住")


async def main() -> None:
    loop = asyncio.get_running_loop()

    # 打开 debug 后，事件循环会提供更多诊断信息。
    loop.set_debug(True)
    loop.slow_callback_duration = 0.1
    print(f"事件循环类型: {type(loop).__name__}")

    await inspect_tasks("启动阶段")

    # 给任务命名是非常好的调试习惯，日志和诊断信息会更容易理解。
    heartbeat_task = asyncio.create_task(heartbeat("before-blocking"), name="heartbeat-before-blocking")
    blocking_task = asyncio.create_task(blocking_mistake(), name="blocking-mistake")
    await asyncio.gather(heartbeat_task, blocking_task)

    await inspect_tasks("阻塞示范后")

    heartbeat_task = asyncio.create_task(heartbeat("with-to-thread"), name="heartbeat-with-to-thread")
    fixed_task = asyncio.create_task(non_blocking_fix(), name="non-blocking-fix")
    await asyncio.gather(heartbeat_task, fixed_task)

    await inspect_tasks("结束阶段")


if __name__ == "__main__":
    asyncio.run(main())
