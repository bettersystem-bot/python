import asyncio


class UnsafeAsyncCounter:
    def __init__(self) -> None:
        self.value = 0

    async def increase(self) -> None:
        # 即使只有一个线程，await 也会让这个读-改-写过程被其他协程插入。
        current = self.value
        await asyncio.sleep(0)
        self.value = current + 1


class SafeAsyncCounter:
    def __init__(self) -> None:
        self.value = 0
        self.lock = asyncio.Lock()

    async def increase(self) -> None:
        # asyncio.Lock 要用 async with，因为获取锁本身可能需要等待。
        async with self.lock:
            current = self.value
            await asyncio.sleep(0)
            self.value = current + 1


async def run_counter(counter, task_count: int) -> int:
    await asyncio.gather(*(counter.increase() for _ in range(task_count)))
    return counter.value


async def limited_api_call(name: str, limiter: asyncio.Semaphore) -> None:
    # asyncio.Semaphore 用来限制协程并发数量，比如最多同时调用 2 个外部接口。
    async with limiter:
        print(f"{name}: 开始调用")
        await asyncio.sleep(0.2)
        print(f"{name}: 调用结束")


async def main() -> None:
    print("\n=== asyncio.Lock 保护协程共享状态 ===")
    task_count = 100

    unsafe = await run_counter(UnsafeAsyncCounter(), task_count)
    print(f"不加 asyncio.Lock: {unsafe}, 预期: {task_count}")

    safe = await run_counter(SafeAsyncCounter(), task_count)
    print(f"加 asyncio.Lock: {safe}, 预期: {task_count}")

    print("\n=== asyncio.Semaphore 限制协程并发 ===")
    limiter = asyncio.Semaphore(2)
    await asyncio.gather(*(limited_api_call(f"api-{index}", limiter) for index in range(5)))


if __name__ == "__main__":
    asyncio.run(main())
