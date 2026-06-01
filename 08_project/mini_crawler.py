import asyncio
import random
from dataclasses import dataclass


@dataclass
class CrawlResult:
    # 用数据类保存抓取结果，便于后续统一汇总输出。
    url: str
    status: str
    duration: float
    detail: str


async def fetch(url: str, limiter: asyncio.Semaphore) -> CrawlResult:
    # semaphore 控制同一时刻最多有多少个抓取动作真正执行。
    async with limiter:
        delay = round(random.uniform(0.4, 1.4), 2)
        print(f"fetch start: {url} (delay={delay:.2f}s)")

        # 用 sleep 模拟网络 I/O 等待。
        await asyncio.sleep(delay)

        # 人工制造一个失败分支，演示并发场景下如何保留错误结果。
        if "fail" in url:
            raise RuntimeError(f"simulated fetch failure for {url}")

        print(f"fetch done: {url}")
        return CrawlResult(url=url, status="ok", duration=delay, detail="content-length=demo")


async def safe_fetch(url: str, limiter: asyncio.Semaphore) -> CrawlResult:
    # 这个包装层的目的是：把异常也转成统一结果，而不是让单个任务直接打断全局流程。
    try:
        return await fetch(url, limiter)
    except Exception as exc:
        return CrawlResult(url=url, status="error", duration=0.0, detail=str(exc))


async def main() -> None:
    random.seed(21)

    # 输入列表可以理解成待抓取的 URL 队列。
    urls = [
        "https://example.com/home",
        "https://example.com/profile",
        "https://example.com/fail-report",
        "https://example.com/feed",
        "https://example.com/settings",
    ]

    # 最多允许两个抓取任务同时进入 fetch 的关键区。
    limiter = asyncio.Semaphore(2)

    # 先把所有抓取任务都启动起来，让它们交给事件循环统一调度。
    tasks = [asyncio.create_task(safe_fetch(url, limiter)) for url in urls]

    results = []

    # as_completed 让我们按“完成顺序”消费结果，而不是按原始输入顺序等待。
    for completed in asyncio.as_completed(tasks):
        result = await completed
        print(f"completed: {result.url} -> {result.status}")
        results.append(result)

    print("\nsummary")

    # 最后统一打印汇总，观察成功和失败任务是如何被同一套结构承载的。
    for result in results:
        print(
            f"url={result.url}, status={result.status}, "
            f"duration={result.duration:.2f}, detail={result.detail}"
        )


if __name__ == "__main__":
    asyncio.run(main())
