import asyncio
import time


def blocking_report(name: str, delay: float) -> str:
    # 这是一个阻塞函数，使用 time.sleep() 会直接卡住当前线程。
    print(f"blocking_report: {name} starts, sleeping {delay:.1f}s")
    time.sleep(delay)
    print(f"blocking_report: {name} ends")
    return f"report for {name}"


async def heartbeat() -> None:
    # heartbeat 用来证明：即使后台有阻塞逻辑，事件循环仍然可以保持活跃。
    for tick in range(6):
        print(f"heartbeat tick {tick}")
        await asyncio.sleep(0.3)


async def main() -> None:
    print("run blocking work in a thread while heartbeat stays responsive")

    # asyncio.to_thread() 会把阻塞函数放到线程池里跑，避免堵住事件循环线程。
    report_task = asyncio.create_task(asyncio.to_thread(blocking_report, "daily-job", 1.5))

    # 与此同时，heartbeat 继续在主事件循环里异步推进。
    heartbeat_task = asyncio.create_task(heartbeat())

    # gather 等两个任务都结束后，一次性拿回结果。
    report, _ = await asyncio.gather(report_task, heartbeat_task)
    print("result:", report)


if __name__ == "__main__":
    asyncio.run(main())
