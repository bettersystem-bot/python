import asyncio
import random
from dataclasses import dataclass


@dataclass
class CrawlResult:
    url: str
    status: str
    duration: float
    detail: str


async def fetch(url: str, limiter: asyncio.Semaphore) -> CrawlResult:
    async with limiter:
        delay = round(random.uniform(0.4, 1.4), 2)
        print(f"fetch start: {url} (delay={delay:.2f}s)")
        await asyncio.sleep(delay)

        if "fail" in url:
            raise RuntimeError(f"simulated fetch failure for {url}")

        print(f"fetch done: {url}")
        return CrawlResult(url=url, status="ok", duration=delay, detail="content-length=demo")


async def safe_fetch(url: str, limiter: asyncio.Semaphore) -> CrawlResult:
    try:
        return await fetch(url, limiter)
    except Exception as exc:
        return CrawlResult(url=url, status="error", duration=0.0, detail=str(exc))


async def main() -> None:
    random.seed(21)
    urls = [
        "https://example.com/home",
        "https://example.com/profile",
        "https://example.com/fail-report",
        "https://example.com/feed",
        "https://example.com/settings",
    ]
    limiter = asyncio.Semaphore(2)
    tasks = [asyncio.create_task(safe_fetch(url, limiter)) for url in urls]

    results = []
    for completed in asyncio.as_completed(tasks):
        result = await completed
        print(f"completed: {result.url} -> {result.status}")
        results.append(result)

    print("\nsummary")
    for result in results:
        print(
            f"url={result.url}, status={result.status}, "
            f"duration={result.duration:.2f}, detail={result.detail}"
        )


if __name__ == "__main__":
    asyncio.run(main())
