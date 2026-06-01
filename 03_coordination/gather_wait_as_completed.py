import asyncio
import random


async def fetch(label: str, delay: float) -> str:
    # 模拟一个异步请求，delay 表示这个请求需要等待多久。
    print(f"{label}: start ({delay:.2f}s)")
    await asyncio.sleep(delay)
    print(f"{label}: end")
    return f"{label} -> {delay:.2f}s"


async def demo_gather() -> None:
    print("\n=== gather ===")

    # gather 适合“并发执行多个任务，并在最后一次性拿到所有结果”。
    # 它返回的结果顺序与输入顺序一致，而不是完成顺序。
    results = await asyncio.gather(
        fetch("A", 1.2),
        fetch("B", 0.7),
        fetch("C", 1.0),
    )
    print("gather results:", results)


async def demo_wait() -> None:
    print("\n=== wait FIRST_COMPLETED ===")

    # 这里先显式创建 Task，因为 wait 更适合与“已经存在的任务集合”配合使用。
    tasks = {
        asyncio.create_task(fetch("D", 0.9)),
        asyncio.create_task(fetch("E", 1.4)),
        asyncio.create_task(fetch("F", 0.5)),
    }

    # FIRST_COMPLETED 表示：只要有任意一个任务完成，就立刻返回。
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    print(f"done={len(done)}, pending={len(pending)}")

    # 已完成任务可以直接读取结果。
    for task in done:
        print("first completed result:", task.result())

    # 对剩余未完成任务主动取消，避免它们继续后台执行。
    for task in pending:
        task.cancel()

    # 用 gather(..., return_exceptions=True) 等待取消真正落地，避免警告。
    await asyncio.gather(*pending, return_exceptions=True)
    print("pending tasks cancelled")


async def demo_as_completed() -> None:
    print("\n=== as_completed ===")

    # 这里随机生成几个耗时，模拟多个完成时间不同的任务。
    delays = [round(random.uniform(0.4, 1.3), 2) for _ in range(4)]
    coroutines = [fetch(f"job-{index}", delay) for index, delay in enumerate(delays, start=1)]

    # as_completed 会按照“谁先完成就先产出谁”的顺序返回 awaitable。
    for finished in asyncio.as_completed(coroutines):
        result = await finished
        print("streamed result:", result)


async def main() -> None:
    # 固定随机种子，保证每次运行的示例输出更稳定，方便学习。
    random.seed(42)
    await demo_gather()
    await demo_wait()
    await demo_as_completed()


if __name__ == "__main__":
    asyncio.run(main())
