import asyncio


class AsyncCounter:
    # 这是一个最小可用的异步迭代器示例。
    # 它每次产出下一个数字之前，都会先异步等待一小段时间。
    def __init__(self, limit: int) -> None:
        self.current = 0
        self.limit = limit

    def __aiter__(self):
        # async for 会先调用 __aiter__() 拿到异步迭代器对象本身。
        return self

    async def __anext__(self) -> int:
        # 当没有更多元素时，必须抛出 StopAsyncIteration。
        if self.current >= self.limit:
            raise StopAsyncIteration

        # 模拟“获取下一个值需要等待”的异步过程。
        await asyncio.sleep(0.2)
        self.current += 1
        return self.current


async def sensor_stream(limit: int):
    # 这是异步生成器：既有 async def，又有 yield。
    # 它适合表示“数据是一条一条异步流出来”的场景。
    for value in range(limit):
        await asyncio.sleep(0.15)
        yield {"reading": value, "unit": "demo"}


class FakeConnection:
    # 这是异步上下文管理器，用于模拟异步资源的申请与释放。
    async def __aenter__(self):
        print("FakeConnection: opening connection")
        await asyncio.sleep(0.2)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        print("FakeConnection: closing connection")
        await asyncio.sleep(0.2)

        # 返回 False 表示如果 with 块内部有异常，不在这里吞掉，继续向外传播。
        return False

    async def send(self, payload: str) -> None:
        # 模拟通过连接发送异步消息。
        await asyncio.sleep(0.1)
        print(f"FakeConnection: sent {payload}")


async def main() -> None:
    print("\n=== async iterator ===")

    # async for 会不断 await __anext__()，直到收到 StopAsyncIteration。
    async for number in AsyncCounter(limit=3):
        print("counter value:", number)

    print("\n=== async generator ===")

    # 对异步生成器的消费方式与异步迭代器类似，都是 async for。
    async for reading in sensor_stream(limit=4):
        print("stream reading:", reading)

    print("\n=== async context manager ===")

    # async with 会自动调用 __aenter__ / __aexit__，适合包裹异步资源生命周期。
    async with FakeConnection() as connection:
        await connection.send("hello async world")


if __name__ == "__main__":
    asyncio.run(main())
