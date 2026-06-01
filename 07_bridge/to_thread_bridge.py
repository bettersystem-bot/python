import asyncio
import time


def blocking_report(name: str, delay: float) -> str:
    print(f"blocking_report: {name} starts, sleeping {delay:.1f}s")
    time.sleep(delay)
    print(f"blocking_report: {name} ends")
    return f"report for {name}"


async def heartbeat() -> None:
    for tick in range(6):
        print(f"heartbeat tick {tick}")
        await asyncio.sleep(0.3)


async def main() -> None:
    print("run blocking work in a thread while heartbeat stays responsive")
    report_task = asyncio.create_task(asyncio.to_thread(blocking_report, "daily-job", 1.5))
    heartbeat_task = asyncio.create_task(heartbeat())
    report, _ = await asyncio.gather(report_task, heartbeat_task)
    print("result:", report)


if __name__ == "__main__":
    asyncio.run(main())
