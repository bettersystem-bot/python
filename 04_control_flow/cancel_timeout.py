import asyncio


async def long_running_job() -> str:
    try:
        # 模拟一个分多个阶段执行的长任务。
        for step in range(1, 6):
            print(f"long_running_job: step {step}")
            await asyncio.sleep(0.6)

        return "job completed"

    except asyncio.CancelledError:
        # 当任务被取消时，会在 await 点收到 CancelledError。
        # 常见做法是先打印日志、释放资源，再把异常继续抛出去。
        print("long_running_job: received cancellation, cleaning up")
        raise

    finally:
        # 无论正常完成、超时取消还是手动取消，finally 都会执行。
        print("long_running_job: finally block executed")


async def demo_timeout() -> None:
    print("\n=== timeout demo ===")
    try:
        # wait_for 给一个协程增加超时限制。
        # 如果超过 timeout，内部任务会被取消，外层这里会收到 TimeoutError。
        result = await asyncio.wait_for(long_running_job(), timeout=1.5)
        print("timeout demo result:", result)
    except asyncio.TimeoutError:
        print("timeout demo: operation exceeded 1.5s")


async def demo_manual_cancel() -> None:
    print("\n=== manual cancel demo ===")

    # 先把长任务放进后台运行。
    task = asyncio.create_task(long_running_job(), name="cancel-demo")

    # 主协程先等待一会儿，让后台任务先跑几步。
    await asyncio.sleep(1.1)
    print(f"cancelling task: {task.get_name()}")

    # cancel() 不是强制瞬间中断，而是向任务发出取消请求。
    task.cancel()

    try:
        # await task 时，调用方会观察到这个取消结果。
        await task
    except asyncio.CancelledError:
        print("manual cancel demo: task cancellation observed by caller")


async def main() -> None:
    await demo_timeout()
    await demo_manual_cancel()


if __name__ == "__main__":
    asyncio.run(main())
