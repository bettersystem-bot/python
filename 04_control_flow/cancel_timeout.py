import asyncio


async def long_running_job() -> str:
    try:
        for step in range(1, 6):
            print(f"long_running_job: step {step}")
            await asyncio.sleep(0.6)
        return "job completed"
    except asyncio.CancelledError:
        print("long_running_job: received cancellation, cleaning up")
        raise
    finally:
        print("long_running_job: finally block executed")


async def demo_timeout() -> None:
    print("\n=== timeout demo ===")
    try:
        result = await asyncio.wait_for(long_running_job(), timeout=1.5)
        print("timeout demo result:", result)
    except asyncio.TimeoutError:
        print("timeout demo: operation exceeded 1.5s")


async def demo_manual_cancel() -> None:
    print("\n=== manual cancel demo ===")
    task = asyncio.create_task(long_running_job(), name="cancel-demo")
    await asyncio.sleep(1.1)
    print(f"cancelling task: {task.get_name()}")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("manual cancel demo: task cancellation observed by caller")


async def main() -> None:
    await demo_timeout()
    await demo_manual_cancel()


if __name__ == "__main__":
    asyncio.run(main())
