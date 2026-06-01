import asyncio
import time


async def worker(name: str, delay: float) -> str:
    # 这个 worker 用来模拟一段会等待的异步工作。
    print(f"{name}: started, need {delay:.1f}s")

    # 模拟 I/O 等待。等待期间事件循环可以切换去执行别的任务。
    await asyncio.sleep(delay)

    print(f"{name}: finished")
    return f"{name} complete"


async def run_sequential() -> None:
    print("\n=== sequential ===")
    started = time.perf_counter()

    # 顺序 await：第二个任务必须等第一个任务彻底结束后才开始。
    result1 = await worker("tea", 1.5)
    result2 = await worker("toast", 1.0)

    elapsed = time.perf_counter() - started
    print(f"results: {result1}, {result2}")
    print(f"sequential elapsed: {elapsed:.2f}s")


async def run_concurrent() -> None:
    print("\n=== concurrent with tasks ===")
    started = time.perf_counter()

    # create_task 会把协程包装成 Task，并立刻交给事件循环调度。
    tea_task = asyncio.create_task(worker("tea", 1.5), name="tea-task")
    toast_task = asyncio.create_task(worker("toast", 1.0), name="toast-task")

    # 刚创建完成时，任务通常还没结束，所以 done() 一般是 False。
    print(f"created: {tea_task.get_name()}, done={tea_task.done()}")
    print(f"created: {toast_task.get_name()}, done={toast_task.done()}")

    # 虽然这里还是逐个 await，但两个任务已经提前被调度，因此总体是并发推进的。
    result1 = await tea_task
    result2 = await toast_task

    elapsed = time.perf_counter() - started
    print(f"results: {result1}, {result2}")
    print(f"concurrent elapsed: {elapsed:.2f}s")


async def main() -> None:
    # 先运行顺序版本，再运行并发版本，便于直接对比执行差异。
    await run_sequential()
    await run_concurrent()


if __name__ == "__main__":
    asyncio.run(main())
