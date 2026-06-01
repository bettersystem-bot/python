import asyncio


async def unstable_job(name: str, delay: float, should_fail: bool = False) -> str:
    # 这个函数模拟“不稳定的远程调用”：可能成功，也可能在等待后失败。
    print(f"{name}: 开始执行")
    await asyncio.sleep(delay)

    if should_fail:
        # 异常不是在 create_task 那一刻抛出，而是在任务真正运行到这里时抛出。
        raise RuntimeError(f"{name}: 模拟失败")

    print(f"{name}: 执行成功")
    return f"{name}: result"


async def demo_gather_default() -> None:
    print("\n=== gather 默认异常策略 ===")
    try:
        # 默认情况下，只要其中一个 awaitable 抛异常，gather 就会把异常抛给调用方。
        # 但“异常被抛给调用方”不等于“所有兄弟任务都已经被强制停止”。
        await asyncio.gather(
            unstable_job("job-A", 0.2),
            unstable_job("job-B", 0.4, should_fail=True),
            unstable_job("job-C", 0.6),
        )
    except RuntimeError as exc:
        print(f"调用方捕获到异常: {exc}")

        # 给 job-C 一个机会继续打印结果，用来观察 gather 默认策略的真实行为。
        # 如果业务要求一个失败就全部停止，应当自己保存 Task 并显式 cancel 剩余任务。
        await asyncio.sleep(0.3)


async def demo_gather_return_exceptions() -> None:
    print("\n=== gather return_exceptions=True ===")

    # return_exceptions=True 会把异常当成普通结果返回，适合批量任务允许部分失败的场景。
    results = await asyncio.gather(
        unstable_job("job-D", 0.2),
        unstable_job("job-E", 0.4, should_fail=True),
        unstable_job("job-F", 0.1),
        return_exceptions=True,
    )

    for index, result in enumerate(results, start=1):
        if isinstance(result, Exception):
            print(f"结果 {index}: 失败 -> {result}")
        else:
            print(f"结果 {index}: 成功 -> {result}")


async def demo_background_task_exception() -> None:
    print("\n=== 后台任务异常处理 ===")

    def report_task_result(task: asyncio.Task) -> None:
        # done_callback 不能直接 await，所以这里用 task.exception() 读取异常。
        # 如果任务失败但没人读取异常，真实项目里会很难排查。
        try:
            task.result()
        except Exception as exc:
            print(f"后台任务被集中记录: {exc}")

    task = asyncio.create_task(unstable_job("background-job", 0.2, should_fail=True))
    task.add_done_callback(report_task_result)

    # 主协程做自己的事，但后台任务的异常仍然会被回调集中处理。
    await asyncio.sleep(0.5)


async def demo_shield() -> None:
    print("\n=== shield 保护关键任务 ===")

    critical_task = asyncio.create_task(unstable_job("critical-job", 0.5))

    try:
        # wait_for 超时后会尝试取消内部 awaitable。
        # shield 的作用是：外层等待可以超时，但里面的关键任务继续执行。
        await asyncio.wait_for(asyncio.shield(critical_task), timeout=0.2)
    except asyncio.TimeoutError:
        print("外层等待超时，但 critical-job 被 shield 保护，没有被取消")

    result = await critical_task
    print(f"关键任务最终结果: {result}")


async def main() -> None:
    await demo_gather_default()
    await demo_gather_return_exceptions()
    await demo_background_task_exception()
    await demo_shield()


if __name__ == "__main__":
    asyncio.run(main())
