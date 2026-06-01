import asyncio
import random


async def producer(queue: asyncio.Queue[int], count: int) -> None:
    # 生产者负责不断往队列里放任务。
    for item in range(1, count + 1):
        await asyncio.sleep(0.1)
        print(f"producer: enqueue job {item}")
        await queue.put(item)


async def worker(name: str, queue: asyncio.Queue[int], limiter: asyncio.Semaphore) -> None:
    # worker 持续从队列取任务，直到收到停止信号。
    while True:
        item = await queue.get()

        # -1 被当作哨兵值，表示“没有更多正常任务了，可以退出”。
        if item == -1:
            queue.task_done()
            print(f"{name}: received stop signal")
            return

        # semaphore 控制真正进入“处理区”的并发数量。
        async with limiter:
            delay = round(random.uniform(0.4, 1.0), 2)
            print(f"{name}: processing job {item} for {delay:.2f}s")
            await asyncio.sleep(delay)
            print(f"{name}: finished job {item}")

        # 每取出一个队列元素，都必须对应调用一次 task_done()。
        queue.task_done()


async def main() -> None:
    random.seed(7)

    # Queue 用来承载待处理任务。
    queue: asyncio.Queue[int] = asyncio.Queue()

    # 虽然有 3 个 worker，但这里只允许最多 2 个同时进入关键处理区。
    limiter = asyncio.Semaphore(2)
    worker_count = 3

    # 先启动多个 worker，让它们在后台等待任务到来。
    workers = [
        asyncio.create_task(worker(f"worker-{index}", queue, limiter))
        for index in range(1, worker_count + 1)
    ]

    # 生产所有任务。
    await producer(queue, count=8)

    # 等待队列里的正常任务都被处理完成。
    await queue.join()

    # 给每个 worker 发送一个停止信号，保证它们都能优雅退出。
    for _ in range(worker_count):
        await queue.put(-1)

    # 等待所有 worker 真正结束。
    await asyncio.gather(*workers)
    print("pipeline complete")


if __name__ == "__main__":
    asyncio.run(main())
