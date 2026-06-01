import asyncio
import time


def log(message: str) -> None:
    # 用统一格式打印日志，方便观察异步执行顺序。
    now = time.strftime("%H:%M:%S")
    print(f"[{now}] {message}")


async def prepare_breakfast() -> str:
    # 进入协程函数体，说明这个协程已经真正开始被事件循环执行。
    log("prepare_breakfast: start")

    # 第一次 await：当前协程主动让出执行权，等待 1 秒后再恢复。
    await asyncio.sleep(1)
    log("prepare_breakfast: after first await")

    # 第二次 await：再次暂停自己，让事件循环有机会调度别的协程。
    await asyncio.sleep(1)
    log("prepare_breakfast: done")

    # 协程完成时像普通函数一样返回结果。
    return "breakfast ready"


async def main() -> None:
    log("main: create coroutine object")

    # 注意：这里只是创建协程对象，并没有立即执行 prepare_breakfast 的函数体。
    coroutine = prepare_breakfast()
    log(f"main: coroutine object = {coroutine!r}")

    # 当 main 显式 await 这个协程对象时，事件循环才会开始驱动它执行。
    log("main: await coroutine now")
    result = await coroutine

    # 协程执行结束后，main 拿到返回值并继续往下执行。
    log(f"main: result = {result}")


if __name__ == "__main__":
    # asyncio.run() 会负责创建事件循环、运行 main、最后安全关闭事件循环。
    asyncio.run(main())
