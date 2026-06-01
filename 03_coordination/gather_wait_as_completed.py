import asyncio
import random


async def fetch(label: str, delay: float) -> str:
    print(f"{label}: start ({delay:.2f}s)")
    await asyncio.sleep(delay)
    print(f"{label}: end")
    return f"{label} -> {delay:.2f}s"


async def demo_gather() -> None:
    print("\n=== gather ===")
    results = await asyncio.gather(
        fetch("A", 1.2),
        fetch("B", 0.7),
        fetch("C", 1.0),
    )
    print("gather results:", results)


async def demo_wait() -> None:
    print("\n=== wait FIRST_COMPLETED ===")
    tasks = {
        asyncio.create_task(fetch("D", 0.9)),
        asyncio.create_task(fetch("E", 1.4)),
        asyncio.create_task(fetch("F", 0.5)),
    }
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    print(f"done={len(done)}, pending={len(pending)}")
    for task in done:
        print("first completed result:", task.result())
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)
    print("pending tasks cancelled")


async def demo_as_completed() -> None:
    print("\n=== as_completed ===")
    delays = [round(random.uniform(0.4, 1.3), 2) for _ in range(4)]
    coroutines = [fetch(f"job-{index}", delay) for index, delay in enumerate(delays, start=1)]
    for finished in asyncio.as_completed(coroutines):
        result = await finished
        print("streamed result:", result)


async def main() -> None:
    random.seed(42)
    await demo_gather()
    await demo_wait()
    await demo_as_completed()


if __name__ == "__main__":
    asyncio.run(main())
