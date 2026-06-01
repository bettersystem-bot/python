import asyncio
import random


async def producer(queue: asyncio.Queue[int], count: int) -> None:
    for item in range(1, count + 1):
        await asyncio.sleep(0.1)
        print(f"producer: enqueue job {item}")
        await queue.put(item)


async def worker(name: str, queue: asyncio.Queue[int], limiter: asyncio.Semaphore) -> None:
    while True:
        item = await queue.get()
        if item == -1:
            queue.task_done()
            print(f"{name}: received stop signal")
            return

        async with limiter:
            delay = round(random.uniform(0.4, 1.0), 2)
            print(f"{name}: processing job {item} for {delay:.2f}s")
            await asyncio.sleep(delay)
            print(f"{name}: finished job {item}")

        queue.task_done()


async def main() -> None:
    random.seed(7)
    queue: asyncio.Queue[int] = asyncio.Queue()
    limiter = asyncio.Semaphore(2)
    worker_count = 3

    workers = [
        asyncio.create_task(worker(f"worker-{index}", queue, limiter))
        for index in range(1, worker_count + 1)
    ]

    await producer(queue, count=8)
    await queue.join()

    for _ in range(worker_count):
        await queue.put(-1)

    await asyncio.gather(*workers)
    print("pipeline complete")


if __name__ == "__main__":
    asyncio.run(main())
