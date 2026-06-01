import asyncio
import concurrent.futures
import time


def blocking_io_job(name: str, delay: float) -> str:
    # 这是一个阻塞 I/O 示例：它大部分时间都在 sleep，类似等待网络或磁盘。
    time.sleep(delay)
    return f"{name} done"


def cpu_job(size: int) -> int:
    # 这是一个 CPU 计算示例：它主要消耗 CPU，而不是等待外部 I/O。
    total = 0
    for number in range(size):
        total += number * number
    return total


async def async_io_job(name: str, delay: float) -> str:
    # 这是一个异步 I/O 示例：await sleep 时会主动让出事件循环。
    await asyncio.sleep(delay)
    return f"{name} done"


def demo_thread_pool_for_io() -> None:
    print("\n=== 线程池处理阻塞 I/O ===")
    started = time.perf_counter()

    # 线程池适合把多个阻塞 I/O 同时推进。
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(blocking_io_job, f"io-{index}", 0.5) for index in range(3)]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())

    print(f"线程池耗时: {time.perf_counter() - started:.2f}s")


async def demo_asyncio_for_io() -> None:
    print("\n=== asyncio 处理异步 I/O ===")
    started = time.perf_counter()

    # asyncio 适合所有任务都愿意用 await 主动让出执行权的场景。
    results = await asyncio.gather(
        async_io_job("async-1", 0.5),
        async_io_job("async-2", 0.5),
        async_io_job("async-3", 0.5),
    )
    print(results)
    print(f"asyncio 耗时: {time.perf_counter() - started:.2f}s")


def demo_process_pool_for_cpu() -> None:
    print("\n=== 进程池处理 CPU 计算 ===")
    started = time.perf_counter()

    # 进程池适合 CPU 密集型任务，因为多个进程可以更好地利用多核。
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(cpu_job, 300_000) for _ in range(2)]
        for future in concurrent.futures.as_completed(futures):
            print(f"计算结果后 6 位: {future.result() % 1_000_000}")

    print(f"进程池耗时: {time.perf_counter() - started:.2f}s")


async def main() -> None:
    demo_thread_pool_for_io()
    await demo_asyncio_for_io()
    demo_process_pool_for_cpu()


if __name__ == "__main__":
    asyncio.run(main())
