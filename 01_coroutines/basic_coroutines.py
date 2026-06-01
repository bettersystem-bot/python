import asyncio
import time


def log(message: str) -> None:
    now = time.strftime("%H:%M:%S")
    print(f"[{now}] {message}")


async def prepare_breakfast() -> str:
    log("prepare_breakfast: start")
    await asyncio.sleep(1)
    log("prepare_breakfast: after first await")
    await asyncio.sleep(1)
    log("prepare_breakfast: done")
    return "breakfast ready"


async def main() -> None:
    log("main: create coroutine object")
    coroutine = prepare_breakfast()
    log(f"main: coroutine object = {coroutine!r}")

    log("main: await coroutine now")
    result = await coroutine
    log(f"main: result = {result}")


if __name__ == "__main__":
    asyncio.run(main())
