import asyncio
import time


async def worker(name: str, delay: float) -> str:
    print(f"{name}: started, need {delay:.1f}s")
    await asyncio.sleep(delay)
    print(f"{name}: finished")
    return f"{name} complete"


async def run_sequential() -> None:
    print("\n=== sequential ===")
    started = time.perf_counter()
    result1 = await worker("tea", 1.5)
    result2 = await worker("toast", 1.0)
    elapsed = time.perf_counter() - started
    print(f"results: {result1}, {result2}")
    print(f"sequential elapsed: {elapsed:.2f}s")


async def run_concurrent() -> None:
    print("\n=== concurrent with tasks ===")
    started = time.perf_counter()
    tea_task = asyncio.create_task(worker("tea", 1.5), name="tea-task")
    toast_task = asyncio.create_task(worker("toast", 1.0), name="toast-task")

    print(f"created: {tea_task.get_name()}, done={tea_task.done()}")
    print(f"created: {toast_task.get_name()}, done={toast_task.done()}")

    result1 = await tea_task
    result2 = await toast_task
    elapsed = time.perf_counter() - started
    print(f"results: {result1}, {result2}")
    print(f"concurrent elapsed: {elapsed:.2f}s")


async def main() -> None:
    await run_sequential()
    await run_concurrent()


if __name__ == "__main__":
    asyncio.run(main())
